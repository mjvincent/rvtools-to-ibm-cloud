import { sampleRows } from '../store/AppContext';
import {
  buildAuditId,
  confidenceFromScore,
  packageGroups,
  packageParitySummary,
  planningGapLabel,
  rowAssignmentValue,
  sharedTokenCount,
  suggestionKey,
  suggestionKindForMode,
  suggestionLabels,
  terraformLabel,
  tokenize,
  type AssignmentSuggestion,
} from '../utils/export-workflow';

describe('export workflow helpers', () => {
  it('normalizes Terraform labels consistently', () => {
    expect(terraformLabel('Prod App US-South 1')).toBe('prod_app_us_south_1');
    expect(terraformLabel('  !!  ')).toBe('new_resource');
  });

  it('tokenizes VM and planning text for assignment matching', () => {
    expect(Array.from(tokenize('Payments-App-01 prod_net'))).toEqual([
      'payments',
      'app',
      'prod',
      'net',
    ]);
  });

  it('scores shared VM planning tokens', () => {
    const target = {
      ...sampleRows[0],
      name: 'payments-app-01',
      application: 'Payments',
      network: 'prod-app',
      owner: 'Payments team',
    };
    const candidate = {
      ...sampleRows[1],
      name: 'payments-db-01',
      application: 'Payments',
      network: 'prod-db',
      owner: 'Payments team',
    };

    expect(sharedTokenCount(target, candidate)).toBeGreaterThanOrEqual(2);
  });

  it('maps assignment modes and labels for remediation guidance', () => {
    expect(suggestionKindForMode('network')).toBe('subnet');
    expect(suggestionKindForMode('security')).toBe('securityGroup');
    expect(suggestionKindForMode('storage')).toBe('storage');
    expect(suggestionKindForMode('wave')).toBe('wave');
    expect(planningGapLabel('security')).toBe('security group');
    expect(suggestionLabels.storage).toBe('storage/IOPS');
  });

  it('returns display values and confidence tags for assignment suggestions', () => {
    const row = {
      ...sampleRows[0],
      subnet: 'prod-app-us-south-1',
      securityGroup: 'sg-app-private',
      storageTier: '5iops-tier',
      overrideStorageTier: '10iops-tier',
      wave: 'Wave 1',
    };

    expect(rowAssignmentValue(row, 'subnet')).toBe('prod-app-us-south-1');
    expect(rowAssignmentValue(row, 'securityGroup')).toBe('sg-app-private');
    expect(rowAssignmentValue(row, 'storage')).toBe('10iops-tier');
    expect(rowAssignmentValue(row, 'wave')).toBe('Wave 1');
    expect(confidenceFromScore(7)).toBe('High');
    expect(confidenceFromScore(3)).toBe('Medium');
    expect(confidenceFromScore(1)).toBe('Low');
  });

  it('builds stable suggestion keys and audit ids', () => {
    const suggestion: AssignmentSuggestion = {
      kind: 'subnet',
      row: sampleRows[0],
      value: 'prod-app-us-south-1',
      label: 'prod-app-us-south-1',
      reason: 'Matched source network',
      confidence: 'High',
      score: 8,
      evidence: ['Same source network'],
    };

    jest.spyOn(Date, 'now').mockReturnValue(12345);

    expect(suggestionKey(suggestion)).toBe('sample-app-01:subnet:prod-app-us-south-1');
    expect(buildAuditId(sampleRows[0], 'subnet', 'prod-app-us-south-1')).toBe(
      'sample-app-01-subnet-prod-app-us-south-1-12345',
    );
  });

  it('keeps package parity metadata aligned with inventory groups', () => {
    expect(packageParitySummary.map((item) => item.label)).toEqual([
      'Handoff parity',
      'Terraform layout',
      'Carbon additions',
    ]);
    expect(packageGroups.map((item) => item.title)).toEqual([
      'Terraform project',
      'Migration handoff',
      'Carbon state',
    ]);
  });
});
