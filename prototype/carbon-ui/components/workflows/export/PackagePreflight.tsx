'use client';

import React from 'react';
import { Button, Tag, Tile } from '@carbon/react';
import type { PreflightResponse } from '../../../hooks/useApi';
import {
  confidenceTagType,
  routesForFinding,
  suggestionLabels,
  type AssignmentSuggestion,
  type PreflightRoute,
} from '../../../utils/export-workflow';

type PackagePreflightProps = {
  summary: PreflightResponse['summary'];
  findings: PreflightResponse['findings'];
  suggestionForFinding: (
    finding: PreflightResponse['findings'][number],
  ) => AssignmentSuggestion | null;
  onApplySuggestion: (suggestion: AssignmentSuggestion) => void;
  onOpenFinding: (
    finding: PreflightResponse['findings'][number],
    route: PreflightRoute,
  ) => void;
};

export default function PackagePreflight({
  summary,
  findings,
  suggestionForFinding,
  onApplySuggestion,
  onOpenFinding,
}: PackagePreflightProps) {
  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Package preflight</h2>
          <p>{summary.total} backend finding(s) from the saved Carbon network plan.</p>
        </div>
        <div className="network-actions">
          <Tag type={summary.blockers === 0 ? 'green' : 'red'}>
            {summary.blockers} blocker(s)
          </Tag>
          <Tag type={summary.warnings === 0 ? 'green' : 'warm-gray'}>
            {summary.warnings} warning(s)
          </Tag>
          <Tag type="gray">{summary.info} info</Tag>
        </div>
      </div>
      {findings.length > 0 ? (
        <div className="resource-list">
          {findings.map((finding, index) => {
            const suggestion = suggestionForFinding(finding);
            return (
              <Tile key={`${finding.Subject}-${finding.Category}-${index}`} className="resource-tile">
                <div className="package-tile__header">
                  <h3>{finding.Subject || 'Package'}</h3>
                  <Tag type={finding.Severity === 'blocker' ? 'red' : finding.Severity === 'warning' ? 'warm-gray' : 'gray'}>
                    {finding.Severity}
                  </Tag>
                </div>
                <p>{finding.Message}</p>
                {finding['Fix Category'] && <p>{finding['Fix Category']}</p>}
                {suggestion && (
                  <>
                    <p>
                      Suggested {suggestionLabels[suggestion.kind]}: {suggestion.label}. {suggestion.reason}
                    </p>
                    <div className="network-actions">
                      <Tag type={confidenceTagType(suggestion.confidence)}>
                        {suggestion.confidence} confidence
                      </Tag>
                      {suggestion.evidence.slice(0, 2).map((item) => (
                        <Tag key={item} type="gray">{item}</Tag>
                      ))}
                    </div>
                  </>
                )}
                <div className="network-actions">
                  {suggestion && (
                    <Button
                      kind="tertiary"
                      size="sm"
                      onClick={() => onApplySuggestion(suggestion)}
                    >
                      Apply suggested {suggestionLabels[suggestion.kind]}
                    </Button>
                  )}
                  {routesForFinding(finding).map((route) => (
                    <Button
                      key={route.label}
                      kind="tertiary"
                      size="sm"
                      onClick={() => onOpenFinding(finding, route)}
                    >
                      {route.label}
                    </Button>
                  ))}
                </div>
              </Tile>
            );
          })}
        </div>
      ) : (
        <Tile className="resource-tile">
          <h3>Ready</h3>
          <p>No package preflight findings returned.</p>
        </Tile>
      )}
    </div>
  );
}
