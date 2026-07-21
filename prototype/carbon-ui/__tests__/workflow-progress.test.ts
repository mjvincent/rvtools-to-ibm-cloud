import { defaultResources, sampleRows } from '../store/AppContext';
import {
  buildWorkflowProgress,
  countMissingPlacement,
  countMissingWavePlanning,
  countPendingImageImports,
  countUnresolvedRemediation,
  findNextWorkflowStep,
} from '../utils/workflow-progress';
import type { WorkflowProgressInput } from '../utils/workflow-progress';

function baseInput(overrides: Partial<WorkflowProgressInput> = {}): WorkflowProgressInput {
  return {
    summary: null,
    assignmentRows: sampleRows,
    resources: defaultResources,
    remediationTracker: {},
    imageImportStatus: {},
    selectedProjectId: '',
    terraformStatus: '',
    ...overrides,
  };
}

describe('workflow progress guide helpers', () => {
  it('summarizes placement, wave, remediation, and image gaps', () => {
    const input = baseInput({
      remediationTracker: {
        'sample-db-01::migration': {
          status: 'Open',
          owner: '',
          dueDate: '',
          notes: '',
        },
      },
      imageImportStatus: {
        'windows-2019': {
          targetCatalogId: '',
          importStatus: 'Pending',
          estimatedImportTime: '',
          notes: '',
        },
      },
    });

    expect(countMissingPlacement(input.assignmentRows)).toBe(3);
    expect(countMissingWavePlanning(input.assignmentRows)).toBe(3);
    expect(countUnresolvedRemediation(input.assignmentRows, input.remediationTracker)).toBe(5);
    expect(countPendingImageImports(input.imageImportStatus)).toBe(1);
  });

  it('builds an ordered migration workflow with actionable statuses', () => {
    const steps = buildWorkflowProgress(baseInput());

    expect(steps.map((step) => step.label)).toEqual([
      'Load workbook',
      'Review inventory',
      'Place VMs',
      'Resolve blockers',
      'Plan images',
      'Plan waves',
      'Review cutover',
      'Build package',
    ]);
    expect(steps.find((step) => step.workflow === 'assignment')?.status).toBe('Needs attention');
    expect(findNextWorkflowStep(steps).workflow).toBe('overview');
  });

  it('marks export complete after a Terraform ZIP download status', () => {
    const rows = sampleRows.map((row) => ({
      ...row,
      image: 'Ready',
      migration: 'Ready',
      memory: 'Ready',
      networkReadiness: 'Ready',
      subnet: 'prod-app-us-south-1',
      securityGroup: 'sg-app-private',
      wave: 'Wave 1',
      owner: 'Migration factory',
      application: row.application || 'Application',
      cutoverGroup: 'Cutover A',
    }));
    const steps = buildWorkflowProgress(baseInput({
      assignmentRows: rows,
      selectedProjectId: 'project-1',
      terraformStatus: 'Terraform ZIP downloaded.',
    }));

    expect(steps.find((step) => step.workflow === 'export')?.status).toBe('Complete');
  });
});
