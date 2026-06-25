'use client';

import React from 'react';
import { Checkbox } from '@carbon/react';
import ReadinessTag from './ReadinessTag';
import type { AssignmentVm } from '../../types/network-planning';

type VmRowProps = {
  vm: AssignmentVm;
  selected: boolean;
  onToggle: () => void;
};

export default function VmRow({ vm, selected, onToggle }: VmRowProps) {
  return (
    <tr>
      <td>
        <Checkbox
          id={`select-${vm.id}`}
          labelText=""
          checked={selected}
          onChange={onToggle}
        />
      </td>
      <td>
        <strong>{vm.name}</strong>
        <span>{vm.profile || 'No profile'} | {vm.network || 'No source network'}</span>
      </td>
      <td>
        <ReadinessTag status={vm.image} />
        <ReadinessTag status={vm.migration} />
        <ReadinessTag status={vm.memory} />
        <ReadinessTag status={vm.networkReadiness} />
      </td>
      <td>{vm.subnet || <span className="empty-value">Unassigned</span>}</td>
      <td>{vm.securityGroup || <span className="empty-value">Unassigned</span>}</td>
      <td>{vm.overrideStorageTier || vm.storageTier || <span className="empty-value">Unassigned</span>}</td>
      <td>{vm.wave || <span className="empty-value">Unassigned</span>}</td>
      <td>{vm.power}</td>
    </tr>
  );
}

// Made with Bob
