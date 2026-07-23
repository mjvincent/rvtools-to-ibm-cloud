'use client';

import React from 'react';
import { Tag, Tile } from '@carbon/react';
import type { PreflightResponse, TerraformPreviewResponse } from '../../../hooks/useApi';
import type { PlanningCompleteness, RemediationQueueItem } from '../../../utils/export-workflow';
import { planningGapCount } from './ExportSummaryMetrics';

type CarbonTagType = 'red' | 'green' | 'blue' | 'purple' | 'gray' | 'warm-gray' | 'cyan';

export type ExportResolutionStep = {
  label: string;
  detail: string;
  status: 'Done' | 'Next' | 'Waiting';
  tagType: CarbonTagType;
};

export function buildExportResolutionOrder(params: {
  selectedProjectId: string;
  isDirty: boolean;
  planningCompleteness: PlanningCompleteness;
  preflight: PreflightResponse | null;
  remediationQueue: RemediationQueueItem[];
  terraformPreview: TerraformPreviewResponse | null;
}): ExportResolutionStep[] {
  const gaps = planningGapCount(params.planningCompleteness);
  const blockers = params.preflight?.summary.blockers ?? 0;
  const hasPreflight = Boolean(params.preflight);
  const hasSavedCurrentProject = Boolean(params.selectedProjectId) && !params.isDirty;
  const preflightClear = hasPreflight && blockers === 0;

  const definitions = [
    {
      label: 'Save or load project',
      detail: 'Backend preflight, preview, and ZIP download need a persisted Carbon project.',
      complete: hasSavedCurrentProject,
      ready: true,
    },
    {
      label: 'Resolve planning gaps',
      detail: gaps === 0 ? 'No assignment, CIDR, storage, wave, or label gaps remain.' : `${gaps} planning gap(s) still need review.`,
      complete: gaps === 0,
      ready: hasSavedCurrentProject,
    },
    {
      label: 'Run package preflight',
      detail: hasPreflight ? 'Backend preflight has run against the saved network plan.' : 'Run preflight after the saved plan reflects current work.',
      complete: hasPreflight,
      ready: hasSavedCurrentProject && gaps === 0,
    },
    {
      label: 'Resolve preflight blockers',
      detail: blockers === 0 ? 'No backend preflight blockers remain.' : `${blockers} preflight blocker(s) must be routed or fixed.`,
      complete: hasPreflight && blockers === 0,
      ready: hasPreflight,
    },
    {
      label: 'Preview package files',
      detail: params.terraformPreview ? 'Generated files are available for in-app inspection.' : 'Preview generated files before sharing the handoff.',
      complete: Boolean(params.terraformPreview),
      ready: preflightClear,
    },
    {
      label: 'Download handoff artifacts',
      detail: preflightClear ? 'Download the readiness report or Terraform ZIP when reviewers are satisfied.' : 'Wait until the saved plan is preflight-clear.',
      complete: false,
      ready: preflightClear,
    },
  ];

  const firstActionableIndex = definitions.findIndex((step) => !step.complete && step.ready);

  return definitions.map((step, index) => {
    if (step.complete) {
      return { label: step.label, detail: step.detail, status: 'Done', tagType: 'green' };
    }
    if (index === firstActionableIndex) {
      return { label: step.label, detail: step.detail, status: 'Next', tagType: 'blue' };
    }
    return { label: step.label, detail: step.detail, status: 'Waiting', tagType: 'warm-gray' };
  });
}

type ExportResolutionOrderProps = {
  steps: ExportResolutionStep[];
};

export default function ExportResolutionOrder({ steps }: ExportResolutionOrderProps) {
  return (
    <Tile className="export-resolution-order" aria-label="Recommended resolution order">
      <div className="section-header compact">
        <div>
          <h2>Recommended resolution order</h2>
          <p>Follow this sequence when Export Readiness is not ready for Terraform handoff.</p>
        </div>
        <Tag type="blue">Guided next steps</Tag>
      </div>
      <ol>
        {steps.map((step) => (
          <li key={step.label}>
            <div>
              <strong>{step.label}</strong>
              <p>{step.detail}</p>
            </div>
            <Tag type={step.tagType}>{step.status}</Tag>
          </li>
        ))}
      </ol>
    </Tile>
  );
}
