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
  onUnassign: (rowId: string) => void;
};

export default function DraggableVmRow({
  row,
  selected,
  assignmentMode,
  onSelect,
  onDragStart,
  onUnassign,
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
          labelText=""
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
        <ReadinessTag status={row.image} />
        <ReadinessTag status={row.migration} />
        <ReadinessTag status={row.memory} />
        <ReadinessTag status={row.networkReadiness} />
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
          <button type="button" onClick={() => onUnassign(row.id)}>
            Unassign {assignmentMode}
          </button>
        </details>
      </td>
    </tr>
  );
}

