'use client';

import React from 'react';
import { Button, Tag, Tile } from '@carbon/react';
import {
  confidenceTagType,
  suggestionLabels,
  type AssignmentSuggestion,
} from '../../../utils/export-workflow';

type AssignmentSuggestionsPanelProps = {
  suggestions: AssignmentSuggestion[];
  auditedCount: number;
  highConfidenceCount: number;
  onApplyHighConfidence: () => void;
  onApplySuggestion: (suggestion: AssignmentSuggestion) => void;
};

export default function AssignmentSuggestionsPanel({
  suggestions,
  auditedCount,
  highConfidenceCount,
  onApplyHighConfidence,
  onApplySuggestion,
}: AssignmentSuggestionsPanelProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Suggested assignment fixes</h2>
          <p>Review likely fixes inferred from matching VM names, applications, networks, and existing assignments.</p>
        </div>
        <div className="network-actions">
          {auditedCount > 0 && <Tag type="gray">{auditedCount} audited</Tag>}
          <Tag type="blue">{suggestions.length} suggestion(s)</Tag>
          <Tag type="green">{highConfidenceCount} high confidence</Tag>
          <Button
            kind="tertiary"
            size="sm"
            disabled={highConfidenceCount === 0}
            onClick={onApplyHighConfidence}
          >
            Apply high-confidence suggestions
          </Button>
        </div>
      </div>
      <div className="resource-list">
        {suggestions.map((suggestion) => (
          <Tile
            key={`${suggestion.row.id}-${suggestion.kind}-${suggestion.value}`}
            className="resource-tile"
          >
            <div className="package-tile__header">
              <h3>{suggestion.row.name}</h3>
              <div className="network-actions">
                <Tag type="blue">{suggestionLabels[suggestion.kind]}</Tag>
                <Tag type={confidenceTagType(suggestion.confidence)}>
                  {suggestion.confidence} confidence
                </Tag>
              </div>
            </div>
            <p>{suggestion.label}</p>
            <p>{suggestion.reason}</p>
            {suggestion.evidence.length > 0 && (
              <p>{suggestion.evidence.join(' | ')}</p>
            )}
            <div className="network-actions">
              <Button
                kind="tertiary"
                size="sm"
                onClick={() => onApplySuggestion(suggestion)}
              >
                Apply suggestion
              </Button>
            </div>
          </Tile>
        ))}
      </div>
    </div>
  );
}
