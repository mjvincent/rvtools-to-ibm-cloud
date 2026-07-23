import React from 'react';
import { render, screen } from '@testing-library/react';
import ExportResolutionOrder, {
  buildExportResolutionOrder,
  type ExportResolutionStep,
} from '../../components/workflows/export/ExportResolutionOrder';
import type { PlanningCompleteness } from '../../utils/export-workflow';

const clearPlanning: PlanningCompleteness = {
  missingSubnet: 0,
  missingSg: 0,
  missingStorage: 0,
  missingWave: 0,
  missingCidr: 0,
  invalidLabels: 0,
};

const clearPreflight = {
  project_id: 'project-1',
  project_name: 'Export Project',
  summary: { blockers: 0, warnings: 0, info: 0, total: 0 },
  findings: [],
};

const blockedPreflight = {
  ...clearPreflight,
  summary: { blockers: 2, warnings: 1, info: 0, total: 3 },
};

function nextStepLabel(steps: ExportResolutionStep[]) {
  return steps.find((step) => step.status === 'Next')?.label;
}

describe('buildExportResolutionOrder', () => {
  it('starts with saving or loading a project when no persisted project is active', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: '',
      isDirty: true,
      planningCompleteness: clearPlanning,
      preflight: null,
      remediationQueue: [],
      terraformPreview: null,
    });

    expect(nextStepLabel(steps)).toBe('Save or load project');
    expect(steps.find((step) => step.label === 'Resolve planning gaps')).toMatchObject({
      status: 'Done',
    });
    expect(steps.find((step) => step.label === 'Run package preflight')).toMatchObject({
      status: 'Waiting',
    });
  });

  it('points users to planning gaps after the saved project is current', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: { ...clearPlanning, missingSubnet: 1, missingWave: 2 },
      preflight: null,
      remediationQueue: [],
      terraformPreview: null,
    });

    expect(steps.find((step) => step.label === 'Save or load project')).toMatchObject({
      status: 'Done',
    });
    expect(nextStepLabel(steps)).toBe('Resolve planning gaps');
  });

  it('moves from clear planning to package preflight', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight: null,
      remediationQueue: [],
      terraformPreview: null,
    });

    expect(nextStepLabel(steps)).toBe('Run package preflight');
  });

  it('routes blockers before package preview and download', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight: blockedPreflight,
      remediationQueue: [],
      terraformPreview: null,
    });

    expect(nextStepLabel(steps)).toBe('Resolve preflight blockers');
    expect(steps.find((step) => step.label === 'Preview package files')).toMatchObject({
      status: 'Waiting',
    });
  });

  it('asks for preview before handoff download once preflight is clear', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight: clearPreflight,
      remediationQueue: [],
      terraformPreview: null,
    });

    expect(nextStepLabel(steps)).toBe('Preview package files');
  });

  it('makes handoff artifacts the next action after preview exists', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight: clearPreflight,
      remediationQueue: [],
      terraformPreview: {
        project_id: 'project-1',
        project_name: 'Export Project',
        files: [{ path: 'README.md', category: 'Terraform', size_bytes: 1, content: '#' }],
      },
    });

    expect(nextStepLabel(steps)).toBe('Download handoff artifacts');
  });
});

describe('ExportResolutionOrder', () => {
  it('renders the recommended resolution panel', () => {
    const steps = buildExportResolutionOrder({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight: clearPreflight,
      remediationQueue: [],
      terraformPreview: null,
    });

    render(<ExportResolutionOrder steps={steps} />);

    expect(screen.getByLabelText('Recommended resolution order')).toBeTruthy();
    expect(screen.getByText('Guided next steps')).toBeTruthy();
    expect(screen.getByText('Save or load project')).toBeTruthy();
    expect(screen.getByText('Resolve planning gaps')).toBeTruthy();
    expect(screen.getByText('Download handoff artifacts')).toBeTruthy();
  });
});
