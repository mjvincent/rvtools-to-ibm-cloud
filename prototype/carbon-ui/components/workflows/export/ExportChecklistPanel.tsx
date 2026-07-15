'use client';

import React from 'react';
import { Tag, Tile } from '@carbon/react';
import type { ExportChecklistItem } from '../../../utils/export-workflow';

type ExportChecklistPanelProps = {
  checklist: ExportChecklistItem[];
  completeCount: number;
};

export default function ExportChecklistPanel({
  checklist,
  completeCount,
}: ExportChecklistPanelProps) {
  const isReady = completeCount === checklist.length;

  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Export checklist</h2>
          <p>{completeCount}/{checklist.length} readiness item(s) complete before Terraform handoff.</p>
        </div>
        <Tag type={isReady ? 'green' : 'warm-gray'}>
          {isReady ? 'Ready' : 'In progress'}
        </Tag>
      </div>
      <div className="resource-list">
        {checklist.map((item) => (
          <Tile key={item.label} className="resource-tile">
            <div className="package-tile__header">
              <h3>{item.label}</h3>
              <Tag type={item.complete ? 'green' : 'warm-gray'}>
                {item.complete ? 'Complete' : 'Needs review'}
              </Tag>
            </div>
          </Tile>
        ))}
      </div>
    </div>
  );
}
