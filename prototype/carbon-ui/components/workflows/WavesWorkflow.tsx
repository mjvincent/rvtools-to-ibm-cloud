'use client';

import React from 'react';
import { Layer, Tile } from '@carbon/react';
import { useAppState } from '../../store/AppContext';

export default function WavesWorkflow() {
  const { state } = useAppState();
  const { resources } = state;

  const rows = resources.waves.map((bucket) => ({
    name: bucket.name,
    detail: `${bucket.owner || 'No owner'} | ${bucket.targetWindow || 'No target window'}`,
  }));

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Wave Plan</h2>
          <p>Group workloads into migration waves with owners and target windows.</p>
        </div>
      </div>
      <div className="resource-list">
        {rows.map((row) => (
          <Tile key={`Wave Plan-${row.name}`} className="resource-tile">
            <h3>{row.name}</h3>
            <p>{row.detail}</p>
          </Tile>
        ))}
      </div>
    </Layer>
  );
}

// Made with Bob
