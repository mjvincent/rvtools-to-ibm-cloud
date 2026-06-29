'use client';

import React, { useMemo } from 'react';
import {
  Layer,
  Select,
  SelectItem,
  Tag,
  TextArea,
  TextInput,
  Tile,
} from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import type {
  AssignmentVm,
  RemediationBacklogItem,
  RemediationStatus,
  RemediationTracker,
} from '../../types/network-planning';

const statusOptions: RemediationStatus[] = ['Open', 'In Progress', 'Resolved', 'Deferred'];

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
  ].filter((finding) => finding.status === 'Blocked' || finding.status === 'Review');
}

export function buildRemediationBacklog(
  rows: AssignmentVm[],
  tracker: RemediationTracker,
): RemediationBacklogItem[] {
  return rows.flatMap((row) =>
    readinessFindings(row).map((finding) => {
      const blockerId = `${row.id}::${finding.type.toLowerCase()}`;
      const saved = tracker[blockerId];
      return {
        blockerId,
        vmKey: row.id,
        vmName: row.name,
        owner: saved?.owner ?? row.owner ?? '',
        blockerType: finding.type,
        blockerDescription: finding.description,
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

export default function RemediationWorkflow() {
  const { state, dispatch } = useAppState();
  const { assignmentRows, remediationTracker } = state;

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
        },
      },
    });
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Remediation Backlog</h2>
          <p>Track readiness blockers with owners, status, due dates, and notes.</p>
        </div>
        <Tag type={summary.open || summary.inProgress ? 'red' : 'green'}>
          {summary.open + summary.inProgress} active
        </Tag>
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
