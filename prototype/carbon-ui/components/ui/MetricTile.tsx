'use client';

import React from 'react';
import { Tile } from '@carbon/react';

type MetricTileProps = {
  value: number | string;
  label: string;
  unit?: string;
  helper?: string;
  onClick?: () => void;
};

export default function MetricTile({ value, label, unit, helper, onClick }: MetricTileProps) {
  return (
    <Tile
      className={onClick ? 'metric-tile metric-tile--button' : 'metric-tile'}
      onClick={onClick}
    >
      <p className="metric-label">{label}</p>
      <p className="metric-value">
        {value}
        {unit && <span className="metric-unit"> {unit}</span>}
      </p>
      {helper && <p className="metric-helper">{helper}</p>}
    </Tile>
  );
}

// Made with Bob
