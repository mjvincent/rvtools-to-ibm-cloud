import fs from 'fs';
import path from 'path';

const workflowFiles = [
  ['overview', 'components/workflows/OverviewWorkflow.tsx'],
  ['intake', 'components/workflows/IntakeWorkflow.tsx'],
  ['assignment', 'components/workflows/AssignmentWorkflow.tsx'],
  ['overrides', 'components/workflows/OverridesWorkflow.tsx'],
  ['remediation', 'components/workflows/RemediationWorkflow.tsx'],
  ['imageImport', 'components/workflows/ImageImportWorkflow.tsx'],
  ['migrationOps', 'components/workflows/MigrationOpsWorkflow.tsx'],
  ['network', 'components/workflows/NetworkPlanWorkflow.tsx'],
  ['security', 'components/workflows/SecurityWorkflow.tsx'],
  ['storage', 'components/workflows/StorageWorkflow.tsx'],
  ['waves', 'components/workflows/WavesWorkflow.tsx'],
  ['export', 'components/workflows/ExportWorkflow.tsx'],
] as const;

describe('workflow completion checklist placement', () => {
  it.each(workflowFiles)('renders visible completion guidance for %s', (workflow, relativePath) => {
    const source = fs.readFileSync(path.join(__dirname, '..', relativePath), 'utf8');

    expect(source).toContain('WorkflowCompletionChecklist');
    expect(source).toContain(`workflow="${workflow}"`);
  });
});
