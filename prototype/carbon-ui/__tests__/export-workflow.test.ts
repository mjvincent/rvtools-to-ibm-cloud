import { sampleRows } from '../store/AppContext';
import {
  buildAuditId,
  buildRemediationQueue,
  confidenceFromScore,
  packageGroups,
  packageParitySummary,
  planningGapLabel,
  primaryRouteForFinding,
  rowAssignmentValue,
  routesForFinding,
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

  it('routes preflight findings to the right Carbon workflow', () => {
    const imageRoute = primaryRouteForFinding({
      Severity: 'blocker',
      Category: 'custom_image',
      'Fix Category': 'Fix image planning',
      Subject: 'app-01',
      Message: 'Image placeholder is missing.',
      Remediation: 'Import image and set target ID.',
      'Fix Location': 'Image Import Planning',
      'Suggested Action': 'Set target custom image ID.',
      'Valid Options': '',
      'Recommended Option': '',
      'Quick Fix Type': 'image_placeholder',
      Field: 'Image',
      'Current Value': '',
      Constraint: '',
    });
    const networkRoute = primaryRouteForFinding({
      Severity: 'warning',
      Category: 'network_mapping',
      'Fix Category': 'Fix app planning',
      Subject: 'app-02',
      Message: 'VM subnet mapping is blank.',
      Remediation: 'Select a target subnet.',
      'Fix Location': 'VM Assignment',
      'Suggested Action': '',
      'Valid Options': '',
      'Recommended Option': '',
      'Quick Fix Type': '',
      Field: 'Subnet',
      'Current Value': '',
      Constraint: '',
    });

    expect(imageRoute).toMatchObject({
      workflow: 'imageImport',
      label: 'Open image planning',
    });
    expect(imageRoute.status).toContain('Set target custom image ID.');
    expect(networkRoute).toMatchObject({
      workflow: 'assignment',
      assignmentMode: 'network',
      label: 'Open network assignment',
    });
  });

  it('adds scope review as a secondary route when needed', () => {
    const routes = routesForFinding({
      Severity: 'blocker',
      Category: 'readiness',
      'Fix Category': 'Fix source data',
      Subject: 'db-01',
      Message: 'Migration readiness is blocked.',
      Remediation: 'Review migration readiness.',
      'Fix Location': 'Readiness tab',
      'Suggested Action': '',
      'Valid Options': '',
      'Recommended Option': '',
      'Quick Fix Type': 'exclude_vm',
      Field: 'Migration Readiness',
      'Current Value': 'Blocked',
      Constraint: '',
    });

    expect(routes.map((route) => route.label)).toEqual([
      'Open remediation',
      'Review scope decision',
    ]);
  });

  it('builds remediation queue entries from preflight and planning gaps', () => {
    const queue = buildRemediationQueue({
      preflightFindings: [
        {
          Severity: 'blocker',
          Category: 'network_mapping',
          'Fix Category': 'Fix app planning',
          Subject: 'app-02',
          Message: 'VM subnet mapping is blank.',
          Remediation: 'Select a target subnet.',
          'Fix Location': 'VM Assignment',
          'Suggested Action': '',
          'Valid Options': '',
          'Recommended Option': '',
          'Quick Fix Type': '',
          Field: 'Subnet',
          'Current Value': '',
          Constraint: '',
        },
        {
          Severity: 'warning',
          Category: 'security_group',
          'Fix Category': 'Fix app planning',
          Subject: 'app-01',
          Message: 'Security group should be reviewed.',
          Remediation: 'Review security group assignment.',
          'Fix Location': 'Security Plan',
          'Suggested Action': '',
          'Valid Options': '',
          'Recommended Option': '',
          'Quick Fix Type': '',
          Field: 'Security Group',
          'Current Value': '',
          Constraint: '',
        },
      ],
      assignmentRows: [
        { ...sampleRows[0], subnet: '', securityGroup: '', wave: '' },
        { ...sampleRows[1], subnet: 'prod-db-us-south-1', securityGroup: 'sg-db-private', wave: 'Wave 1' },
      ],
      planningCompleteness: {
        missingSubnet: 1,
        missingSg: 1,
        missingStorage: 0,
        missingWave: 1,
        missingCidr: 1,
        invalidLabels: 1,
      },
    });

    expect(queue[0]).toMatchObject({
      id: 'preflight-blocker-network_mapping-app-02-0',
      source: 'preflight',
      severity: 'blocker',
    });
    expect(queue.map((item) => item.id)).toEqual([
      'preflight-blocker-network_mapping-app-02-0',
      'missing-subnet-sample-app-01',
      'missing-security-sample-app-01',
      'missing-wave-sample-app-01',
      'missing-subnet-cidrs',
      'invalid-terraform-labels',
      'preflight-warning-security_group-app-01-0',
    ]);
  });
});
