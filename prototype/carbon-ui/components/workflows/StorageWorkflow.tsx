'use client';

import React from 'react';
import { Layer, Tile } from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import WorkflowCompletionChecklist from '../ui/WorkflowCompletionChecklist';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';

export default function StorageWorkflow() {
  const { state } = useAppState();
  const { resources } = state;

  const rows = resources.storageProfiles.map((bucket) => ({
    name: bucket.name,
    detail: `${bucket.tier} | ${bucket.label} | ${(bucket as any).iopsIntent || 'No IOPS note'}`,
  }));

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Storage / IOPS Plan</h2>
          <p>Create storage intent buckets with labels that can later flow into Terraform naming and handoff files.</p>
        </div>
        <WorkflowHeaderHelp workflow="storage" />
      </div>
      <WorkflowCompletionChecklist workflow="storage" />
      <div className="resource-list">
        {rows.map((row) => (
          <Tile key={`Storage / IOPS Plan-${row.name}`} className="resource-tile">
            <h3>{row.name}</h3>
            <p>{row.detail}</p>
          </Tile>
        ))}
      </div>
    </Layer>
  );
}

// Made with Bob
