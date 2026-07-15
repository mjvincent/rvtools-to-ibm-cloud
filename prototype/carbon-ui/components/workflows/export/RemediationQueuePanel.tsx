'use client';

import React from 'react';
import { Button, Checkbox, Tag, Tile } from '@carbon/react';
import {
  confidenceTagType,
  suggestionKey,
  suggestionLabels,
  type AssignmentSuggestion,
  type RemediationQueueItem,
} from '../../../utils/export-workflow';

type RemediationQueuePanelProps = {
  remediationQueue: RemediationQueueItem[];
  uniqueSuggestionCount: number;
  selectedSuggestionCount: number;
  highConfidenceSuggestionCount: number;
  selectedSuggestionIds: string[];
  suggestionForItem: (item: RemediationQueueItem) => AssignmentSuggestion | null;
  onSelectHighConfidence: () => void;
  onClearSelection: () => void;
  onApplySelected: () => void;
  onToggleSuggestion: (suggestion: AssignmentSuggestion, checked: boolean) => void;
  onApplySuggestion: (suggestion: AssignmentSuggestion) => void;
  onReviewIssue: (item: RemediationQueueItem) => void;
};

export default function RemediationQueuePanel({
  remediationQueue,
  uniqueSuggestionCount,
  selectedSuggestionCount,
  highConfidenceSuggestionCount,
  selectedSuggestionIds,
  suggestionForItem,
  onSelectHighConfidence,
  onClearSelection,
  onApplySelected,
  onToggleSuggestion,
  onApplySuggestion,
  onReviewIssue,
}: RemediationQueuePanelProps) {
  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Remediation queue</h2>
          <p>{remediationQueue.length === 0 ? 'No unresolved export readiness issues.' : `${remediationQueue.length} issue(s) sorted by export priority.`}</p>
        </div>
        <div className="network-actions">
          <Tag type={remediationQueue.length === 0 ? 'green' : 'warm-gray'}>
            {remediationQueue.length === 0 ? 'Clear' : 'Action needed'}
          </Tag>
          <Tag type={uniqueSuggestionCount === 0 ? 'gray' : 'blue'}>
            {uniqueSuggestionCount} suggested
          </Tag>
          <Tag type={selectedSuggestionCount === 0 ? 'gray' : 'green'}>
            {selectedSuggestionCount} selected
          </Tag>
          <Button
            kind="tertiary"
            size="sm"
            disabled={highConfidenceSuggestionCount === 0}
            onClick={onSelectHighConfidence}
          >
            Select high confidence
          </Button>
          <Button
            kind="tertiary"
            size="sm"
            disabled={selectedSuggestionCount === 0}
            onClick={onClearSelection}
          >
            Clear selection
          </Button>
          <Button
            kind="secondary"
            size="sm"
            disabled={selectedSuggestionCount === 0}
            onClick={onApplySelected}
          >
            Apply selected fixes
          </Button>
        </div>
      </div>
      {remediationQueue.length > 0 ? (
        <div className="remediation-queue">
          {remediationQueue.map((item, index) => {
            const suggestion = suggestionForItem(item);
            const key = suggestion ? suggestionKey(suggestion) : '';
            const selected = selectedSuggestionIds.includes(key);
            return (
              <Tile key={item.id} className="remediation-queue__item">
                <div className="remediation-queue__rank">P{index + 1}</div>
                <div className="remediation-queue__body">
                  <div className="package-tile__header">
                    <div>
                      <h3>{item.title}</h3>
                      <p>{item.subject}</p>
                    </div>
                    <div className="network-actions">
                      <Tag type={item.tagType}>{item.severity}</Tag>
                      <Tag type="gray">{item.tag}</Tag>
                    </div>
                  </div>
                  <p>{item.detail}</p>
                  {suggestion ? (
                    <div className="remediation-queue__suggestion">
                      <Checkbox
                        id={`queue-suggestion-${key}`}
                        labelText={`Select suggested ${suggestionLabels[suggestion.kind]} for ${suggestion.row.name}`}
                        checked={selected}
                        onChange={(_, data) => onToggleSuggestion(suggestion, Boolean(data.checked))}
                      />
                      <div>
                        <p>
                          Suggested {suggestionLabels[suggestion.kind]}: {suggestion.label}
                        </p>
                        <div className="network-actions">
                          <Tag type={confidenceTagType(suggestion.confidence)}>
                            {suggestion.confidence} confidence
                          </Tag>
                          {suggestion.evidence.slice(0, 2).map((evidence) => (
                            <Tag key={evidence} type="gray">{evidence}</Tag>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p>No automatic suggestion is available for this issue.</p>
                  )}
                </div>
                <div className="remediation-queue__action">
                  {suggestion && (
                    <Button
                      kind="tertiary"
                      size="sm"
                      onClick={() => onApplySuggestion(suggestion)}
                    >
                      Apply fix
                    </Button>
                  )}
                  <Button
                    kind="tertiary"
                    size="sm"
                    onClick={() => onReviewIssue(item)}
                  >
                    Review issue
                  </Button>
                </div>
              </Tile>
            );
          })}
        </div>
      ) : (
        <Tile className="resource-tile">
          <h3>Ready</h3>
          <p>All tracked export readiness items are clear.</p>
        </Tile>
      )}
    </div>
  );
}
