'use client';

import React from 'react';
import { Button, Tile } from '@carbon/react';
import type { AssignmentMode } from '../../types/network-planning';

type SubnetDropZoneProps = {
  bucket: Record<string, string>;
  assignmentMode: AssignmentMode;
  children: React.ReactNode;
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
  onAssign,
  onDropVmIds,
}: SubnetDropZoneProps) {
  const [dragActive, setDragActive] = React.useState(false);

  return (
    <Tile
      className={dragActive ? 'bucket-tile bucket-tile--drop-active' : 'bucket-tile'}
      data-drop-mode={assignmentMode}
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
      <Button size="sm" onClick={onAssign}>
        Assign
      </Button>
    </Tile>
  );
}

