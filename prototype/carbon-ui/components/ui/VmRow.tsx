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
          aria-label={`Select ${vm.name}`}
          hideLabel
          labelText={`Select ${vm.name}`}
          checked={selected}
          onChange={onToggle}
        />
      </td>
      <td>
        <strong>{vm.name}</strong>
        <span>{vm.profile || 'No profile'} | {vm.network || 'No source network'}</span>
      </td>
      <td>
        <ReadinessTag area="Image" status={vm.image} reason={vm.imageReasons} vmName={vm.name} />
        <ReadinessTag area="Migration" status={vm.migration} reason={vm.migrationReasons} vmName={vm.name} />
        <ReadinessTag area="Memory" status={vm.memory} reason={vm.memoryReasons} vmName={vm.name} />
        <ReadinessTag area="Network" status={vm.networkReadiness} reason={vm.networkReasons} vmName={vm.name} />
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
