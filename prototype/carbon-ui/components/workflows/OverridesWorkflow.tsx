'use client';

import React from 'react';
import {
  Button,
  Checkbox,
  Layer,
  Search,
  Select,
  SelectItem,
  Tag,
  TextArea,
  TextInput,
  Tile,
} from '@carbon/react';
import { Download } from '@carbon/icons-react';
import { useAppState } from '../../store/AppContext';
import type { AssignmentVm } from '../../types/network-planning';

export type DecisionAuditRow = {
  'VM Key': string;
  'VM Name': string;
  Owner: string;
  Application: string;
  Wave: string;
  'Original Profile': string;
  'Chosen Profile': string;
  'Profile Override Reason': string;
  'Original Storage Tier': string;
  'Chosen Storage Tier': string;
  'Storage Tier Override Reason': string;
  'Network Mode': string;
  'Include/Exclude': string;
  'Exclusion Reason': string;
};

const DECISION_AUDIT_COLUMNS: Array<keyof DecisionAuditRow> = [
  'VM Key',
  'VM Name',
  'Owner',
  'Application',
  'Wave',
  'Original Profile',
  'Chosen Profile',
  'Profile Override Reason',
  'Original Storage Tier',
  'Chosen Storage Tier',
  'Storage Tier Override Reason',
  'Network Mode',
  'Include/Exclude',
  'Exclusion Reason',
];

function textValue(value: unknown) {
  return value === null || value === undefined ? '' : String(value);
}

function csvValue(value: unknown) {
  const text = textValue(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function buildDecisionAuditRows(rows: AssignmentVm[]): DecisionAuditRow[] {
  return rows.map((row) => ({
    'VM Key': row.id,
    'VM Name': row.name,
    Owner: row.owner,
    Application: row.application,
    Wave: row.wave,
    'Original Profile': row.profile,
    'Chosen Profile': row.overrideProfile || row.profile,
    'Profile Override Reason': row.overrideProfileReason || '',
    'Original Storage Tier': row.storageTier,
    'Chosen Storage Tier': row.overrideStorageTier || row.storageTier,
    'Storage Tier Override Reason': row.overrideStorageTierReason || '',
    'Network Mode': row.network,
    'Include/Exclude': row.excluded ? 'Exclude' : 'Include',
    'Exclusion Reason': row.exclusionReason || '',
  }));
}

export function decisionAuditCsv(rows: AssignmentVm[]) {
  const auditRows = buildDecisionAuditRows(rows);
  return [
    DECISION_AUDIT_COLUMNS.join(','),
    ...auditRows.map((row) =>
      DECISION_AUDIT_COLUMNS.map((column) => csvValue(row[column])).join(','),
    ),
  ].join('\n');
}

export function summarizeOverrides(rows: AssignmentVm[]) {
  return rows.reduce(
    (summary, row) => {
      const hasProfileOverride = Boolean(row.overrideProfile);
      const hasStorageOverride = Boolean(row.overrideStorageTier);
      const isExcluded = Boolean(row.excluded);
      const missingProfileReason = hasProfileOverride && !row.overrideProfileReason?.trim();
      const missingStorageReason = hasStorageOverride && !row.overrideStorageTierReason?.trim();
      const missingExclusionReason = isExcluded && !row.exclusionReason?.trim();
      return {
        profileOverrides: summary.profileOverrides + (hasProfileOverride ? 1 : 0),
        storageOverrides: summary.storageOverrides + (hasStorageOverride ? 1 : 0),
        excluded: summary.excluded + (isExcluded ? 1 : 0),
        missingReasons: summary.missingReasons
          + (missingProfileReason ? 1 : 0)
          + (missingStorageReason ? 1 : 0)
          + (missingExclusionReason ? 1 : 0),
      };
    },
    { profileOverrides: 0, storageOverrides: 0, excluded: 0, missingReasons: 0 },
  );
}

export default function OverridesWorkflow() {
  const { state, dispatch } = useAppState();
  const { assignmentRows, resources, searchValue } = state;
  const summary = summarizeOverrides(assignmentRows);
  const profileOptions = [...new Set(assignmentRows.map((row) => row.profile).filter(Boolean))];

  const filteredRows = assignmentRows.filter((row) => {
    const query = searchValue.trim().toLowerCase();
    if (!query) return true;
    return [row.name, row.profile, row.overrideProfile, row.storageTier, row.overrideStorageTier, row.application, row.owner]
      .some((value) => textValue(value).toLowerCase().includes(query));
  });

  function updateRow(rowId: string, patch: Partial<AssignmentVm>) {
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => (row.id === rowId ? { ...row, ...patch } : row)),
    });
  }

  function exportCsv() {
    const blob = new Blob([decisionAuditCsv(assignmentRows)], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'decision-audit.csv';
    anchor.click();
    URL.revokeObjectURL(url);
    dispatch({ type: 'SET_PROJECT_STATUS', payload: 'Decision audit CSV exported from Carbon VM overrides.' });
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>VM Overrides</h2>
          <p>Review IBM VSI sizing, storage tier, and exclusion decisions before Terraform handoff.</p>
        </div>
        <div className="network-actions">
          <Tag type={summary.missingReasons > 0 ? 'red' : 'green'}>
            {summary.missingReasons} missing reasons
          </Tag>
          <Button kind="secondary" renderIcon={Download} onClick={exportCsv}>
            Export decision audit CSV
          </Button>
        </div>
      </div>

      <div className="summary-grid override-summary">
        <Tile>
          <strong>Profile overrides</strong>
          <p>{summary.profileOverrides}</p>
        </Tile>
        <Tile>
          <strong>Storage overrides</strong>
          <p>{summary.storageOverrides}</p>
        </Tile>
        <Tile>
          <strong>Excluded VMs</strong>
          <p>{summary.excluded}</p>
        </Tile>
        <Tile>
          <strong>Reason gaps</strong>
          <p>{summary.missingReasons}</p>
        </Tile>
      </div>

      <div className="assignment-toolbar override-toolbar">
        <Search
          id="override-search"
          labelText="Search VM overrides"
          placeholder="Search by VM, profile, storage tier, owner, or app"
          value={searchValue}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            dispatch({ type: 'SET_SEARCH_VALUE', payload: event.target.value })
          }
        />
      </div>

      <div className="vm-table-wrap override-table-wrap">
        <table className="vm-table override-table">
          <thead>
            <tr>
              <th>VM</th>
              <th>Profile override</th>
              <th>Storage override</th>
              <th>Exclude</th>
              <th>Planning context</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{row.name}</strong>
                  <span>{row.application || 'No application'} | {row.owner || 'No owner'}</span>
                </td>
                <td>
                  <TextInput
                    id={`profile-${row.id}`}
                    labelText={`Override profile for ${row.name}`}
                    value={row.overrideProfile || ''}
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                      updateRow(row.id, { overrideProfile: event.target.value })
                    }
                  />
                  <TextArea
                    id={`profile-reason-${row.id}`}
                    labelText={`Profile override reason for ${row.name}`}
                    value={row.overrideProfileReason || ''}
                    onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                      updateRow(row.id, { overrideProfileReason: event.target.value })
                    }
                  />
                  <span>Recommended: {row.profile || 'No IBM profile'}</span>
                  {profileOptions.length > 0 && (
                    <Select
                      id={`profile-preset-${row.id}`}
                      labelText={`Profile preset for ${row.name}`}
                      value=""
                      onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                        updateRow(row.id, { overrideProfile: event.target.value })
                      }
                    >
                      <SelectItem text="Choose profile" value="" />
                      {profileOptions.map((profile) => (
                        <SelectItem key={profile} text={profile} value={profile} />
                      ))}
                    </Select>
                  )}
                </td>
                <td>
                  <Select
                    id={`storage-${row.id}`}
                    labelText={`Override storage tier for ${row.name}`}
                    value={row.overrideStorageTier || ''}
                    onChange={(event: React.ChangeEvent<HTMLSelectElement>) => {
                      const tier = event.target.value;
                      const bucket = resources.storageProfiles.find((storage) => storage.tier === tier);
                      updateRow(row.id, {
                        overrideStorageTier: tier,
                        storageLabel: bucket?.label || '',
                      });
                    }}
                  >
                    <SelectItem text="Use recommended tier" value="" />
                    {resources.storageProfiles.map((storage) => (
                      <SelectItem key={storage.id} text={`${storage.label} (${storage.tier})`} value={storage.tier} />
                    ))}
                  </Select>
                  <TextArea
                    id={`storage-reason-${row.id}`}
                    labelText={`Storage override reason for ${row.name}`}
                    value={row.overrideStorageTierReason || ''}
                    onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                      updateRow(row.id, { overrideStorageTierReason: event.target.value })
                    }
                  />
                  <span>Recommended: {row.storageTier || 'No storage tier'}</span>
                </td>
                <td>
                  <Checkbox
                    id={`exclude-${row.id}`}
                    labelText={`Exclude ${row.name}`}
                    checked={Boolean(row.excluded)}
                    onChange={(_: unknown, data: { checked?: boolean }) =>
                      updateRow(row.id, { excluded: Boolean(data.checked) })
                    }
                  />
                  <TextArea
                    id={`exclude-reason-${row.id}`}
                    labelText={`Exclusion reason for ${row.name}`}
                    value={row.exclusionReason || ''}
                    onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                      updateRow(row.id, { exclusionReason: event.target.value })
                    }
                  />
                </td>
                <td>
                  <Tag type={row.wave ? 'purple' : 'gray'}>{row.wave || 'No wave'}</Tag>
                  <Tag type={row.subnet ? 'cyan' : 'gray'}>{row.subnet || 'No subnet'}</Tag>
                  <span>{row.securityGroup || 'No security group'}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layer>
  );
}
