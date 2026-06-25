'use client';

import React from 'react';
import { Layer, Tile } from '@carbon/react';
import { useAppState } from '../../store/AppContext';

export default function SecurityWorkflow() {
  const { state } = useAppState();
  const { resources } = state;

  const rows = resources.securityGroups.map((bucket) => ({
    name: bucket.name,
    detail: `${bucket.label} | ${bucket.purpose || 'No purpose label'}`,
  }));

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Security Plan</h2>
          <p>Create security group intent buckets for Terraform review and VM assignment.</p>
        </div>
      </div>
      <div className="resource-list">
        {rows.map((row) => (
          <Tile key={`Security Plan-${row.name}`} className="resource-tile">
            <h3>{row.name}</h3>
            <p>{row.detail}</p>
          </Tile>
        ))}
      </div>
    </Layer>
  );
}

// Made with Bob
