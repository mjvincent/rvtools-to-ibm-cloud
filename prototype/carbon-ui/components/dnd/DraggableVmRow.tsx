'use client';

import React from 'react';
import { Checkbox, Tag } from '@carbon/react';
import type { AssignmentMode, AssignmentVm } from '../../types/network-planning';
import ReadinessTag from '../ui/ReadinessTag';

type DraggableVmRowProps = {
  row: AssignmentVm;
  selected: boolean;
  assignmentMode: AssignmentMode;
  onSelect: (rowId: string, checked: boolean) => void;
  onDragStart: (row: AssignmentVm, event: React.DragEvent<HTMLTableRowElement>) => void;
  onUnassign: (rowId: string, assignmentMode: AssignmentMode) => void;
  onOverride?: (row: AssignmentVm) => void;
  onReadinessAction?: (area: 'Image' | 'Migration' | 'Memory' | 'Network', row: AssignmentVm) => void;
};

export default function DraggableVmRow({
  row,
  selected,
  assignmentMode,
  onSelect,
  onDragStart,
  onUnassign,
  onOverride,
  onReadinessAction,
}: DraggableVmRowProps) {
  return (
    <tr
      className={selected ? 'vm-row vm-row--selected' : 'vm-row'}
      data-vm-id={row.id}
      draggable
      onDragStart={(event) => onDragStart(row, event)}
    >
      <td>
        <Checkbox
          id={`select-${row.id}`}
          aria-label={`Select ${row.name}`}
          labelText={`Select ${row.name}`}
          checked={selected}
          onChange={(_: unknown, data: { checked?: boolean }) =>
            onSelect(row.id, Boolean(data.checked))
          }
        />
      </td>
      <td>
        <strong>{row.name}</strong>
        <span>{row.profile || 'No profile'} | {row.network || 'No source network'}</span>
      </td>
      <td>
        <ReadinessTag
          area="Image"
          status={row.image}
          reason={row.imageReasons}
          vmName={row.name}
          onAction={onReadinessAction ? () => onReadinessAction('Image', row) : undefined}
        />
        <ReadinessTag
          area="Migration"
          status={row.migration}
          reason={row.migrationReasons}
          vmName={row.name}
          onAction={onReadinessAction ? () => onReadinessAction('Migration', row) : undefined}
        />
        <ReadinessTag
          area="Memory"
          status={row.memory}
          reason={row.memoryReasons}
          vmName={row.name}
          onAction={onReadinessAction ? () => onReadinessAction('Memory', row) : undefined}
        />
        <ReadinessTag
          area="Network"
          status={row.networkReadiness}
          reason={row.networkReasons}
          vmName={row.name}
          onAction={onReadinessAction ? () => onReadinessAction('Network', row) : undefined}
        />
      </td>
      <td>
        {row.subnet ? <Tag type="cyan">{row.subnet}</Tag> : <span className="empty-value">Unassigned</span>}
      </td>
      <td>{row.securityGroup || <span className="empty-value">Unassigned</span>}</td>
      <td>{row.overrideStorageTier || row.storageTier || <span className="empty-value">Unassigned</span>}</td>
      <td>
        {row.wave ? <Tag type="purple">{row.wave}</Tag> : <span className="empty-value">Unassigned</span>}
      </td>
      <td>{row.power}</td>
      <td>
        <details className="row-overflow">
          <summary aria-label={`Placement actions for ${row.name}`}>Actions</summary>
          <button
            type="button"
            disabled={!row.subnet}
            onClick={() => onUnassign(row.id, 'network')}
          >
            Clear subnet
          </button>
          <button
            type="button"
            disabled={!row.securityGroup}
            onClick={() => onUnassign(row.id, 'security')}
          >
            Clear security group
          </button>
          <button
            type="button"
            disabled={!row.overrideStorageTier && !row.storageLabel}
            onClick={() => onUnassign(row.id, 'storage')}
          >
            Clear storage override
          </button>
          <button
            type="button"
            disabled={!row.wave && !row.cutoverGroup}
            onClick={() => onUnassign(row.id, 'wave')}
          >
            Clear wave
          </button>
          {onOverride && (
            <button type="button" onClick={() => onOverride(row)}>
              Review overrides
            </button>
          )}
        </details>
      </td>
    </tr>
  );
}
