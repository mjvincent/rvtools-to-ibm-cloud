'use client';

import React from 'react';
import { Tag, Tile } from '@carbon/react';
import type { PreflightResponse, TerraformPreviewResponse } from '../../../hooks/useApi';
import type { PlanningCompleteness, RemediationQueueItem } from '../../../utils/export-workflow';

type CarbonTagType = 'red' | 'green' | 'blue' | 'purple' | 'gray' | 'warm-gray' | 'cyan';

export type ExportSummaryMetric = {
  label: string;
  value: string;
  helper: string;
  tag: string;
  tagType: CarbonTagType;
};

export function planningGapCount(planningCompleteness: PlanningCompleteness) {
  return Object.values(planningCompleteness).reduce((total, count) => total + count, 0);
}

export function buildExportSummaryMetrics(params: {
  selectedProjectId: string;
  isDirty: boolean;
  planningCompleteness: PlanningCompleteness;
  preflight: PreflightResponse | null;
  remediationQueue: RemediationQueueItem[];
  terraformPreview: TerraformPreviewResponse | null;
}): ExportSummaryMetric[] {
  const {
    selectedProjectId,
    isDirty,
    planningCompleteness,
    preflight,
    remediationQueue,
    terraformPreview,
  } = params;
  const gaps = planningGapCount(planningCompleteness);
  const blockers = preflight?.summary.blockers ?? 0;
  const warnings = preflight?.summary.warnings ?? 0;
  const hasPreflight = Boolean(preflight);
  const canDownloadZip = Boolean(selectedProjectId) && gaps === 0 && hasPreflight && blockers === 0;

  return [
    {
      label: 'Saved project',
      value: selectedProjectId ? 'Selected' : 'Missing',
      helper: selectedProjectId
        ? isDirty ? 'Save queued changes before final handoff.' : 'Project is available for backend export actions.'
        : 'Save or load a project before preflight, preview, or ZIP download.',
      tag: selectedProjectId && !isDirty ? 'Ready' : 'Needs save',
      tagType: selectedProjectId && !isDirty ? 'green' : 'warm-gray',
    },
    {
      label: 'Planning gaps',
      value: String(gaps),
      helper: gaps === 0 ? 'Assignments, CIDRs, labels, storage, and waves are complete.' : 'Resolve gaps before relying on ZIP readiness.',
      tag: gaps === 0 ? 'Clear' : 'Needs review',
      tagType: gaps === 0 ? 'green' : 'red',
    },
    {
      label: 'Preflight',
      value: hasPreflight ? `${blockers}/${warnings}` : 'Not run',
      helper: hasPreflight ? 'Shown as blocker(s)/warning(s).' : 'Run preflight after saving the latest plan.',
      tag: !hasPreflight ? 'Required' : blockers > 0 ? 'Blocked' : warnings > 0 ? 'Warnings' : 'Clear',
      tagType: !hasPreflight ? 'warm-gray' : blockers > 0 ? 'red' : warnings > 0 ? 'warm-gray' : 'green',
    },
    {
      label: 'Queue issues',
      value: String(remediationQueue.length),
      helper: remediationQueue.length === 0 ? 'No routed export-readiness issues remain.' : 'Use Resolve next issue or row review actions.',
      tag: remediationQueue.length === 0 ? 'Clear' : 'Action needed',
      tagType: remediationQueue.length === 0 ? 'green' : 'red',
    },
    {
      label: 'Preview status',
      value: terraformPreview ? String(terraformPreview.files.length) : 'Not generated',
      helper: terraformPreview ? 'Generated file(s) are available for in-app inspection.' : 'Preview Terraform before sharing the handoff.',
      tag: terraformPreview ? 'Available' : 'Optional',
      tagType: terraformPreview ? 'blue' : 'gray',
    },
    {
      label: 'ZIP readiness',
      value: canDownloadZip ? 'Ready' : 'Hold',
      helper: canDownloadZip ? 'Preflight is clear and planning gaps are resolved.' : 'Requires saved project, clear planning gaps, and blocker-free preflight.',
      tag: canDownloadZip ? 'Downloadable' : 'Not ready',
      tagType: canDownloadZip ? 'green' : 'warm-gray',
    },
  ];
}

type ExportSummaryMetricsProps = {
  metrics: ExportSummaryMetric[];
};

export default function ExportSummaryMetrics({ metrics }: ExportSummaryMetricsProps) {
  return (
    <div className="export-summary-metrics" aria-label="Export readiness summary metrics">
      {metrics.map((metric) => (
        <Tile className="export-summary-metric" key={metric.label}>
          <div className="export-summary-metric__header">
            <h3>{metric.label}</h3>
            <Tag type={metric.tagType}>{metric.tag}</Tag>
          </div>
          <strong>{metric.value}</strong>
          <p>{metric.helper}</p>
        </Tile>
      ))}
    </div>
  );
}
