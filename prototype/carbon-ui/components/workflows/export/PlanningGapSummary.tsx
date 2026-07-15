'use client';

import React from 'react';
import { Tile } from '@carbon/react';

type PlanningGapSummaryProps = {
  findings: Array<[string, number]>;
};

export default function PlanningGapSummary({ findings }: PlanningGapSummaryProps) {
  return (
    <div className="resource-list">
      {findings.map(([label, count]) => (
        <Tile key={label} className="resource-tile">
          <h3>{label}</h3>
          <p>{count === 0 ? 'Ready' : `${count} item(s) need attention`}</p>
        </Tile>
      ))}
    </div>
  );
}
