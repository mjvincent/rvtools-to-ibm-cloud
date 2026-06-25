'use client';

import React from 'react';
import { Button, Tile } from '@carbon/react';

type BucketCardProps = {
  title: string;
  subtitle?: string;
  items: string[];
  onAdd?: () => void;
};

export default function BucketCard({ title, subtitle, items, onAdd }: BucketCardProps) {
  return (
    <Tile className="bucket-tile">
      <div className="bucket-tile-header">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {onAdd && (
          <Button kind="ghost" size="sm" onClick={onAdd}>
            Add
          </Button>
        )}
      </div>
      {items.length > 0 && (
        <ul className="bucket-item-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
      {items.length === 0 && (
        <p className="bucket-empty">No items assigned</p>
      )}
    </Tile>
  );
}

// Made with Bob
