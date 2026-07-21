import type { Workflow } from '../types/network-planning';

export type WorkflowHelpContent = {
  workflow: Workflow;
  title: string;
  purpose: string;
  beforeContinuing: string[];
  completeWhen: string[];
  commonMistakes: string[];
  nextStep: string;
};

export const workflowHelpContent: Record<Workflow, WorkflowHelpContent> = {
  overview: {
    workflow: 'overview',
    title: 'Overview',
    purpose: 'Use Overview to understand the estate summary, current readiness posture, and where the migration plan needs attention first.',
    beforeContinuing: ['Confirm a workbook is loaded or a saved project is restored.', 'Review high-level blockers and missing planning counts.'],
    completeWhen: ['You know which workflow needs review next.', 'The sample or customer workbook summary looks credible.'],
    commonMistakes: ['Treating Overview as a final approval step.', 'Ignoring missing assignment or remediation counts before export.'],
    nextStep: 'Go to Workbook Intake for a new workbook, or VM Assignment when the workbook is already loaded.',
  },
  intake: {
    workflow: 'intake',
    title: 'Workbook Intake',
    purpose: 'Upload an RVTools workbook so Carbon can build the VM inventory, readiness signals, and migration planning rows.',
    beforeContinuing: ['Use a valid RVTools .xlsx workbook.', 'Start with samples/rvtools-small-complete.xlsx for a clean first run.'],
    completeWhen: ['Upload succeeds.', 'Summary metrics and VM rows appear in VM Assignment.'],
    commonMistakes: ['Uploading a non-RVTools workbook.', 'Continuing after an upload error without retrying or checking the workbook.'],
    nextStep: 'Go to VM Assignment and confirm subnet, security, storage, and wave placement.',
  },
  assignment: {
    workflow: 'assignment',
    title: 'VM Assignment',
    purpose: 'Place VMs into target subnet, security group, storage, and wave buckets before Terraform handoff.',
    beforeContinuing: ['Review readiness chips for blocked or review items.', 'Create or confirm assignment buckets for the migration target.'],
    completeWhen: ['In-scope VMs have subnet and security group assignments.', 'Storage and wave placement are reviewed or intentionally deferred.'],
    commonMistakes: ['Using drag/drop only and missing keyboard assignment controls.', 'Leaving in-scope VMs unassigned before Export.'],
    nextStep: 'Go to VM Overrides for sizing exceptions, or Network Plan to review the target topology.',
  },
  overrides: {
    workflow: 'overrides',
    title: 'VM Overrides',
    purpose: 'Capture intentional profile, storage, and exclusion decisions with reasons for audit and handoff.',
    beforeContinuing: ['Review readiness and sizing recommendations.', 'Have workload-owner approval for manual overrides.'],
    completeWhen: ['Overrides have reasons.', 'Excluded VMs have clear exclusion reasons.'],
    commonMistakes: ['Changing profiles without a reason.', 'Using exclusion as a shortcut for fixable readiness issues.'],
    nextStep: 'Go to Remediation Backlog for blockers, or Export Readiness when planning is complete.',
  },
  remediation: {
    workflow: 'remediation',
    title: 'Remediation Backlog',
    purpose: 'Track readiness blockers with owner, status, due date, and notes so the migration team knows what must be resolved.',
    beforeContinuing: ['Review Blocked and Review readiness signals.', 'Assign owners for items that need action.'],
    completeWhen: ['Open blockers have an owner and status.', 'Resolved or deferred items are clearly marked.'],
    commonMistakes: ['Leaving blocker ownership blank.', 'Marking an item resolved without notes when evidence is needed.'],
    nextStep: 'Go to Image Import Planning for image readiness work, then Migration Ops for cutover status.',
  },
  imageImport: {
    workflow: 'imageImport',
    title: 'Image Import Planning',
    purpose: 'Group source images and track conversion/import status before Terraform operators replace image placeholders.',
    beforeContinuing: ['Review image readiness reasons.', 'Identify who owns conversion, COS staging, and IBM Cloud custom image import.'],
    completeWhen: ['Each image group has an import status.', 'Imported images have target catalog IDs when known.'],
    commonMistakes: ['Assuming this app imports images.', 'Leaving image groups Pending before cutover readiness review.'],
    nextStep: 'Go to Migration Ops to see whether image status blocks cutover.',
  },
  migrationOps: {
    workflow: 'migrationOps',
    title: 'Migration Ops',
    purpose: 'Review cutover readiness across waves, owners, remediation status, and image import status.',
    beforeContinuing: ['Complete wave, owner, cutover group, remediation, and image import fields where possible.'],
    completeWhen: ['Ready rows are explainable.', 'Blocked or Review rows have clear next actions.'],
    commonMistakes: ['Treating Review as Ready.', 'Ignoring missing planning fields because Terraform can still be generated.'],
    nextStep: 'Go to Export Readiness when blockers are understood and planning data is ready for handoff.',
  },
  network: {
    workflow: 'network',
    title: 'Network Plan',
    purpose: 'Review the IBM Cloud VPC target topology, subnet CIDRs, and network components before Terraform package generation.',
    beforeContinuing: ['Check the Network validation panel.', 'Edit network components that need a VPC, attachment, or clearer notes.'],
    completeWhen: ['No local network validation blockers remain.', 'The diagram matches the intended landing-zone design.'],
    commonMistakes: ['Ignoring missing subnet CIDRs.', 'Leaving stale VPC references or duplicate Terraform labels.'],
    nextStep: 'Go to Security Plan or Export Readiness after topology blockers are resolved.',
  },
  security: {
    workflow: 'security',
    title: 'Security Plan',
    purpose: 'Review target security group intent for VMs and subnets before Terraform handoff.',
    beforeContinuing: ['Confirm security group bucket names and purpose labels.', 'Route unresolved security gaps from VM Assignment or Export.'],
    completeWhen: ['In-scope VMs have security group placement.', 'Security groups have understandable purpose labels.'],
    commonMistakes: ['Using one generic group for everything without review.', 'Forgetting management and app-to-db traffic needs.'],
    nextStep: 'Go to Storage / IOPS Plan or Export Readiness depending on remaining gaps.',
  },
  storage: {
    workflow: 'storage',
    title: 'Storage / IOPS Plan',
    purpose: 'Review storage profile intent and IOPS-sensitive exceptions for the Terraform handoff package.',
    beforeContinuing: ['Review storage recommendations and workload sensitivity.', 'Confirm owners approve high-IOPS choices.'],
    completeWhen: ['Storage tiers are assigned or intentionally accepted.', 'Any high-impact overrides have reasons.'],
    commonMistakes: ['Overriding storage tier without approval.', 'Assuming the default tier is correct for every database workload.'],
    nextStep: 'Go to Wave Plan or VM Overrides when exceptions need audit reasons.',
  },
  waves: {
    workflow: 'waves',
    title: 'Wave Plan',
    purpose: 'Group VMs by migration wave, cutover group, owner, application, and dependency context.',
    beforeContinuing: ['Confirm application/dependency groupings with migration stakeholders.', 'Use bulk assignment only when the scope is clear.'],
    completeWhen: ['In-scope VMs have wave and cutover context.', 'Owners and applications are populated where needed.'],
    commonMistakes: ['Assigning waves without dependency review.', 'Leaving owner/cutover group blank until after export.'],
    nextStep: 'Go to Migration Ops to inspect cutover readiness by wave and cutover group.',
  },
  export: {
    workflow: 'export',
    title: 'Export Readiness',
    purpose: 'Run final package checks, preview generated files, and download the Terraform handoff ZIP.',
    beforeContinuing: ['Save the project.', 'Resolve local planning gaps and run preflight.', 'Review blocker and warning findings.'],
    completeWhen: ['Preflight blockers are cleared or intentionally handled.', 'The preview and downloaded ZIP contents are acceptable.'],
    commonMistakes: ['Downloading without reviewing preflight findings.', 'Assuming Carbon runs Terraform or imports images.'],
    nextStep: 'Give the ZIP and operator README/checklist to the Terraform operator; keep Streamlit available as fallback during pilot.',
  },
};

export function helpForWorkflow(workflow: Workflow): WorkflowHelpContent {
  return workflowHelpContent[workflow];
}

export function allWorkflowHelp(): WorkflowHelpContent[] {
  return Object.values(workflowHelpContent);
}
