import { defaultResources, sampleRows } from '../store/AppContext';
import {
  buildNetworkPlanBody,
  exportNetworkPlanJson,
  parseNetworkPlanJson,
  resourcesFromNetworkPlan,
  rowsFromNetworkPlan,
  vmAssignmentsFromRows,
} from '../utils/planning-state';

describe('planning-state API adapter', () => {
  it('builds the snake_case network-plan body expected by FastAPI', () => {
    const body = buildNetworkPlanBody({
      resources: defaultResources,
      assignmentRows: sampleRows,
      projectName: 'Migration assessment',
      summary: { filename: 'rvtools.xlsx' } as any,
    });

    expect(body.security_groups).toHaveLength(defaultResources.securityGroups.length);
    expect(body.storage_profiles).toHaveLength(defaultResources.storageProfiles.length);
    expect(body.network_components).toHaveLength(defaultResources.networkComponents.length);
    expect(body.vm_assignments[0]).toMatchObject({
      vm_key: 'sample-app-01',
      vm_name: 'app-01',
      secondary_nics: [],
      excluded: false,
      exclusion_reason: null,
      override_profile_reason: null,
      storage_tier: '5iops-tier',
      override_storage_tier_reason: null,
      network: 'app-net',
      application: 'App tier',
    });
    expect(body.metadata.project_name).toBe('Migration assessment');
    expect(body.metadata.rvtools_filename).toBe('rvtools.xlsx');
  });

  it('exports and parses planning-state JSON', () => {
    const json = exportNetworkPlanJson({
      resources: defaultResources,
      assignmentRows: sampleRows,
      projectName: 'Migration assessment',
      summary: { filename: 'rvtools.xlsx' } as any,
    });
    const parsed = parseNetworkPlanJson(json);

    expect(parsed.vm_assignments).toHaveLength(3);
    expect(parsed.metadata.project_name).toBe('Migration assessment');
    expect(parsed.security_groups).toHaveLength(defaultResources.securityGroups.length);
  });

  it('rejects invalid planning-state JSON', () => {
    expect(() => parseNetworkPlanJson('not-json')).toThrow('valid JSON');
    expect(() => parseNetworkPlanJson('{}')).toThrow('missing VPC or subnet resources');
  });

  it('maps UI assignment names to persisted resource IDs', () => {
    const assignments = vmAssignmentsFromRows(
      [{ ...sampleRows[0], subnet: 'prod-app-us-south-1', securityGroup: 'sg-app-private', wave: 'Wave 1' }],
      defaultResources,
    );

    expect(assignments[0].primary_subnet_id).toBe('subnet-app');
    expect(assignments[0].primary_security_group_id).toBe('sg-app');
    expect(assignments[0].wave_id).toBe('wave-1');
  });

  it('hydrates resources and rows from a saved network plan', () => {
    const plan = {
      vpcs: defaultResources.vpcs,
      subnets: defaultResources.subnets,
      security_groups: defaultResources.securityGroups,
      storage_profiles: defaultResources.storageProfiles,
      waves: defaultResources.waves,
      network_components: defaultResources.networkComponents,
      vm_assignments: [
        {
          vm_key: 'sample-app-01',
      vm_name: 'app-01',
      primary_subnet_id: 'subnet-db',
      primary_security_group_id: 'sg-db',
      storage_profile_id: 'storage-db',
      wave_id: 'wave-2',
      excluded: true,
      exclusion_reason: 'Out of migration scope',
      override_profile: 'mx2-16x128',
      override_profile_reason: 'Database cache needs extra memory',
      storage_tier: '5iops-tier',
      override_storage_tier_reason: 'Database write latency target',
      owner: 'DB owner',
      application: 'Database',
      network: 'db-net',
    },
      ],
    };

    expect(resourcesFromNetworkPlan(plan).securityGroups).toHaveLength(2);
    expect(rowsFromNetworkPlan(plan, sampleRows)[0]).toMatchObject({
      subnet: 'prod-db-us-south-1',
      securityGroup: 'sg-db-private',
      overrideStorageTier: '10iops-tier',
      wave: 'Wave 2',
      excluded: true,
      exclusionReason: 'Out of migration scope',
      overrideProfile: 'mx2-16x128',
      overrideProfileReason: 'Database cache needs extra memory',
      overrideStorageTierReason: 'Database write latency target',
      owner: 'DB owner',
      application: 'Database',
      network: 'db-net',
    });
  });
});
