'use client';

import React from 'react';
import { Button, Tile } from '@carbon/react';
import type { AssignmentMode } from '../../types/network-planning';

type SubnetDropZoneProps = {
  bucket: Record<string, string>;
  assignmentMode: AssignmentMode;
  children: React.ReactNode;
  selectedCount?: number;
  onAssign: () => void;
  onDropVmIds: (vmIds: string[], bucket: Record<string, string>) => void;
};

function vmIdsFromDrag(event: React.DragEvent<HTMLElement>) {
  const raw = event.dataTransfer.getData('application/json') || event.dataTransfer.getData('text/plain');
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed?.vmIds) ? parsed.vmIds.filter((id: unknown) => typeof id === 'string') : [];
  } catch {
    return raw.split(',').map((id) => id.trim()).filter(Boolean);
  }
}

export default function SubnetDropZone({
  bucket,
  assignmentMode,
  children,
  selectedCount = 0,
  onAssign,
  onDropVmIds,
}: SubnetDropZoneProps) {
  const [dragActive, setDragActive] = React.useState(false);
  const bucketName = bucket.name || 'bucket';
  const modeLabel = assignmentMode === 'network'
    ? 'subnet'
    : assignmentMode === 'security'
      ? 'security group'
      : assignmentMode === 'storage'
        ? 'storage profile'
        : 'migration wave';

  return (
    <Tile
      aria-describedby={`drop-help-${bucket.id || bucketName}`}
      aria-label={`Drop VMs on ${bucketName} ${modeLabel}`}
      className={dragActive ? 'bucket-tile bucket-tile--drop-active' : 'bucket-tile'}
      data-drop-mode={assignmentMode}
      role="region"
      tabIndex={0}
      onDragEnter={(event: React.DragEvent<HTMLElement>) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragOver={(event: React.DragEvent<HTMLElement>) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(event: React.DragEvent<HTMLElement>) => {
        event.preventDefault();
        setDragActive(false);
        const vmIds = vmIdsFromDrag(event);
        if (vmIds.length > 0) {
          onDropVmIds(vmIds, bucket);
        }
      }}
    >
      <div>{children}</div>
      <p className="sr-only" id={`drop-help-${bucket.id || bucketName}`}>
        Drop one or more selected VMs here, or use Assign to place {selectedCount} selected VM{selectedCount === 1 ? '' : 's'}.
      </p>
      <Button
        aria-label={`Assign ${selectedCount} selected VM${selectedCount === 1 ? '' : 's'} to ${bucketName}`}
        size="sm"
        onClick={onAssign}
      >
        Assign
      </Button>
    </Tile>
  );
}
