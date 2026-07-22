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
import WorkflowCompletionChecklist from '../ui/WorkflowCompletionChecklist';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';

export const COMMON_VSI_PROFILES = [
  'bx2-2x8',
  'bx2-4x16',
  'bx2-8x32',
  'bx2-16x64',
  'cx2-2x4',
  'cx2-4x8',
  'cx2-8x16',
  'cx2-16x32',
  'mx2-2x16',
  'mx2-4x32',
  'mx2-8x64',
  'mx2-16x128',
  'ux2d-2x56',
  'ux2d-4x112',
  'ux2d-8x224',
].sort();

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

export function profileSizeLabel(profile: string) {
  const match = profile.match(/^[a-z0-9]+(?:d)?-(\d+)x(\d+)$/i);
  if (!match) return profile || 'No profile';
  const [, vcpu, memory] = match;
  return `${profile} (${vcpu} vCPU / ${memory} GB)`;
}

export function buildProfileOptions(rows: AssignmentVm[]) {
  return [...new Set([
    ...COMMON_VSI_PROFILES,
    ...rows.flatMap((row) => [row.profile, row.overrideProfile]).filter(Boolean),
  ])].sort();
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

type OverrideFilter = 'all' | 'missingReasons' | 'profileOverrides' | 'storageOverrides' | 'excluded';

export function hasMissingOverrideReason(row: AssignmentVm) {
  return Boolean(
    (row.overrideProfile && !row.overrideProfileReason?.trim())
      || (row.overrideStorageTier && !row.overrideStorageTierReason?.trim())
      || (row.excluded && !row.exclusionReason?.trim()),
  );
}

export function filterOverrideRows(
  rows: AssignmentVm[],
  searchValue: string,
  overrideFilter: OverrideFilter,
) {
  const query = searchValue.trim().toLowerCase();
  return rows.filter((row) => {
    const matchesSearch = !query || [row.name, row.profile, row.overrideProfile, row.storageTier, row.overrideStorageTier, row.application, row.owner]
      .some((value) => textValue(value).toLowerCase().includes(query));
    if (!matchesSearch) return false;
    if (overrideFilter === 'missingReasons') return hasMissingOverrideReason(row);
    if (overrideFilter === 'profileOverrides') return Boolean(row.overrideProfile);
    if (overrideFilter === 'storageOverrides') return Boolean(row.overrideStorageTier);
    if (overrideFilter === 'excluded') return Boolean(row.excluded);
    return true;
  });
}

export default function OverridesWorkflow() {
  const [overrideFilter, setOverrideFilter] = React.useState<OverrideFilter>('all');
  const [bulkProfile, setBulkProfile] = React.useState('');
  const [bulkProfileReason, setBulkProfileReason] = React.useState('');
  const [bulkStorageReason, setBulkStorageReason] = React.useState('');
  const [bulkExclusionReason, setBulkExclusionReason] = React.useState('');
  const { state, dispatch } = useAppState();
  const { assignmentRows, resources, searchValue, selectedVmIds } = state;
  const summary = summarizeOverrides(assignmentRows);
  const profileOptions = buildProfileOptions(assignmentRows);

  const filteredRows = filterOverrideRows(assignmentRows, searchValue, overrideFilter);
  const selectedOverrideRows = assignmentRows.filter((row) => selectedVmIds.includes(row.id));
  const selectedProfileOverrideRows = selectedOverrideRows.filter((row) => row.overrideProfile);
  const selectedStorageOverrideRows = selectedOverrideRows.filter((row) => row.overrideStorageTier);
  const selectedExcludedRows = selectedOverrideRows.filter((row) => row.excluded);
  const allFilteredSelected =
    filteredRows.length > 0 && filteredRows.every((row) => selectedVmIds.includes(row.id));

  function updateRow(rowId: string, patch: Partial<AssignmentVm>) {
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => (row.id === rowId ? { ...row, ...patch } : row)),
    });
  }

  function resetProfileOverride(rowId: string) {
    updateRow(rowId, { overrideProfile: '', overrideProfileReason: '' });
  }

  function updateSelectedRows(patchForRow: (row: AssignmentVm) => Partial<AssignmentVm>) {
    const selectedIds = new Set(selectedVmIds);
    if (selectedIds.size === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select one or more VMs before applying bulk overrides.' });
      return;
    }
    dispatch({ type: 'SET_PROJECT_ERROR', payload: '' });
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) =>
        selectedIds.has(row.id) ? { ...row, ...patchForRow(row) } : row,
      ),
    });
  }

  function toggleSelected(rowId: string, checked: boolean) {
    dispatch({
      type: 'SET_SELECTED_VM_IDS',
      payload: checked
        ? [...new Set([...selectedVmIds, rowId])]
        : selectedVmIds.filter((id) => id !== rowId),
    });
  }

  function toggleAllFiltered(checked: boolean) {
    if (checked) {
      dispatch({
        type: 'SET_SELECTED_VM_IDS',
        payload: [...new Set([...selectedVmIds, ...filteredRows.map((row) => row.id)])],
      });
      return;
    }
    const filteredIds = new Set(filteredRows.map((row) => row.id));
    dispatch({
      type: 'SET_SELECTED_VM_IDS',
      payload: selectedVmIds.filter((id) => !filteredIds.has(id)),
    });
  }

  function clearSelectedOverrides() {
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [] });
  }

  function applyBulkProfile() {
    if (!bulkProfile) return;
    if (selectedOverrideRows.length === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select one or more VMs before applying bulk overrides.' });
      return;
    }
    updateSelectedRows(() => ({ overrideProfile: bulkProfile }));
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `Applied profile override ${bulkProfile} to ${selectedVmIds.length} VM(s).` });
  }

  function applyBulkProfileReason() {
    const reason = bulkProfileReason.trim();
    if (!reason) return;
    if (selectedProfileOverrideRows.length === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select one or more VMs with profile overrides before applying a profile reason.' });
      return;
    }
    updateSelectedRows((row) => (row.overrideProfile ? { overrideProfileReason: reason } : {}));
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `Applied profile override reason to ${selectedProfileOverrideRows.length} VM(s).` });
  }

  function applyBulkStorageReason() {
    const reason = bulkStorageReason.trim();
    if (!reason) return;
    if (selectedStorageOverrideRows.length === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select one or more VMs with storage overrides before applying a storage reason.' });
      return;
    }
    updateSelectedRows((row) => (row.overrideStorageTier ? { overrideStorageTierReason: reason } : {}));
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `Applied storage override reason to ${selectedStorageOverrideRows.length} VM(s).` });
  }

  function applyBulkExclusionReason() {
    const reason = bulkExclusionReason.trim();
    if (!reason) return;
    if (selectedExcludedRows.length === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select one or more excluded VMs before applying an exclusion reason.' });
      return;
    }
    updateSelectedRows((row) => (row.excluded ? { exclusionReason: reason } : {}));
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `Applied exclusion reason to ${selectedExcludedRows.length} VM(s).` });
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
          <WorkflowHeaderHelp workflow="overrides" />
          <Tag type={summary.missingReasons > 0 ? 'red' : 'green'}>
            {summary.missingReasons} missing reasons
          </Tag>
          <Button kind="secondary" renderIcon={Download} onClick={exportCsv}>
            Export decision audit CSV
          </Button>
        </div>
      </div>
      <WorkflowCompletionChecklist workflow="overrides" />

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
        <Select
          id="override-filter"
          labelText="Override filter"
          value={overrideFilter}
          onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
            setOverrideFilter(event.target.value as OverrideFilter)
          }
        >
          <SelectItem value="all" text="All override decisions" />
          <SelectItem value="missingReasons" text="Missing reasons" />
          <SelectItem value="profileOverrides" text="Profile overrides" />
          <SelectItem value="storageOverrides" text="Storage overrides" />
          <SelectItem value="excluded" text="Excluded VMs" />
        </Select>
      </div>

      <Layer className="bulk-override-panel">
        <div className="section-header compact">
          <div>
            <h3>Bulk override cleanup</h3>
            <p>{selectedOverrideRows.length} selected | {filteredRows.length} visible after filter</p>
          </div>
          <div className="network-actions">
            <Button kind="tertiary" size="sm" disabled={filteredRows.length === 0} onClick={() => toggleAllFiltered(true)}>
              Select visible
            </Button>
            <Button kind="tertiary" size="sm" disabled={selectedOverrideRows.length === 0} onClick={clearSelectedOverrides}>
              Clear selection
            </Button>
          </div>
        </div>
        <div className="bulk-override-grid">
          <Select
            id="bulk-profile"
            labelText="Bulk profile override"
            value={bulkProfile}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setBulkProfile(event.target.value)}
          >
            <SelectItem text="Choose profile" value="" />
            {profileOptions.map((profile) => (
              <SelectItem key={profile} text={profileSizeLabel(profile)} value={profile} />
            ))}
          </Select>
          <Button
            kind="secondary"
            size="sm"
            disabled={!bulkProfile || selectedOverrideRows.length === 0}
            onClick={applyBulkProfile}
          >
            Apply profile
          </Button>
          <TextArea
            id="bulk-profile-reason"
            labelText="Bulk profile reason"
            value={bulkProfileReason}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setBulkProfileReason(event.target.value)}
          />
          <Button
            kind="tertiary"
            size="sm"
            disabled={!bulkProfileReason.trim() || selectedProfileOverrideRows.length === 0}
            onClick={applyBulkProfileReason}
          >
            Apply profile reason
          </Button>
          <TextArea
            id="bulk-storage-reason"
            labelText="Bulk storage reason"
            value={bulkStorageReason}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setBulkStorageReason(event.target.value)}
          />
          <Button
            kind="tertiary"
            size="sm"
            disabled={!bulkStorageReason.trim() || selectedStorageOverrideRows.length === 0}
            onClick={applyBulkStorageReason}
          >
            Apply storage reason
          </Button>
          <TextArea
            id="bulk-exclusion-reason"
            labelText="Bulk exclusion reason"
            value={bulkExclusionReason}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setBulkExclusionReason(event.target.value)}
          />
          <Button
            kind="tertiary"
            size="sm"
            disabled={!bulkExclusionReason.trim() || selectedExcludedRows.length === 0}
            onClick={applyBulkExclusionReason}
          >
            Apply exclusion reason
          </Button>
        </div>
      </Layer>

      <div className="vm-table-wrap override-table-wrap">
        <table className="vm-table override-table" aria-label="VM override rows">
          <thead>
            <tr>
              <th>
                <label className="row-select-label">
                  <input
                    type="checkbox"
                    aria-label="Select all visible override rows"
                    checked={allFilteredSelected}
                    onChange={(event) => toggleAllFiltered(event.target.checked)}
                  />
                </label>
              </th>
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
                  <label className="row-select-label">
                    <input
                      type="checkbox"
                      aria-label={`Select override row for ${row.name}`}
                      checked={selectedVmIds.includes(row.id)}
                      onChange={(event) => toggleSelected(row.id, event.target.checked)}
                    />
                  </label>
                </td>
                <td>
                  <strong>{row.name}</strong>
                  <span>{row.application || 'No application'} | {row.owner || 'No owner'}</span>
                </td>
                <td>
                  <div className={`profile-decision${row.overrideProfile ? ' profile-decision--overridden' : ''}`}>
                    <span className="profile-decision__label">Effective VSI profile</span>
                    <strong>{profileSizeLabel(row.overrideProfile || row.profile)}</strong>
                    <div className="network-actions">
                      <Tag type={row.overrideProfile ? 'blue' : 'gray'}>
                        {row.overrideProfile ? 'Override' : 'Recommended'}
                      </Tag>
                      {row.overrideProfile && !row.overrideProfileReason?.trim() && (
                        <Tag type="red">Reason needed</Tag>
                      )}
                    </div>
                  </div>
                  <Select
                    id={`profile-${row.id}`}
                    labelText={`Override profile for ${row.name}`}
                    value={row.overrideProfile || ''}
                    onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                      updateRow(row.id, { overrideProfile: event.target.value })
                    }
                  >
                    <SelectItem text="Use recommended profile" value="" />
                    {profileOptions.map((profile) => (
                      <SelectItem key={profile} text={profileSizeLabel(profile)} value={profile} />
                    ))}
                  </Select>
                  <TextArea
                    id={`profile-reason-${row.id}`}
                    labelText={`Profile override reason for ${row.name}`}
                    value={row.overrideProfileReason || ''}
                    placeholder="Example: Rightsized after memory validation or workload owner approval"
                    onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                      updateRow(row.id, { overrideProfileReason: event.target.value })
                    }
                  />
                  <div className="override-effective">
                    <span>Recommended: {profileSizeLabel(row.profile)}</span>
                    <Tag type={row.overrideProfile ? 'blue' : 'gray'}>
                      Effective: {profileSizeLabel(row.overrideProfile || row.profile)}
                    </Tag>
                  </div>
                  <TextInput
                    id={`profile-custom-${row.id}`}
                    labelText={`Custom profile for ${row.name}`}
                    value={row.overrideProfile || ''}
                    placeholder="Example: mx2-16x128"
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                      updateRow(row.id, { overrideProfile: event.target.value })
                    }
                  />
                  <Button
                    kind="ghost"
                    size="sm"
                    disabled={!row.overrideProfile && !row.overrideProfileReason}
                    onClick={() => resetProfileOverride(row.id)}
                  >
                    Reset profile override
                  </Button>
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
