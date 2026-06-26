'use client';

import React from 'react';
import { Modal, Tag } from '@carbon/react';
import type { AssignmentMode } from '../../types/network-planning';

type PlacementModalProps = {
  open: boolean;
  assignmentMode: AssignmentMode;
  bucketName: string;
  vmCount: number;
  onCancel: () => void;
  onConfirm: () => void;
};

const modeLabels: Record<AssignmentMode, string> = {
  network: 'subnet',
  security: 'security group',
  storage: 'storage profile',
  wave: 'wave',
};

export default function PlacementModal({
  open,
  assignmentMode,
  bucketName,
  vmCount,
  onCancel,
  onConfirm,
}: PlacementModalProps) {
  return (
    <Modal
      open={open}
      modalHeading="Confirm VM placement"
      primaryButtonText="Assign VMs"
      secondaryButtonText="Cancel"
      onRequestClose={onCancel}
      onRequestSubmit={onConfirm}
    >
      <div className="placement-modal-body">
        <Tag type="blue">{modeLabels[assignmentMode]}</Tag>
        <p>
          Assign {vmCount} VM{vmCount === 1 ? '' : 's'} to {bucketName}?
        </p>
      </div>
    </Modal>
  );
}

