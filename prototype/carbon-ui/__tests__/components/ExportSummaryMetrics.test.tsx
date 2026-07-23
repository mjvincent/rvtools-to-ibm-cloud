import React from 'react';
import { render, screen } from '@testing-library/react';
import ExportSummaryMetrics, {
  buildExportSummaryMetrics,
  planningGapCount,
} from '../../components/workflows/export/ExportSummaryMetrics';
import type { PlanningCompleteness, RemediationQueueItem } from '../../utils/export-workflow';

const clearPlanning: PlanningCompleteness = {
  missingSubnet: 0,
  missingSg: 0,
  missingStorage: 0,
  missingWave: 0,
  missingCidr: 0,
  invalidLabels: 0,
};

const preflight = {
  project_id: 'project-1',
  project_name: 'Export Project',
  summary: { blockers: 0, warnings: 1, info: 0, total: 1 },
  findings: [],
};

describe('planningGapCount', () => {
  it('sums all export planning gap categories', () => {
    expect(planningGapCount({
      missingSubnet: 1,
      missingSg: 2,
      missingStorage: 3,
      missingWave: 4,
      missingCidr: 5,
      invalidLabels: 6,
    })).toBe(21);
  });
});

describe('buildExportSummaryMetrics', () => {
  it('marks ZIP readiness when saved, gap-free, and preflight has no blockers', () => {
    const metrics = buildExportSummaryMetrics({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight,
      remediationQueue: [],
      terraformPreview: {
        project_id: 'project-1',
        project_name: 'Export Project',
        files: [{ path: 'README.md', category: 'Terraform', size_bytes: 1, content: '#' }],
      },
    });

    expect(metrics).toContainEqual(expect.objectContaining({
      label: 'ZIP readiness',
      value: 'Ready',
      tag: 'Downloadable',
    }));
    expect(metrics).toContainEqual(expect.objectContaining({
      label: 'Preflight',
      value: '0/1',
      tag: 'Warnings',
    }));
    expect(metrics).toContainEqual(expect.objectContaining({
      label: 'Preview status',
      value: '1',
      tag: 'Available',
    }));
  });

  it('marks blockers and planning gaps as not ready', () => {
    const queue = [{ id: 'missing-subnet', source: 'plan-gap' }] as unknown as RemediationQueueItem[];
    const metrics = buildExportSummaryMetrics({
      selectedProjectId: '',
      isDirty: true,
      planningCompleteness: { ...clearPlanning, missingSubnet: 2 },
      preflight: {
        ...preflight,
        summary: { blockers: 1, warnings: 2, info: 0, total: 3 },
      },
      remediationQueue: queue,
      terraformPreview: null,
    });

    expect(metrics).toContainEqual(expect.objectContaining({
      label: 'Saved project',
      value: 'Missing',
      tag: 'Needs save',
    }));
    expect(metrics).toContainEqual(expect.objectContaining({
      label: 'Planning gaps',
      value: '2',
      tag: 'Needs review',
    }));
    expect(metrics).toContainEqual(expect.objectContaining({
      label: 'ZIP readiness',
      value: 'Hold',
      tag: 'Not ready',
    }));
  });
});

describe('ExportSummaryMetrics', () => {
  it('renders the export summary metrics panel', () => {
    const metrics = buildExportSummaryMetrics({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: clearPlanning,
      preflight,
      remediationQueue: [],
      terraformPreview: null,
    });

    render(<ExportSummaryMetrics metrics={metrics} />);

    expect(screen.getByLabelText('Export readiness summary metrics')).toBeTruthy();
    expect(screen.getByText('Saved project')).toBeTruthy();
    expect(screen.getByText('Planning gaps')).toBeTruthy();
    expect(screen.getByText('ZIP readiness')).toBeTruthy();
    expect(screen.getByText('Queue issues')).toBeTruthy();
    expect(screen.getByText('Preview status')).toBeTruthy();
    expect(screen.getByText('Preflight is clear and planning gaps are resolved.')).toBeTruthy();
  });
});
