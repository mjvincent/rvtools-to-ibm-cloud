'use client';

import React, { useMemo } from 'react';
import {
  Button,
  FileUploaderDropContainer,
  InlineNotification,
  Layer,
  Select,
  SelectItem,
  Tag,
  TextInput,
  Tile,
} from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import type { AssignmentVm } from '../../types/network-planning';
import WorkflowCompletionChecklist from '../ui/WorkflowCompletionChecklist';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';

const waveColumns = [
  'Wave',
  'Cutover Group',
  'Owner',
  'Application',
  'Priority',
  'Dependency Group',
] as const;

type WaveColumn = typeof waveColumns[number];

const priorityOptions = ['', 'High', 'Medium', 'Low'];
const bulkScopes = ['incomplete', 'selected', 'all'] as const;

type BulkScope = typeof bulkScopes[number];
type WaveBulkDraft = Record<WaveColumn, string>;

function csvEscape(value: string) {
  return `"${value.replace(/"/g, '""')}"`;
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

export function wavePlanningCsv(rows: AssignmentVm[]) {
  const headers = ['VM Key', 'VM Name', ...waveColumns];
  const lines = rows.map((row) => [
    row.id,
    row.name,
    row.wave,
    row.cutoverGroup,
    row.owner,
    row.application,
    row.priority,
    row.dependencyGroup,
  ].map(csvEscape).join(','));
  return [headers.join(','), ...lines].join('\n');
}

export function importWavePlanningCsv(
  csvText: string,
  rows: AssignmentVm[],
): { rows: AssignmentVm[]; applied: number; skipped: number } {
  const importedRows = parseCsv(csvText);
  let applied = 0;
  let skipped = 0;
  const byId = new Map(rows.map((row) => [row.id, row]));
  const updates = new Map<string, Partial<AssignmentVm>>();

  importedRows.forEach((row) => {
    const vmKey = row['VM Key'];
    if (!vmKey || !byId.has(vmKey)) {
      skipped += 1;
      return;
    }
    updates.set(vmKey, {
      wave: row.Wave || '',
      cutoverGroup: row['Cutover Group'] || '',
      owner: row.Owner || '',
      application: row.Application || '',
      priority: row.Priority || '',
      dependencyGroup: row['Dependency Group'] || '',
    });
    applied += 1;
  });

  return {
    rows: rows.map((row) => ({ ...row, ...(updates.get(row.id) || {}) })),
    applied,
    skipped,
  };
}

export function detectApplicationCutoverConflicts(rows: AssignmentVm[]) {
  const byApplication = new Map<string, Set<string>>();
  rows.forEach((row) => {
    if (!row.application || !row.cutoverGroup) return;
    const groups = byApplication.get(row.application) || new Set<string>();
    groups.add(row.cutoverGroup);
    byApplication.set(row.application, groups);
  });
  return [...byApplication.entries()]
    .filter(([, groups]) => groups.size > 1)
    .map(([application, groups]) => ({ application, cutoverGroups: [...groups].sort() }));
}

export function detectDependencyWaveConflicts(rows: AssignmentVm[]) {
  const byDependency = new Map<string, Set<string>>();
  rows.forEach((row) => {
    if (!row.dependencyGroup || !row.wave) return;
    const waves = byDependency.get(row.dependencyGroup) || new Set<string>();
    waves.add(row.wave);
    byDependency.set(row.dependencyGroup, waves);
  });
  return [...byDependency.entries()]
    .filter(([, waves]) => waves.size > 1)
    .map(([dependencyGroup, waves]) => ({ dependencyGroup, waves: [...waves].sort() }));
}

export function waveCompletion(rows: AssignmentVm[]) {
  const complete = rows.filter((row) => row.wave && row.cutoverGroup && row.owner && row.application).length;
  return {
    total: rows.length,
    complete,
    incomplete: rows.length - complete,
  };
}

export function applyWaveBulkAssignment(
  rows: AssignmentVm[],
  draft: WaveBulkDraft,
  scope: BulkScope,
  selectedVmIds: string[] = [],
) {
  const selected = new Set(selectedVmIds);
  const patch = Object.fromEntries(
    waveColumns
      .map((column) => [column, draft[column]?.trim() || ''])
      .filter(([, value]) => value),
  ) as Partial<WaveBulkDraft>;
  if (Object.keys(patch).length === 0) {
    return { rows, applied: 0 };
  }

  let applied = 0;
  const nextRows = rows.map((row) => {
    const inScope =
      scope === 'all'
      || (scope === 'selected' && selected.has(row.id))
      || (scope === 'incomplete' && (!row.wave || !row.cutoverGroup || !row.owner || !row.application));
    if (!inScope) return row;
    applied += 1;
    return {
      ...row,
      wave: patch.Wave ?? row.wave,
      cutoverGroup: patch['Cutover Group'] ?? row.cutoverGroup,
      owner: patch.Owner ?? row.owner,
      application: patch.Application ?? row.application,
      priority: patch.Priority ?? row.priority,
      dependencyGroup: patch['Dependency Group'] ?? row.dependencyGroup,
    };
  });

  return { rows: nextRows, applied };
}

export default function WavesWorkflow() {
  const { state, dispatch } = useAppState();
  const { assignmentRows, selectedVmIds } = state;
  const [importStatus, setImportStatus] = React.useState('');
  const [importError, setImportError] = React.useState('');
  const [bulkScope, setBulkScope] = React.useState<BulkScope>('incomplete');
  const [bulkDraft, setBulkDraft] = React.useState<WaveBulkDraft>({
    Wave: '',
    'Cutover Group': '',
    Owner: '',
    Application: '',
    Priority: '',
    'Dependency Group': '',
  });

  const completion = useMemo(() => waveCompletion(assignmentRows), [assignmentRows]);
  const appConflicts = useMemo(() => detectApplicationCutoverConflicts(assignmentRows), [assignmentRows]);
  const dependencyConflicts = useMemo(() => detectDependencyWaveConflicts(assignmentRows), [assignmentRows]);
  const csvHref = `data:text/csv;charset=utf-8,${encodeURIComponent(wavePlanningCsv(assignmentRows))}`;

  function updateRow(rowId: string, patch: Partial<AssignmentVm>) {
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => (row.id === rowId ? { ...row, ...patch } : row)),
    });
  }

  function updateBulkDraft(column: WaveColumn, value: string) {
    setBulkDraft((current) => ({ ...current, [column]: value }));
  }

  function applyBulkFields() {
    const result = applyWaveBulkAssignment(assignmentRows, bulkDraft, bulkScope, selectedVmIds);
    dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: result.rows });
    setImportStatus(`Applied bulk wave planning to ${result.applied} VM(s).`);
    setImportError('');
  }

  async function importCsvFile(_event: unknown, content: { addedFiles?: File[] }) {
    const file = content.addedFiles?.[0];
    if (!file) return;
    setImportStatus('');
    setImportError('');
    try {
      const result = importWavePlanningCsv(await file.text(), assignmentRows);
      dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: result.rows });
      setImportStatus(`Imported wave planning for ${result.applied} VM(s)${result.skipped ? `; skipped ${result.skipped} unmatched row(s).` : '.'}`);
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Could not import wave planning CSV.');
    }
  }

  function fieldValue(row: AssignmentVm, column: WaveColumn) {
    if (column === 'Wave') return row.wave;
    if (column === 'Cutover Group') return row.cutoverGroup;
    if (column === 'Owner') return row.owner;
    if (column === 'Application') return row.application;
    if (column === 'Priority') return row.priority;
    return row.dependencyGroup;
  }

  function fieldPatch(column: WaveColumn, value: string): Partial<AssignmentVm> {
    if (column === 'Wave') return { wave: value };
    if (column === 'Cutover Group') return { cutoverGroup: value };
    if (column === 'Owner') return { owner: value };
    if (column === 'Application') return { application: value };
    if (column === 'Priority') return { priority: value };
    return { dependencyGroup: value };
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Wave Planning</h2>
          <p>Assign wave, cutover group, owner, application, priority, and dependency fields per VM.</p>
        </div>
        <div className="workflow-header-actions">
          <WorkflowHeaderHelp workflow="waves" />
          <Tag type={completion.incomplete ? 'purple' : 'green'}>
            {completion.complete} of {completion.total} complete
          </Tag>
        </div>
      </div>
      <WorkflowCompletionChecklist workflow="waves" />

      <div className="summary-grid wave-summary">
        <Tile>
          <h3>Total VMs</h3>
          <p>{completion.total}</p>
        </Tile>
        <Tile>
          <h3>Complete</h3>
          <p>{completion.complete}</p>
        </Tile>
        <Tile>
          <h3>Incomplete</h3>
          <p>{completion.incomplete}</p>
        </Tile>
        <Tile>
          <h3>Conflicts</h3>
          <p>{appConflicts.length + dependencyConflicts.length}</p>
        </Tile>
      </div>

      <div className="export-actions">
        <div className="remediation-import">
          <FileUploaderDropContainer
            accept={['.csv', 'text/csv']}
            labelText="Import wave planning CSV"
            onAddFiles={importCsvFile}
          />
        </div>
        <a
          className={`cds--btn cds--btn--secondary${assignmentRows.length === 0 ? ' cds--btn--disabled' : ''}`}
          href={csvHref}
          download="wave-planning.csv"
          aria-disabled={assignmentRows.length === 0}
          onClick={(event) => {
            if (assignmentRows.length === 0) event.preventDefault();
          }}
        >
          Export wave planning CSV
        </a>
      </div>

      <div className="bulk-wave-panel">
        <div className="bulk-wave-controls">
          <Select
            id="bulk-wave-scope"
            labelText="Bulk scope"
            value={bulkScope}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              setBulkScope(event.target.value as BulkScope)
            }
          >
            <SelectItem value="incomplete" text="Incomplete rows" />
            <SelectItem value="selected" text={`Selected rows (${selectedVmIds.length})`} />
            <SelectItem value="all" text="All rows" />
          </Select>
          {waveColumns.map((column) => (
            column === 'Priority' ? (
              <Select
                key={column}
                id={`bulk-${column}`}
                labelText={column}
                value={bulkDraft[column]}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                  updateBulkDraft(column, event.target.value)
                }
              >
                {priorityOptions.map((priority) => (
                  <SelectItem key={priority || 'blank'} value={priority} text={priority || 'Unset'} />
                ))}
              </Select>
            ) : (
              <TextInput
                key={column}
                id={`bulk-${column}`}
                labelText={column}
                value={bulkDraft[column]}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  updateBulkDraft(column, event.target.value)
                }
              />
            )
          ))}
          <Button kind="primary" size="sm" onClick={applyBulkFields}>
            Apply bulk wave fields
          </Button>
        </div>
      </div>

      {importStatus && (
        <InlineNotification
          kind="success"
          lowContrast
          title="Wave planning CSV imported"
          subtitle={importStatus}
        />
      )}
      {importError && (
        <InlineNotification
          kind="error"
          lowContrast
          title="Wave planning CSV import failed"
          subtitle={importError}
        />
      )}

      {(appConflicts.length > 0 || dependencyConflicts.length > 0) && (
        <div className="conflict-list">
          {appConflicts.map((conflict) => (
            <InlineNotification
              key={`app-${conflict.application}`}
              kind="warning"
              lowContrast
              title={`Application ${conflict.application} spans multiple cutover groups`}
              subtitle={conflict.cutoverGroups.join(', ')}
            />
          ))}
          {dependencyConflicts.map((conflict) => (
            <InlineNotification
              key={`dependency-${conflict.dependencyGroup}`}
              kind="warning"
              lowContrast
              title={`Dependency group ${conflict.dependencyGroup} spans multiple waves`}
              subtitle={conflict.waves.join(', ')}
            />
          ))}
        </div>
      )}

      <div className="vm-table-wrap wave-planning-table-wrap">
        <table className="vm-table wave-planning-table" aria-label="Wave planning rows">
          <thead>
            <tr>
              <th>VM</th>
              {waveColumns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {assignmentRows.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{row.name}</strong>
                  <span>{row.id}</span>
                </td>
                {waveColumns.map((column) => (
                  <td key={`${row.id}-${column}`}>
                    {column === 'Priority' ? (
                      <Select
                        id={`wave-${row.id}-${column}`}
                        labelText={column}
                        value={fieldValue(row, column)}
                        onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                          updateRow(row.id, fieldPatch(column, event.target.value))
                        }
                      >
                        {priorityOptions.map((priority) => (
                          <SelectItem key={priority || 'blank'} value={priority} text={priority || 'Unset'} />
                        ))}
                      </Select>
                    ) : (
                      <TextInput
                        id={`wave-${row.id}-${column}`}
                        labelText={column}
                        value={fieldValue(row, column)}
                        onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                          updateRow(row.id, fieldPatch(column, event.target.value))
                        }
                      />
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layer>
  );
}

// Made with Bob
