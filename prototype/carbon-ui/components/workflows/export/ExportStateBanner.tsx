'use client';

import React from 'react';
import { Button, Tag, Tile } from '@carbon/react';
import type { ExportResolutionStep } from './ExportResolutionOrder';

type CarbonTagType = 'red' | 'green' | 'blue' | 'purple' | 'gray' | 'warm-gray' | 'cyan';

export type ExportStateBannerModel = {
  state: string;
  detail: string;
  nextAction: string;
  tagType: CarbonTagType;
};

const stateByStep: Record<string, Omit<ExportStateBannerModel, 'detail'>> = {
  'Save or load project': {
    state: 'Needs save',
    nextAction: 'Review saved project controls',
    tagType: 'warm-gray',
  },
  'Resolve planning gaps': {
    state: 'Planning gaps',
    nextAction: 'Go to next issue',
    tagType: 'red',
  },
  'Run package preflight': {
    state: 'Ready for preflight',
    nextAction: 'Start package preflight',
    tagType: 'blue',
  },
  'Resolve preflight blockers': {
    state: 'Blockers remain',
    nextAction: 'Go to next issue',
    tagType: 'red',
  },
  'Preview package files': {
    state: 'Ready to preview',
    nextAction: 'Open package preview',
    tagType: 'blue',
  },
  'Download handoff artifacts': {
    state: 'Ready to download',
    nextAction: 'Download readiness report',
    tagType: 'green',
  },
};

export function buildExportStateBanner(steps: ExportResolutionStep[]): ExportStateBannerModel {
  const nextStep = steps.find((step) => step.status === 'Next') || steps[steps.length - 1];
  if (!nextStep) {
    return {
      state: 'Needs review',
      detail: 'Export readiness has not been evaluated yet.',
      nextAction: 'Review export readiness',
      tagType: 'warm-gray',
    };
  }
  const mappedState = stateByStep[nextStep.label] || {
    state: 'Needs review',
    nextAction: 'Review export readiness',
    tagType: 'warm-gray' as CarbonTagType,
  };
  return {
    ...mappedState,
    detail: nextStep.detail,
  };
}

type ExportStateBannerProps = {
  model: ExportStateBannerModel;
  onNextAction?: () => void;
};

export default function ExportStateBanner({ model, onNextAction }: ExportStateBannerProps) {
  return (
    <Tile className="export-state-banner" aria-label="Current export state">
      <div>
        <span>Current export state</span>
        <div className="export-state-banner__headline">
          <strong>{model.state}</strong>
          <Tag type={model.tagType}>Next action</Tag>
        </div>
        <p>{model.detail}</p>
      </div>
      {onNextAction && (
        <Button kind="secondary" size="sm" onClick={onNextAction}>
          {model.nextAction}
        </Button>
      )}
    </Tile>
  );
}
