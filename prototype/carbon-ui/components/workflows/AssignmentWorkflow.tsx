'use client';

import React, { useMemo } from 'react';
import {
  Button,
  Layer,
  Modal,
  Search,
  Select,
  SelectItem,
  Tag,
  TextArea,
  TextInput,
  Tile,
} from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import type { AssignmentMode, AssignmentVm } from '../../types/network-planning';
import DraggableVmRow from '../dnd/DraggableVmRow';
import PlacementModal from '../dnd/PlacementModal';
import SubnetDropZone from '../dnd/SubnetDropZone';

export function textValue(value: unknown) {
  return value === null || value === undefined ? '' : String(value);
}

export function filterAndSortAssignmentRows(
  rows: AssignmentVm[],
  params: {
    searchValue: string;
    readinessFilter: string;
    sortKey: string;
    sortDirection: 'asc' | 'desc';
  },
) {
  const query = params.searchValue.trim().toLowerCase();
  const filteredRows = rows.filter((row) => {
    const matchesSearch = !query || [
      row.name, row.network, row.subnet, row.securityGroup,
      row.wave, row.application, row.owner,
    ].some((value) => value.toLowerCase().includes(query));
    const statuses = [row.image, row.migration, row.memory, row.networkReadiness];
    const matchesReadiness = params.readinessFilter === 'all' || statuses.includes(params.readinessFilter);
    return matchesSearch && matchesReadiness;
  });
  return [...filteredRows].sort((left, right) => {
    const a = textValue((left as Record<string, unknown>)[params.sortKey]).toLowerCase();
    const b = textValue((right as Record<string, unknown>)[params.sortKey]).toLowerCase();
    if (a === b) return left.name.localeCompare(right.name);
    const result = a > b ? 1 : -1;
    return params.sortDirection === 'asc' ? result : -result;
  });
}

function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

function newBucketId(prefix: string, name: string) {
  return `${prefix}-${terraformLabel(name)}-${Date.now()}`;
}

export default function AssignmentWorkflow() {
  const [pendingPlacement, setPendingPlacement] = React.useState<{
    vmIds: string[];
    bucket: Record<string, string>;
    mode: AssignmentMode;
  } | null>(null);
  const { state, dispatch } = useAppState();
  const {
    assignmentRows,
    selectedVmIds,
    searchValue,
    readinessFilter,
    sortKey,
    sortDirection,
    assignmentMode,
    bucketModal,
    bucketDraft,
    resources,
  } = state;

  const filteredRows = useMemo(() => {
    return filterAndSortAssignmentRows(assignmentRows, {
      searchValue,
      readinessFilter,
      sortKey,
      sortDirection,
    });
  }, [assignmentRows, readinessFilter, searchValue, sortDirection, sortKey]);

  const selectedRows = useMemo(
    () => assignmentRows.filter((row) => selectedVmIds.includes(row.id)),
    [assignmentRows, selectedVmIds],
  );

  const allFilteredSelected =
    filteredRows.length > 0 && filteredRows.every((row) => selectedVmIds.includes(row.id));

  function toggleSort(nextKey: string) {
    if (sortKey === nextKey) {
      dispatch({ type: 'SET_SORT_DIRECTION', payload: sortDirection === 'asc' ? 'desc' : 'asc' });
    } else {
      dispatch({ type: 'SET_SORT_KEY', payload: nextKey });
      dispatch({ type: 'SET_SORT_DIRECTION', payload: 'asc' });
    }
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
    } else {
      const filteredIds = new Set(filteredRows.map((row) => row.id));
      dispatch({
        type: 'SET_SELECTED_VM_IDS',
        payload: selectedVmIds.filter((id) => !filteredIds.has(id)),
      });
    }
  }

  function applyAssignment(type: AssignmentMode, bucket: Record<string, string>, vmIds: string[]) {
    const targetIds = [...new Set(vmIds)].filter(Boolean);
    if (targetIds.length === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select or drag one or more VMs before assigning a bucket.' });
      return;
    }
    dispatch({ type: 'SET_PROJECT_ERROR', payload: '' });
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => {
        if (!targetIds.includes(row.id)) return row;
        if (type === 'network') return { ...row, subnet: bucket.name, network: bucket.purpose || row.network };
        if (type === 'security') return { ...row, securityGroup: bucket.name };
        if (type === 'storage') return { ...row, overrideStorageTier: bucket.tier, storageLabel: bucket.label };
        return { ...row, wave: bucket.name, owner: row.owner || bucket.owner, cutoverGroup: row.cutoverGroup || bucket.name };
      }),
    });
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: targetIds });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `${targetIds.length} VM(s) assigned to ${bucket.name}.` });
  }

  function assignSelected(type: AssignmentMode, bucket: Record<string, string>) {
    applyAssignment(type, bucket, selectedVmIds);
  }

  function clearAssignments(vmIds: string[], mode: AssignmentMode = assignmentMode) {
    const targetIds = [...new Set(vmIds)].filter(Boolean);
    if (targetIds.length === 0) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Select one or more VMs before clearing assignments.' });
      return;
    }
    dispatch({ type: 'SET_PROJECT_ERROR', payload: '' });
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => {
        if (!targetIds.includes(row.id)) return row;
        if (mode === 'network') return { ...row, subnet: '' };
        if (mode === 'security') return { ...row, securityGroup: '' };
        if (mode === 'storage') return { ...row, overrideStorageTier: '', storageLabel: '' };
        return { ...row, wave: '', cutoverGroup: '' };
      }),
    });
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: targetIds });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `${targetIds.length} VM ${mode} assignment(s) cleared.` });
  }

  function clearSelectedAssignment() {
    clearAssignments(selectedVmIds);
  }

  function dragVm(row: AssignmentVm, event: React.DragEvent<HTMLTableRowElement>) {
    const vmIds = selectedVmIds.includes(row.id) ? selectedVmIds : [row.id];
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('application/json', JSON.stringify({ vmIds }));
    event.dataTransfer.setData('text/plain', vmIds.join(','));
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: vmIds });
  }

  function requestDropPlacement(vmIds: string[], bucket: Record<string, string>) {
    setPendingPlacement({ vmIds, bucket, mode: assignmentMode });
  }

  function confirmDropPlacement() {
    if (!pendingPlacement) return;
    applyAssignment(pendingPlacement.mode, pendingPlacement.bucket, pendingPlacement.vmIds);
    setPendingPlacement(null);
  }

  function openReadinessWorkflow(
    area: 'Image' | 'Migration' | 'Memory' | 'Network',
    row: AssignmentVm,
  ) {
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [row.id] });
    dispatch({ type: 'SET_SEARCH_VALUE', payload: row.name });
    if (area === 'Image') {
      dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'imageImport' });
      dispatch({ type: 'SET_PROJECT_STATUS', payload: `Review image import planning for ${row.name}.` });
      return;
    }
    if (area === 'Network') {
      dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: 'network' });
      dispatch({ type: 'SET_READINESS_FILTER', payload: row.networkReadiness || 'all' });
      dispatch({ type: 'SET_PROJECT_STATUS', payload: `Review network readiness for ${row.name}.` });
      return;
    }
    dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'remediation' });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `Review ${area.toLowerCase()} readiness for ${row.name} in Remediation Backlog.` });
  }

  function openOverrideWorkflow(row: AssignmentVm) {
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [row.id] });
    dispatch({ type: 'SET_SEARCH_VALUE', payload: row.name });
    dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'overrides' });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `Review profile, storage, and exclusion overrides for ${row.name}.` });
  }

  function openBucketModal(type: AssignmentMode | 'vpc' | 'component') {
    dispatch({ type: 'SET_BUCKET_MODAL', payload: type });
    if (type === 'vpc') {
      dispatch({ type: 'SET_BUCKET_DRAFT', payload: { name: '', label: '', region: 'us-south', notes: '' } });
    } else if (type === 'component') {
      dispatch({ type: 'SET_BUCKET_DRAFT', payload: { name: '', label: '', type: 'Public Gateway', vpcId: resources.vpcs[0]?.id || '', attachment: '', notes: '' } });
    } else if (type === 'network') {
      dispatch({ type: 'SET_BUCKET_DRAFT', payload: { name: '', label: '', vpcId: resources.vpcs[0]?.id || '', zone: 'us-south-1', cidr: '', purpose: '' } });
    } else if (type === 'security') {
      dispatch({ type: 'SET_BUCKET_DRAFT', payload: { name: '', label: '', purpose: '', notes: '' } });
    } else if (type === 'storage') {
      dispatch({ type: 'SET_BUCKET_DRAFT', payload: { name: '', label: '', tier: '3iops-tier', iopsIntent: '', notes: '' } });
    } else {
      dispatch({ type: 'SET_BUCKET_DRAFT', payload: { name: '', owner: '', targetWindow: '', notes: '' } });
    }
  }

  function createBucket() {
    const name = bucketDraft.name?.trim();
    if (!name) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: 'Enter a bucket name before creating it.' });
      return;
    }
    const label = terraformLabel(bucketDraft.label || name);
    const now = new Date().toISOString();
    if (bucketModal === 'vpc') {
      dispatch({
        type: 'SET_RESOURCES',
        payload: {
          ...resources,
          vpcs: [...resources.vpcs, {
            id: newBucketId('vpc', name), name, label,
            region: bucketDraft.region || 'us-south',
            addressPrefixMode: 'manual', addressPrefixes: [],
            tags: {}, notes: bucketDraft.notes || '',
            createdAt: now, updatedAt: now,
          }],
        },
      });
    } else if (bucketModal === 'component') {
      dispatch({
        type: 'SET_RESOURCES',
        payload: {
          ...resources,
          networkComponents: [...(resources.networkComponents || []), {
            id: newBucketId('component', name), name, label,
            type: (bucketDraft.type as any) || 'public_gateway',
            vpcId: bucketDraft.vpcId || resources.vpcs[0]?.id || '',
            attachment: bucketDraft.attachment || '',
            config: {}, tags: {}, notes: bucketDraft.notes || '',
            createdAt: now, updatedAt: now,
          }],
        },
      });
    } else if (bucketModal === 'network') {
      dispatch({
        type: 'SET_RESOURCES',
        payload: {
          ...resources,
          subnets: [...resources.subnets, {
            id: newBucketId('subnet', name), name, label,
            vpcId: bucketDraft.vpcId || resources.vpcs[0]?.id || '',
            zone: bucketDraft.zone || 'us-south-1',
            cidr: bucketDraft.cidr || '',
            purpose: bucketDraft.purpose || '',
            publicGateway: false, tags: {}, notes: '',
            createdAt: now, updatedAt: now,
          }],
        },
      });
    } else if (bucketModal === 'security') {
      dispatch({
        type: 'SET_RESOURCES',
        payload: {
          ...resources,
          securityGroups: [...resources.securityGroups, {
            id: newBucketId('sg', name), name, label,
            vpcId: resources.vpcs[0]?.id || '',
            purpose: bucketDraft.purpose || '',
            rules: [], tags: {}, notes: bucketDraft.notes || '',
            createdAt: now, updatedAt: now,
          }],
        },
      });
    } else if (bucketModal === 'storage') {
      dispatch({
        type: 'SET_RESOURCES',
        payload: {
          ...resources,
          storageProfiles: [...resources.storageProfiles, {
            id: newBucketId('storage', name), name, label,
            tier: bucketDraft.tier || '3iops-tier',
            iopsIntent: bucketDraft.iopsIntent || '',
            notes: bucketDraft.notes || '',
            createdAt: now, updatedAt: now,
          }],
        },
      });
    } else if (bucketModal === 'wave') {
      dispatch({
        type: 'SET_RESOURCES',
        payload: {
          ...resources,
          waves: [...resources.waves, {
            id: newBucketId('wave', name), name,
            owner: bucketDraft.owner || '',
            targetWindow: bucketDraft.targetWindow || '',
            priority: 'medium' as const,
            notes: bucketDraft.notes || '',
            createdAt: now, updatedAt: now,
          }],
        },
      });
    }
    dispatch({ type: 'SET_BUCKET_MODAL', payload: '' });
    dispatch({ type: 'SET_BUCKET_DRAFT', payload: {} });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: `${name} bucket created.` });
  }

  function assignmentBuckets() {
    if (assignmentMode === 'network') {
      return resources.subnets.map((bucket) => ({
        ...bucket,
        details: `${bucket.zone} | ${bucket.cidr || 'CIDR needed'} | ${bucket.purpose || 'No purpose label'}`,
      }));
    }
    if (assignmentMode === 'security') {
      return resources.securityGroups.map((bucket) => ({
        ...bucket,
        details: `${bucket.label} | ${bucket.purpose || 'No purpose label'}`,
      }));
    }
    if (assignmentMode === 'storage') {
      return resources.storageProfiles.map((bucket) => ({
        ...bucket,
        details: `${bucket.tier} | ${(bucket as any).iopsIntent || 'No IOPS note'}`,
      }));
    }
    return resources.waves.map((bucket) => ({
      ...bucket,
      details: `${bucket.owner || 'No owner'} | ${bucket.targetWindow || 'No window'}`,
    }));
  }

  const setBucketDraft = (draft: Record<string, string>) =>
    dispatch({ type: 'SET_BUCKET_DRAFT', payload: draft });

  return (
    <>
      <div className="assignment-layout">
        <Layer className="workbench-section assignment-main">
          <div className="section-header">
            <div>
              <h2>VM Assignment Workbench</h2>
              <p>Select VMs, then assign target subnet, security group, storage/IOPS, and wave buckets.</p>
            </div>
            <Tag type={selectedVmIds.length ? 'blue' : 'gray'}>{selectedVmIds.length} selected</Tag>
          </div>

          <div className="assignment-toolbar">
            <Search
              id="vm-assignment-search"
              labelText="Search VMs"
              placeholder="Search VM, network, subnet, security group, wave, owner"
              value={searchValue}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                dispatch({ type: 'SET_SEARCH_VALUE', payload: event.target.value })
              }
            />
            <Select
              id="readiness-filter"
              labelText="Readiness filter"
              value={readinessFilter}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                dispatch({ type: 'SET_READINESS_FILTER', payload: event.target.value })
              }
            >
              <SelectItem value="all" text="All readiness states" />
              <SelectItem value="Blocked" text="Blocked" />
              <SelectItem value="Review" text="Review" />
              <SelectItem value="Ready" text="Ready" />
            </Select>
          </div>

          <div className="vm-table-wrap">
            <table className="vm-table" aria-label="VM assignment rows">
              <thead>
                <tr>
                  <th>
                    <label className="row-select-label">
                      <input
                        type="checkbox"
                        aria-label="Select all filtered VMs"
                        checked={allFilteredSelected}
                        onChange={(event) => toggleAllFiltered(event.target.checked)}
                      />
                    </label>
                  </th>
                  {[
                    ['name', 'VM'],
                    ['migration', 'Readiness'],
                    ['subnet', 'Subnet'],
                    ['securityGroup', 'Security group'],
                    ['overrideStorageTier', 'Storage / IOPS'],
                    ['wave', 'Wave'],
                    ['power', 'Power'],
                    ['actions', 'Actions'],
                  ].map(([key, label]) => (
                    <th key={key}>
                      <button type="button" onClick={() => toggleSort(key)}>
                        {label}{sortKey === key ? ` ${sortDirection === 'asc' ? 'up' : 'down'}` : ''}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => (
                  <DraggableVmRow
                    key={row.id}
                    row={row}
                    selected={selectedVmIds.includes(row.id)}
                    assignmentMode={assignmentMode}
                    onSelect={toggleSelected}
                    onDragStart={dragVm}
                    onUnassign={(rowId, mode) => clearAssignments([rowId], mode)}
                    onOverride={openOverrideWorkflow}
                    onReadinessAction={openReadinessWorkflow}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </Layer>

        {/* Assignment panel */}
        <Layer className="workbench-section assignment-panel">
          <div className="section-header compact">
            <div>
              <h2>Assignment buckets</h2>
              <p>{selectedRows.length} VM(s) ready for assignment</p>
            </div>
          </div>
          <div className="mode-switcher" role="group" aria-label="Assignment bucket mode">
            {([['network', 'Network'], ['security', 'Security'], ['storage', 'Storage / IOPS'], ['wave', 'Wave']] as const).map(([mode, label]) => (
              <Button
                key={mode}
                kind={assignmentMode === mode ? 'primary' : 'tertiary'}
                size="sm"
                onClick={() => dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: mode })}
              >
                {label}
              </Button>
            ))}
          </div>
          <div className="bucket-actions">
            {assignmentMode === 'network' && (
              <Button kind="tertiary" size="sm" onClick={() => openBucketModal('vpc')}>
                Create VPC
              </Button>
            )}
            <Button kind="secondary" size="sm" onClick={() => openBucketModal(assignmentMode)}>
              {assignmentMode === 'network' ? 'Create subnet' : 'Create bucket'}
            </Button>
            <Button kind="ghost" size="sm" onClick={clearSelectedAssignment}>
              Clear selected
            </Button>
          </div>
          {assignmentMode === 'network' && (
            <div className="vpc-bucket-strip" aria-label="Planned VPC buckets">
              <p className="bucket-group-label">VPCs</p>
              {resources.vpcs.map((vpc) => (
                <Tile key={vpc.id} className="vpc-pill-tile">
                  <strong>{vpc.name}</strong>
                  <span>{vpc.region} | {vpc.label}</span>
                </Tile>
              ))}
            </div>
          )}
          <div className="bucket-list">
            {assignmentMode === 'network' && <p className="bucket-group-label">Subnets assignable to selected VMs</p>}
            {assignmentBuckets().map((bucket) => (
              <SubnetDropZone
                key={bucket.id}
                bucket={bucket as any}
                assignmentMode={assignmentMode}
                selectedCount={selectedVmIds.length}
                onAssign={() => assignSelected(assignmentMode, bucket as any)}
                onDropVmIds={requestDropPlacement}
              >
                <h3>{bucket.name}</h3>
                <p>{(bucket as any).details}</p>
              </SubnetDropZone>
            ))}
          </div>
        </Layer>
      </div>

      <PlacementModal
        open={Boolean(pendingPlacement)}
        assignmentMode={pendingPlacement?.mode || assignmentMode}
        bucketName={pendingPlacement?.bucket.name || ''}
        vmCount={pendingPlacement?.vmIds.length || 0}
        onCancel={() => setPendingPlacement(null)}
        onConfirm={confirmDropPlacement}
      />

      {/* Bucket creation modal */}
      <Modal
        open={Boolean(bucketModal)}
        modalHeading={
          bucketModal === 'vpc'
            ? 'Create VPC bucket'
            : bucketModal === 'component'
              ? 'Create network component'
              : `Create ${assignmentMode === 'network' ? 'subnet' : assignmentMode} bucket`
        }
        primaryButtonText={bucketModal === 'component' ? 'Create component' : 'Create bucket'}
        secondaryButtonText="Cancel"
        onRequestClose={() => dispatch({ type: 'SET_BUCKET_MODAL', payload: '' })}
        onRequestSubmit={createBucket}
      >
        <TextInput
          id="bucket-name"
          labelText="Name"
          value={bucketDraft.name || ''}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setBucketDraft({ ...bucketDraft, name: event.target.value, label: bucketDraft.label || terraformLabel(event.target.value) })
          }
        />
        {bucketModal !== 'wave' && (
          <TextInput
            id="bucket-label"
            labelText="Terraform label"
            value={bucketDraft.label || ''}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              setBucketDraft({ ...bucketDraft, label: terraformLabel(event.target.value) })
            }
          />
        )}
        {bucketModal === 'vpc' && (
          <TextInput
            id="bucket-region"
            labelText="Region"
            value={bucketDraft.region || ''}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              setBucketDraft({ ...bucketDraft, region: event.target.value })
            }
          />
        )}
        {bucketModal === 'component' && (
          <>
            <Select
              id="component-type"
              labelText="Component type"
              value={bucketDraft.type || 'Public Gateway'}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                setBucketDraft({ ...bucketDraft, type: event.target.value })
              }
            >
              <SelectItem value="Address Prefix" text="Address Prefix" />
              <SelectItem value="Public Gateway" text="Public Gateway" />
              <SelectItem value="VPN Gateway" text="VPN Gateway" />
              <SelectItem value="VPE Gateway" text="VPE Gateway" />
              <SelectItem value="Transit Gateway" text="Transit Gateway" />
              <SelectItem value="Application Load Balancer" text="Application Load Balancer" />
              <SelectItem value="Network Load Balancer" text="Network Load Balancer" />
              <SelectItem value="Route Table" text="Route Table" />
              <SelectItem value="Security Group" text="Security Group" />
              <SelectItem value="Network ACL" text="Network ACL" />
              <SelectItem value="Floating IP" text="Floating IP" />
              <SelectItem value="BYOIP Range" text="BYOIP Range" />
              <SelectItem value="Direct Link" text="Direct Link" />
              <SelectItem value="Direct Link on Classic" text="Direct Link on Classic" />
            </Select>
            <Select
              id="component-vpc"
              labelText="VPC"
              value={bucketDraft.vpcId || ''}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                setBucketDraft({ ...bucketDraft, vpcId: event.target.value })
              }
            >
              {resources.vpcs.map((vpc) => (
                <SelectItem key={vpc.id} value={vpc.id} text={vpc.name} />
              ))}
            </Select>
            <TextInput
              id="component-attachment"
              labelText="Attachment or target"
              value={bucketDraft.attachment || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, attachment: event.target.value })
              }
            />
          </>
        )}
        {bucketModal === 'network' && (
          <>
            <Select
              id="bucket-vpc"
              labelText="VPC"
              value={bucketDraft.vpcId || ''}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                setBucketDraft({ ...bucketDraft, vpcId: event.target.value })
              }
            >
              {resources.vpcs.map((vpc) => (
                <SelectItem key={vpc.id} value={vpc.id} text={vpc.name} />
              ))}
            </Select>
            <TextInput
              id="bucket-zone"
              labelText="Zone"
              value={bucketDraft.zone || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, zone: event.target.value })
              }
            />
            <TextInput
              id="bucket-cidr"
              labelText="CIDR"
              value={bucketDraft.cidr || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, cidr: event.target.value })
              }
            />
            <TextInput
              id="bucket-purpose"
              labelText="Purpose label"
              value={bucketDraft.purpose || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, purpose: event.target.value })
              }
            />
          </>
        )}
        {bucketModal === 'security' && (
          <TextInput
            id="bucket-purpose"
            labelText="Purpose label"
            value={bucketDraft.purpose || ''}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              setBucketDraft({ ...bucketDraft, purpose: event.target.value })
            }
          />
        )}
        {bucketModal === 'storage' && (
          <>
            <Select
              id="bucket-tier"
              labelText="Storage tier"
              value={bucketDraft.tier || '3iops-tier'}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                setBucketDraft({ ...bucketDraft, tier: event.target.value })
              }
            >
              <SelectItem value="3iops-tier" text="3iops-tier" />
              <SelectItem value="5iops-tier" text="5iops-tier" />
              <SelectItem value="10iops-tier" text="10iops-tier" />
            </Select>
            <TextInput
              id="bucket-iops-intent"
              labelText="IOPS intent"
              value={bucketDraft.iopsIntent || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, iopsIntent: event.target.value })
              }
            />
          </>
        )}
        {bucketModal === 'wave' && (
          <>
            <TextInput
              id="bucket-owner"
              labelText="Owner"
              value={bucketDraft.owner || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, owner: event.target.value })
              }
            />
            <TextInput
              id="bucket-window"
              labelText="Target window"
              value={bucketDraft.targetWindow || ''}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setBucketDraft({ ...bucketDraft, targetWindow: event.target.value })
              }
            />
          </>
        )}
        {bucketModal !== 'network' && (
          <TextArea
            id="bucket-notes"
            labelText="Notes"
            value={bucketDraft.notes || ''}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
              setBucketDraft({ ...bucketDraft, notes: event.target.value })
            }
          />
        )}
      </Modal>
    </>
  );
}

// Made with Bob
