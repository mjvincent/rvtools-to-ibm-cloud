import type {
  AssignmentVm,
  ImageImportStatus,
  RemediationTracker,
  ResourceState,
  Workflow,
  WorkbookSummary,
} from '../types/network-planning';

export type WorkflowProgressStatus = 'Not started' | 'Needs attention' | 'Ready' | 'Complete';

export type WorkflowProgressStep = {
  workflow: Workflow;
  label: string;
  status: WorkflowProgressStatus;
  reason: string;
  nextAction: string;
};

export type WorkflowProgressInput = {
  summary: WorkbookSummary | null;
  assignmentRows: AssignmentVm[];
  resources: ResourceState;
  remediationTracker: RemediationTracker;
  imageImportStatus: ImageImportStatus;
  selectedProjectId: string;
  terraformStatus: string;
};

function inScopeRows(rows: AssignmentVm[]): AssignmentVm[] {
  return rows.filter((row) => !row.excluded);
}

function isNonReady(value: string | undefined): boolean {
  return value === 'Blocked' || value === 'Review';
}

export function countReadinessFindings(rows: AssignmentVm[]): number {
  return inScopeRows(rows).reduce((count, row) => (
    count
    + [row.image, row.migration, row.memory, row.networkReadiness].filter(isNonReady).length
  ), 0);
}

export function countUnresolvedRemediation(
  rows: AssignmentVm[],
  tracker: RemediationTracker,
): number {
  return inScopeRows(rows).reduce((count, row) => {
    const readinessAreas = [
      ['image', row.image],
      ['migration', row.migration],
      ['memory', row.memory],
      ['network', row.networkReadiness],
    ];
    return count + readinessAreas.filter(([area, status]) => {
      const item = tracker[`${row.id}::${area}`];
      return isNonReady(status) && item?.status !== 'Resolved' && item?.status !== 'Deferred';
    }).length;
  }, 0);
}

export function countMissingPlacement(rows: AssignmentVm[]): number {
  return inScopeRows(rows).filter((row) => !row.subnet || !row.securityGroup).length;
}

export function countMissingWavePlanning(rows: AssignmentVm[]): number {
  return inScopeRows(rows).filter((row) => (
    !row.wave || !row.cutoverGroup || !row.owner || !row.application
  )).length;
}

export function countPendingImageImports(status: ImageImportStatus): number {
  return Object.values(status).filter((entry) => entry.importStatus !== 'Imported').length;
}

function statusForWorkbook(input: WorkflowProgressInput): WorkflowProgressStep {
  if (input.summary || input.selectedProjectId) {
    return {
      workflow: 'intake',
      label: 'Load workbook',
      status: 'Complete',
      reason: input.summary?.filename ? `Workbook loaded: ${input.summary.filename}` : 'Saved project restored.',
      nextAction: 'Review the estate summary and VM rows.',
    };
  }
  if (input.assignmentRows.length > 0) {
    return {
      workflow: 'intake',
      label: 'Load workbook',
      status: 'Ready',
      reason: 'Sample planning rows are available for prototype review.',
      nextAction: 'Upload RVTools or continue with sample rows.',
    };
  }
  return {
    workflow: 'intake',
    label: 'Load workbook',
    status: 'Not started',
    reason: 'No RVTools workbook or saved project is loaded.',
    nextAction: 'Upload an RVTools workbook in Workbook Intake.',
  };
}

function statusForReview(input: WorkflowProgressInput): WorkflowProgressStep {
  const findings = countReadinessFindings(input.assignmentRows);
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'overview',
      label: 'Review inventory',
      status: 'Not started',
      reason: 'Inventory rows are not available yet.',
      nextAction: 'Load a workbook first.',
    };
  }
  return {
    workflow: 'overview',
    label: 'Review inventory',
    status: findings > 0 ? 'Needs attention' : 'Complete',
    reason: findings > 0 ? `${findings} readiness signal(s) need review.` : 'No readiness review signals are currently open.',
    nextAction: findings > 0 ? 'Open Remediation Backlog and review blockers.' : 'Continue to VM Assignment.',
  };
}

function statusForAssignment(input: WorkflowProgressInput): WorkflowProgressStep {
  const gaps = countMissingPlacement(input.assignmentRows);
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'assignment',
      label: 'Place VMs',
      status: 'Not started',
      reason: 'There are no VM rows to assign.',
      nextAction: 'Load a workbook first.',
    };
  }
  return {
    workflow: 'assignment',
    label: 'Place VMs',
    status: gaps > 0 ? 'Needs attention' : 'Complete',
    reason: gaps > 0 ? `${gaps} in-scope VM(s) are missing subnet or security group placement.` : 'In-scope VMs have subnet and security group placement.',
    nextAction: gaps > 0 ? 'Assign missing subnet and security group values.' : 'Review overrides and migration waves.',
  };
}

function statusForRemediation(input: WorkflowProgressInput): WorkflowProgressStep {
  const openItems = countUnresolvedRemediation(input.assignmentRows, input.remediationTracker);
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'remediation',
      label: 'Resolve blockers',
      status: 'Not started',
      reason: 'Readiness findings are not available yet.',
      nextAction: 'Load and review workbook readiness first.',
    };
  }
  return {
    workflow: 'remediation',
    label: 'Resolve blockers',
    status: openItems > 0 ? 'Needs attention' : 'Complete',
    reason: openItems > 0 ? `${openItems} readiness item(s) are unresolved.` : 'No unresolved remediation items are currently open.',
    nextAction: openItems > 0 ? 'Assign owners, update status, or defer with notes.' : 'Continue to image import planning.',
  };
}

function statusForImageImport(input: WorkflowProgressInput): WorkflowProgressStep {
  const pending = countPendingImageImports(input.imageImportStatus);
  const imageReviews = inScopeRows(input.assignmentRows).filter((row) => isNonReady(row.image)).length;
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'imageImport',
      label: 'Plan images',
      status: 'Not started',
      reason: 'Image readiness cannot be reviewed until inventory is loaded.',
      nextAction: 'Load a workbook first.',
    };
  }
  if (pending > 0 || imageReviews > 0) {
    return {
      workflow: 'imageImport',
      label: 'Plan images',
      status: 'Needs attention',
      reason: `${pending} image import group(s) are not imported and ${imageReviews} VM image signal(s) need review.`,
      nextAction: 'Update image import status and target catalog IDs where known.',
    };
  }
  return {
    workflow: 'imageImport',
    label: 'Plan images',
    status: 'Ready',
    reason: 'No pending image import statuses are recorded.',
    nextAction: 'Confirm image IDs before Terraform operators run plan.',
  };
}

function statusForWaves(input: WorkflowProgressInput): WorkflowProgressStep {
  const gaps = countMissingWavePlanning(input.assignmentRows);
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'waves',
      label: 'Plan waves',
      status: 'Not started',
      reason: 'Wave planning needs VM rows.',
      nextAction: 'Load a workbook first.',
    };
  }
  return {
    workflow: 'waves',
    label: 'Plan waves',
    status: gaps > 0 ? 'Needs attention' : 'Complete',
    reason: gaps > 0 ? `${gaps} in-scope VM(s) are missing wave, owner, application, or cutover group.` : 'Wave, owner, application, and cutover context is populated.',
    nextAction: gaps > 0 ? 'Complete wave planning fields.' : 'Review Migration Ops readiness.',
  };
}

function statusForMigrationOps(input: WorkflowProgressInput): WorkflowProgressStep {
  const blockers = countReadinessFindings(input.assignmentRows)
    + countUnresolvedRemediation(input.assignmentRows, input.remediationTracker)
    + countMissingWavePlanning(input.assignmentRows)
    + countPendingImageImports(input.imageImportStatus);
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'migrationOps',
      label: 'Review cutover',
      status: 'Not started',
      reason: 'Cutover readiness needs loaded planning rows.',
      nextAction: 'Load a workbook first.',
    };
  }
  return {
    workflow: 'migrationOps',
    label: 'Review cutover',
    status: blockers > 0 ? 'Needs attention' : 'Ready',
    reason: blockers > 0 ? `${blockers} readiness, planning, remediation, or image signal(s) remain.` : 'Current planning signals do not show cutover blockers.',
    nextAction: blockers > 0 ? 'Use Migration Ops to review grouped blockers.' : 'Proceed to Export Readiness.',
  };
}

function statusForExport(input: WorkflowProgressInput): WorkflowProgressStep {
  const placementGaps = countMissingPlacement(input.assignmentRows);
  const waveGaps = countMissingWavePlanning(input.assignmentRows);
  const unresolved = countUnresolvedRemediation(input.assignmentRows, input.remediationTracker);
  const hasDownloaded = input.terraformStatus.includes('Terraform ZIP downloaded');

  if (hasDownloaded) {
    return {
      workflow: 'export',
      label: 'Build package',
      status: 'Complete',
      reason: 'Terraform ZIP was downloaded in this session.',
      nextAction: 'Hand the ZIP to the Terraform operator with the package README.',
    };
  }
  if (input.assignmentRows.length === 0) {
    return {
      workflow: 'export',
      label: 'Build package',
      status: 'Not started',
      reason: 'Export needs a loaded inventory and saved project.',
      nextAction: 'Load a workbook and save a project before export.',
    };
  }
  if (!input.selectedProjectId) {
    return {
      workflow: 'export',
      label: 'Build package',
      status: 'Needs attention',
      reason: 'Carbon ZIP export needs a saved project.',
      nextAction: 'Save the project before building the Terraform ZIP.',
    };
  }
  if (placementGaps > 0 || waveGaps > 0 || unresolved > 0) {
    return {
      workflow: 'export',
      label: 'Build package',
      status: 'Needs attention',
      reason: `${placementGaps + waveGaps + unresolved} planning or remediation item(s) should be reviewed before export.`,
      nextAction: 'Run Export preflight and resolve queued issues.',
    };
  }
  return {
    workflow: 'export',
    label: 'Build package',
    status: 'Ready',
    reason: 'Planning state is ready for package preflight.',
    nextAction: 'Run preflight, preview Terraform, then download the ZIP.',
  };
}

export function buildWorkflowProgress(input: WorkflowProgressInput): WorkflowProgressStep[] {
  return [
    statusForWorkbook(input),
    statusForReview(input),
    statusForAssignment(input),
    statusForRemediation(input),
    statusForImageImport(input),
    statusForWaves(input),
    statusForMigrationOps(input),
    statusForExport(input),
  ];
}

export function findNextWorkflowStep(steps: WorkflowProgressStep[]): WorkflowProgressStep {
  return steps.find((step) => step.status === 'Needs attention')
    || steps.find((step) => step.status === 'Not started')
    || steps.find((step) => step.status === 'Ready')
    || steps[steps.length - 1];
}
