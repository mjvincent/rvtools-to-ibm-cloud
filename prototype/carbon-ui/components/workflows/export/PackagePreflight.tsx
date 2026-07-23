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
  totalFindingCount?: number;
  showingAllFindings?: boolean;
  suggestionForFinding: (
    finding: PreflightResponse['findings'][number],
  ) => AssignmentSuggestion | null;
  onApplySuggestion: (suggestion: AssignmentSuggestion) => void;
  onOpenFinding: (
    finding: PreflightResponse['findings'][number],
    route: PreflightRoute,
  ) => void;
  onToggleFindings?: () => void;
};

const severityOrder = ['blocker', 'warning', 'info'] as const;

function severityLabel(severity: string) {
  if (severity === 'blocker') return 'Blockers';
  if (severity === 'warning') return 'Warnings';
  if (severity === 'info') return 'Info';
  return 'Other';
}

function severityTagType(severity: string) {
  if (severity === 'blocker') return 'red';
  if (severity === 'warning') return 'warm-gray';
  return 'gray';
}

export type PreflightFindingGroup = {
  severity: string;
  category: string;
  findings: PreflightResponse['findings'];
};

export function groupPreflightFindings(findings: PreflightResponse['findings']): PreflightFindingGroup[] {
  const grouped = new Map<string, PreflightFindingGroup>();
  findings.forEach((finding) => {
    const severity = String(finding.Severity || 'info').toLowerCase();
    const category = finding.Category || 'General';
    const key = `${severity}::${category}`;
    const existing = grouped.get(key);
    if (existing) {
      existing.findings.push(finding);
      return;
    }
    grouped.set(key, { severity, category, findings: [finding] });
  });

  return Array.from(grouped.values()).sort((a, b) => {
    const severityA = severityOrder.indexOf(a.severity as (typeof severityOrder)[number]);
    const severityB = severityOrder.indexOf(b.severity as (typeof severityOrder)[number]);
    const normalizedA = severityA === -1 ? severityOrder.length : severityA;
    const normalizedB = severityB === -1 ? severityOrder.length : severityB;
    if (normalizedA !== normalizedB) return normalizedA - normalizedB;
    return a.category.localeCompare(b.category);
  });
}

export default function PackagePreflight({
  summary,
  findings,
  totalFindingCount = findings.length,
  showingAllFindings = true,
  suggestionForFinding,
  onApplySuggestion,
  onOpenFinding,
  onToggleFindings,
}: PackagePreflightProps) {
  const groupedFindings = groupPreflightFindings(findings);
  const hiddenFindingCount = Math.max(totalFindingCount - findings.length, 0);
  const canToggleFindings = Boolean(onToggleFindings) && (
    totalFindingCount > findings.length || (showingAllFindings && totalFindingCount > 5)
  );

  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Package preflight</h2>
          <p>
            {summary.total} backend finding(s) from the saved Carbon network plan.
            {hiddenFindingCount > 0
              ? ` Showing top ${findings.length}; ${hiddenFindingCount} additional finding(s) are hidden.`
              : totalFindingCount > 5
                ? ' Showing all findings.'
                : ''}
          </p>
        </div>
        <div className="network-actions">
          <Tag type={summary.blockers === 0 ? 'green' : 'red'}>
            {summary.blockers} blocker(s)
          </Tag>
          <Tag type={summary.warnings === 0 ? 'green' : 'warm-gray'}>
            {summary.warnings} warning(s)
          </Tag>
          <Tag type="gray">{summary.info} info</Tag>
          {canToggleFindings && onToggleFindings && (
            <Button
              kind="tertiary"
              size="sm"
              onClick={onToggleFindings}
            >
              {showingAllFindings ? 'Show top findings' : 'Show all findings'}
            </Button>
          )}
        </div>
      </div>
      {findings.length > 0 ? (
        <div className="preflight-finding-groups">
          {groupedFindings.map((group) => (
            <section
              className="preflight-finding-group"
              key={`${group.severity}-${group.category}`}
              aria-label={`${severityLabel(group.severity)} ${group.category}`}
            >
              <div className="preflight-finding-group__header">
                <div>
                  <h3>{severityLabel(group.severity)}</h3>
                  <p>{group.category}</p>
                </div>
                <Tag type={severityTagType(group.severity)}>
                  {group.findings.length} finding(s)
                </Tag>
              </div>
              <div className="resource-list">
                {group.findings.map((finding, index) => {
                  const suggestion = suggestionForFinding(finding);
                  return (
                    <Tile key={`${finding.Subject}-${finding.Category}-${index}`} className="resource-tile">
                      <div className="package-tile__header">
                        <h4>{finding.Subject || 'Package'}</h4>
                        <Tag type={severityTagType(finding.Severity)}>
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
            </section>
          ))}
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
