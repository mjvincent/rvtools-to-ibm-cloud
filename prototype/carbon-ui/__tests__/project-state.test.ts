import { sampleRows } from '../store/AppContext';
import {
  buildProjectStatePayload,
  normalizeProjectState,
} from '../utils/project-state';
import type { SavedProjectState } from '../types/network-planning';

describe('project-state helpers', () => {
  it('builds Carbon and planning-state compatible project payloads', () => {
    const payload = buildProjectStatePayload({
      assignmentRows: sampleRows,
      summary: { filename: 'rvtools.xlsx' } as any,
      resources: { vpcs: [] },
      remediationTracker: {
        'sample-db-01::migration': {
          status: 'In Progress',
          owner: 'Migration lead',
          dueDate: '2026-08-01',
          notes: 'Validate migration blocker',
          vmKey: 'sample-db-01',
          vm_key: 'sample-db-01',
          blockerType: 'Migration',
          blocker_type: 'Migration',
          blockerDescription: 'Resolve migration finding',
          blocker_description: 'Resolve migration finding',
        },
      },
      imageImportStatus: {
        'windows-template': {
          targetCatalogId: 'r006-custom-image',
          importStatus: 'Imported',
          estimatedImportTime: '2026-08-02',
          notes: 'Ready for Terraform image ID replacement',
        },
      },
      suggestionAudit: [{
        id: 'audit-1',
        vmId: 'sample-app-01',
        vmName: 'app-01',
        field: 'subnet',
        oldValue: '',
        newValue: 'prod-app-us-south-1',
        confidence: 'High',
        reason: 'Matched application network',
        evidence: ['network token match'],
        appliedAt: '2026-07-14T12:00:00Z',
      }],
      projectName: 'Migration assessment',
    });

    expect(payload.schema_version).toBe('carbon-prototype-0.3');
    expect(payload.vm_decisions[0]).toMatchObject({
      'VM Key': 'sample-app-01',
      'VM Name': 'app-01',
      Network: 'app-net',
    });
    expect(payload.remediation_tracker['sample-db-01::migration']).toMatchObject({
      due_date: '2026-08-01',
      vm_key: 'sample-db-01',
      blocker_type: 'Migration',
    });
    expect(payload.image_import_status['windows-template']).toMatchObject({
      target_catalog_id: 'r006-custom-image',
      import_status: 'Imported',
    });
    expect(payload.suggestion_audit[0]).toMatchObject({
      vm_id: 'sample-app-01',
      field: 'subnet',
      confidence: 'High',
    });
  });

  it('normalizes Streamlit-compatible project state into Carbon state', () => {
    const savedState: SavedProjectState = {
      planning_state_json: {
        remediation_tracker: {
          'sample-db-01::migration': {
            status: 'In Progress',
            owner: 'Migration lead',
            due_date: '2026-08-01',
            notes: 'Validate migration blocker',
          },
        },
        image_import_status: {
          'windows-template': {
            target_catalog_id: 'r006-custom-image',
            import_status: 'Imported',
            estimated_import_time: '2026-08-02',
            notes: 'Ready',
          },
        },
        suggestion_audit: [{
          id: 'audit-1',
          vm_id: 'sample-app-01',
          vm_name: 'app-01',
          field: 'subnet',
          old_value: '',
          new_value: 'prod-app-us-south-1',
          confidence: 'High',
          reason: 'Matched application network',
          evidence: ['network token match'],
          applied_at: '2026-07-14T12:00:00Z',
        }],
      },
    };

    const normalized = normalizeProjectState(savedState);

    expect(normalized.remediationTracker['sample-db-01::migration']).toMatchObject({
      status: 'In Progress',
      owner: 'Migration lead',
      dueDate: '2026-08-01',
      vmKey: 'sample-db-01',
    });
    expect(normalized.imageImportStatus['windows-template']).toMatchObject({
      targetCatalogId: 'r006-custom-image',
      importStatus: 'Imported',
      estimatedImportTime: '2026-08-02',
    });
    expect(normalized.suggestionAudit[0]).toMatchObject({
      vmId: 'sample-app-01',
      vmName: 'app-01',
      field: 'subnet',
      newValue: 'prod-app-us-south-1',
      confidence: 'High',
    });
  });
});
