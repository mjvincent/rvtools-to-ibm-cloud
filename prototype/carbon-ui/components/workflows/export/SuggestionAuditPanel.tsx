'use client';

import React from 'react';
import { Button, Tag, Tile } from '@carbon/react';
import type { SuggestionAuditEntry } from '../../../types/network-planning';
import {
  confidenceTagType,
  suggestionLabels,
} from '../../../utils/export-workflow';

type SuggestionAuditPanelProps = {
  entries: SuggestionAuditEntry[];
  totalCount: number;
  activeCount: number;
  onRevertSuggestion: (entryId: string) => void;
};

export default function SuggestionAuditPanel({
  entries,
  totalCount,
  activeCount,
  onRevertSuggestion,
}: SuggestionAuditPanelProps) {
  if (entries.length === 0) return null;

  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Suggestion audit</h2>
          <p>Review applied recommendation changes and revert any active suggestion before export.</p>
        </div>
        <div className="network-actions">
          <Tag type="blue">{totalCount} total</Tag>
          <Tag type={activeCount === 0 ? 'gray' : 'green'}>{activeCount} active</Tag>
        </div>
      </div>
      <div className="resource-list">
        {entries.map((entry) => (
          <Tile key={entry.id} className="resource-tile">
            <div className="package-tile__header">
              <h3>{entry.vmName}</h3>
              <div className="network-actions">
                <Tag type="blue">{suggestionLabels[entry.field]}</Tag>
                <Tag type={confidenceTagType(entry.confidence)}>
                  {entry.confidence} confidence
                </Tag>
                {entry.revertedAt && <Tag type="gray">Reverted</Tag>}
              </div>
            </div>
            <p>{entry.oldValue || '(blank)'} to {entry.newValue || '(blank)'}</p>
            <p>{entry.reason}</p>
            {entry.evidence.length > 0 && <p>{entry.evidence.slice(0, 2).join(' | ')}</p>}
            <p>Applied {entry.appliedAt}</p>
            <div className="network-actions">
              <Button
                kind="tertiary"
                size="sm"
                disabled={Boolean(entry.revertedAt)}
                onClick={() => onRevertSuggestion(entry.id)}
              >
                Undo suggestion
              </Button>
            </div>
          </Tile>
        ))}
      </div>
    </div>
  );
}
