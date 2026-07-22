'use client';

import React, { useMemo } from 'react';
import {
  FileUploaderDropContainer,
  InlineNotification,
  Layer,
  Select,
  SelectItem,
  Tag,
  TextArea,
  TextInput,
  Tile,
} from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';
import type {
  AssignmentVm,
  RemediationBacklogItem,
  RemediationStatus,
  RemediationTracker,
} from '../../types/network-planning';

const statusOptions: RemediationStatus[] = ['Open', 'In Progress', 'Resolved', 'Deferred'];
const normalizedStatusOptions = new Map(
  statusOptions.map((status) => [status.toLowerCase(), status]),
);

type ImportResult = {
  tracker: RemediationTracker;
  applied: number;
  skipped: number;
};

function readinessFindings(row: AssignmentVm) {
  return [
    {
      type: 'Image',
      status: row.image,
      description: row.imageReasons || 'Review image import path before cutover.',
    },
    {
      type: 'Migration',
      status: row.migration,
      description: row.migrationReasons || 'Resolve migration readiness finding.',
    },
    {
      type: 'Memory',
      status: row.memory,
      description: row.memoryReasons || 'Validate memory profile before migration.',
    },
    {
      type: 'Network',
      status: row.networkReadiness,
      description: row.networkReasons || 'Validate target network design.',
    },
  ].filter((finding) => ['blocked', 'review'].includes(String(finding.status).toLowerCase()));
}

function trackerBlockerType(entry: RemediationTracker[string] | undefined, fallback: string) {
  return entry?.blockerType || entry?.blocker_type || entry?.type || fallback;
}

function trackerBlockerDescription(entry: RemediationTracker[string] | undefined, fallback: string) {
  return entry?.blockerDescription || entry?.blocker_description || entry?.description || fallback;
}

export function buildRemediationBacklog(
  rows: AssignmentVm[],
  tracker: RemediationTracker,
): RemediationBacklogItem[] {
  return rows.flatMap((row) =>
    readinessFindings(row).map((finding) => {
      const blockerId = `${row.id}::${finding.type.toLowerCase()}`;
      const saved = tracker[blockerId];
      const blockerType = trackerBlockerType(saved, finding.type);
      const blockerDescription = trackerBlockerDescription(saved, finding.description);
      return {
        blockerId,
        vmKey: saved?.vmKey || saved?.vm_key || row.id,
        vmName: row.name,
        owner: saved?.owner ?? row.owner ?? '',
        blockerType,
        blockerDescription,
        status: saved?.status ?? 'Open',
        dueDate: saved?.dueDate ?? '',
        notes: saved?.notes ?? '',
      };
    }),
  );
}

function csvEscape(value: string) {
  return `"${value.replace(/"/g, '""')}"`;
}

function backlogCsv(items: RemediationBacklogItem[]) {
  const headers = [
    'blocker_id',
    'VM Key',
    'VM Name',
    'Owner',
    'Blocker Type',
    'Blocker Description',
    'Status',
    'Due Date',
    'Notes',
  ];
  const lines = items.map((item) => [
    item.blockerId,
    item.vmKey,
    item.vmName,
    item.owner,
    item.blockerType,
    item.blockerDescription,
    item.status,
    item.dueDate,
    item.notes,
  ].map(csvEscape).join(','));
  return [headers.join(','), ...lines].join('\n');
}

function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let field = '';
  let row: string[] = [];
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      row.push(field);
      field = '';
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') index += 1;
      row.push(field);
      if (row.some((value) => value.trim())) rows.push(row);
      field = '';
      row = [];
    } else {
      field += char;
    }
  }

  row.push(field);
  if (row.some((value) => value.trim())) rows.push(row);
  if (rows.length < 2) return [];

  const headers = rows[0].map((header) => header.trim());
  return rows.slice(1).map((values) => Object.fromEntries(
    headers.map((header, index) => [header, values[index]?.trim() || '']),
  ));
}

function normalizeStatus(value: string): RemediationStatus {
  return normalizedStatusOptions.get(String(value || '').trim().toLowerCase()) || 'Open';
}

export function importRemediationCsv(
  csvText: string,
  backlog: RemediationBacklogItem[],
  tracker: RemediationTracker,
): ImportResult {
  const rows = parseCsv(csvText);
  const bySignature = new Map(
    backlog.map((item) => [
      `${item.vmKey}::${item.blockerType}::${item.blockerDescription}`,
      item.blockerId,
    ]),
  );
  const validIds = new Set(backlog.map((item) => item.blockerId));
  const nextTracker = { ...tracker };
  let applied = 0;
  let skipped = 0;

  rows.forEach((row) => {
    const blockerId = row.blocker_id || row['Blocker ID'] || bySignature.get(
      `${row['VM Key'] || ''}::${row['Blocker Type'] || ''}::${row['Blocker Description'] || ''}`,
    );
    if (!blockerId || !validIds.has(blockerId)) {
      skipped += 1;
      return;
    }
    const existing = backlog.find((item) => item.blockerId === blockerId);
    const blockerType = row['Blocker Type'] || existing?.blockerType || '';
    const blockerDescription = row['Blocker Description'] || existing?.blockerDescription || '';
    const vmKey = row['VM Key'] || existing?.vmKey || blockerId.split('::', 1)[0].split(':', 1)[0];
    nextTracker[blockerId] = {
      status: normalizeStatus(row.Status || existing?.status || 'Open'),
      owner: row.Owner || existing?.owner || '',
      dueDate: row['Due Date'] || row.due_date || '',
      notes: row.Notes || '',
      vmKey,
      vm_key: vmKey,
      blockerType,
      blocker_type: blockerType,
      blockerDescription,
      blocker_description: blockerDescription,
    };
    applied += 1;
  });

  return { tracker: nextTracker, applied, skipped };
}

export default function RemediationWorkflow() {
  const { state, dispatch } = useAppState();
  const { assignmentRows, remediationTracker } = state;
  const [importStatus, setImportStatus] = React.useState('');
  const [importError, setImportError] = React.useState('');

  const backlog = useMemo(
    () => buildRemediationBacklog(assignmentRows, remediationTracker),
    [assignmentRows, remediationTracker],
  );

  const summary = useMemo(() => ({
    open: backlog.filter((item) => item.status === 'Open').length,
    inProgress: backlog.filter((item) => item.status === 'In Progress').length,
    resolved: backlog.filter((item) => item.status === 'Resolved').length,
    deferred: backlog.filter((item) => item.status === 'Deferred').length,
  }), [backlog]);

  const csvHref = `data:text/csv;charset=utf-8,${encodeURIComponent(backlogCsv(backlog))}`;

  function updateTracker(blockerId: string, patch: Partial<RemediationBacklogItem>) {
    const currentItem = backlog.find((item) => item.blockerId === blockerId);
    if (!currentItem) return;
    const current = remediationTracker[blockerId] ?? {
      status: currentItem.status,
      owner: currentItem.owner,
      dueDate: currentItem.dueDate,
      notes: currentItem.notes,
      vmKey: currentItem.vmKey,
      vm_key: currentItem.vmKey,
      blockerType: currentItem.blockerType,
      blocker_type: currentItem.blockerType,
      blockerDescription: currentItem.blockerDescription,
      blocker_description: currentItem.blockerDescription,
    };
    dispatch({
      type: 'SET_REMEDIATION_TRACKER',
      payload: {
        ...remediationTracker,
        [blockerId]: {
          status: (patch.status as RemediationStatus) ?? current.status,
          owner: patch.owner ?? current.owner,
          dueDate: patch.dueDate ?? current.dueDate,
          notes: patch.notes ?? current.notes,
          vmKey: current.vmKey || current.vm_key || currentItem.vmKey,
          vm_key: current.vm_key || current.vmKey || currentItem.vmKey,
          blockerType: current.blockerType || current.blocker_type || currentItem.blockerType,
          blocker_type: current.blocker_type || current.blockerType || currentItem.blockerType,
          blockerDescription: current.blockerDescription || current.blocker_description || currentItem.blockerDescription,
          blocker_description: current.blocker_description || current.blockerDescription || currentItem.blockerDescription,
        },
      },
    });
  }

  async function importCsvFile(_event: unknown, content: { addedFiles?: File[] }) {
    const file = content.addedFiles?.[0];
    if (!file) return;
    setImportStatus('');
    setImportError('');
    try {
      const result = importRemediationCsv(await file.text(), backlog, remediationTracker);
      dispatch({ type: 'SET_REMEDIATION_TRACKER', payload: result.tracker });
      setImportStatus(`Imported ${result.applied} remediation row(s)${result.skipped ? `; skipped ${result.skipped} unmatched row(s).` : '.'}`);
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Could not import remediation CSV.');
    }
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Remediation Backlog</h2>
          <p>Track readiness blockers with owners, status, due dates, and notes.</p>
        </div>
        <div className="workflow-header-actions">
          <WorkflowHeaderHelp workflow="remediation" />
          <Tag type={summary.open || summary.inProgress ? 'red' : 'green'}>
            {summary.open + summary.inProgress} active
          </Tag>
        </div>
      </div>

      <div className="summary-grid remediation-summary">
        <Tile>
          <h3>Open</h3>
          <p>{summary.open}</p>
        </Tile>
        <Tile>
          <h3>In progress</h3>
          <p>{summary.inProgress}</p>
        </Tile>
        <Tile>
          <h3>Resolved</h3>
          <p>{summary.resolved}</p>
        </Tile>
        <Tile>
          <h3>Deferred</h3>
          <p>{summary.deferred}</p>
        </Tile>
      </div>

      <div className="export-actions">
        <div className="remediation-import">
          <FileUploaderDropContainer
            accept={['.csv', 'text/csv']}
            labelText="Import remediation CSV"
            onAddFiles={importCsvFile}
          />
        </div>
        <a
          className={`cds--btn cds--btn--secondary${backlog.length === 0 ? ' cds--btn--disabled' : ''}`}
          href={csvHref}
          download="p4-remediation-backlog.csv"
          aria-disabled={backlog.length === 0}
          onClick={(event) => {
            if (backlog.length === 0) event.preventDefault();
          }}
        >
          Export remediation CSV
        </a>
      </div>
      {importStatus && (
        <InlineNotification
          kind="success"
          lowContrast
          title="Remediation CSV imported"
          subtitle={importStatus}
        />
      )}
      {importError && (
        <InlineNotification
          kind="error"
          lowContrast
          title="Remediation CSV import failed"
          subtitle={importError}
        />
      )}

      {backlog.length === 0 ? (
        <Tile className="empty-state">
          <h3>No readiness blockers found</h3>
          <p>Workbook intake or VM assignment rows with Blocked or Review readiness signals will appear here.</p>
        </Tile>
      ) : (
        <div className="vm-table-wrap remediation-table-wrap">
          <table className="vm-table remediation-table" aria-label="Remediation backlog rows">
            <thead>
              <tr>
                <th>VM</th>
                <th>Blocker</th>
                <th>Status</th>
                <th>Owner</th>
                <th>Due date</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {backlog.map((item) => (
                <tr key={item.blockerId}>
                  <td>
                    <strong>{item.vmName}</strong>
                    <span>{item.vmKey}</span>
                  </td>
                  <td>
                    <Tag type={item.blockerType === 'Migration' ? 'red' : 'blue'}>
                      {item.blockerType}
                    </Tag>
                    <span>{item.blockerDescription}</span>
                  </td>
                  <td>
                    <Select
                      id={`status-${item.blockerId}`}
                      labelText="Status"
                      value={item.status}
                      onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                        updateTracker(item.blockerId, { status: event.target.value as RemediationStatus })
                      }
                    >
                      {statusOptions.map((status) => (
                        <SelectItem key={status} value={status} text={status} />
                      ))}
                    </Select>
                  </td>
                  <td>
                    <TextInput
                      id={`owner-${item.blockerId}`}
                      labelText="Owner"
                      value={item.owner}
                      onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                        updateTracker(item.blockerId, { owner: event.target.value })
                      }
                    />
                  </td>
                  <td>
                    <TextInput
                      id={`due-${item.blockerId}`}
                      labelText="Due date"
                      value={item.dueDate}
                      onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                        updateTracker(item.blockerId, { dueDate: event.target.value })
                      }
                    />
                  </td>
                  <td>
                    <TextArea
                      id={`notes-${item.blockerId}`}
                      labelText="Notes"
                      value={item.notes}
                      onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                        updateTracker(item.blockerId, { notes: event.target.value })
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layer>
  );
}

// Made with Bob
