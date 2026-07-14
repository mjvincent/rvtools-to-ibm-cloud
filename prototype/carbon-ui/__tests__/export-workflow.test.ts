import { defaultResources, sampleRows } from '../store/AppContext';
import {
  applySuggestionsToRows,
  buildAuditId,
  buildAssignmentSuggestions,
  buildExportChecklist,
  buildRemediationQueue,
  calculatePlanningCompleteness,
  confidenceFromScore,
  filterPreviewFiles,
  handoffCsvFileCount,
  inferAssignmentSuggestion,
  markSuggestionAuditReverted,
  packageGroups,
  packageParitySummary,
  planningGapLabel,
  planningFindings,
  previewCategories,
  previewFileSizeLabel,
  primaryRouteForFinding,
  readinessReportPayload,
  revertSuggestionInRows,
  rowAssignmentValue,
  routesForFinding,
  sharedTokenCount,
  suggestionAuditEntries,
  suggestionForFinding,
  suggestionForQueueItem,
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

  it('builds planning completeness, findings, and checklist rows', () => {
    const resources = {
      ...defaultResources,
      subnets: [{ ...defaultResources.subnets[0], cidr: '' }],
      securityGroups: [{ ...defaultResources.securityGroups[0], label: 'Bad Label' }],
    };
    const completeness = calculatePlanningCompleteness({
      assignmentRows: [
        { ...sampleRows[0], subnet: '', securityGroup: '', storageTier: '', overrideStorageTier: '', wave: '' },
        { ...sampleRows[1], subnet: 'prod-db-us-south-1', securityGroup: 'sg-db-private', storageTier: '10iops-tier', wave: 'Wave 1' },
      ],
      resources,
    });
    const checklist = buildExportChecklist({
      selectedProjectId: 'project-1',
      isDirty: false,
      planningCompleteness: completeness,
      hasPreflight: true,
    });

    expect(completeness).toMatchObject({
      missingSubnet: 1,
      missingSg: 1,
      missingStorage: 1,
      missingWave: 1,
      missingCidr: 1,
      invalidLabels: 1,
    });
    expect(planningFindings(completeness)).toContainEqual(['Subnets missing CIDR', 1]);
    expect(checklist).toContainEqual({ label: 'Network plan saved', complete: true });
    expect(checklist).toContainEqual({ label: 'VM assignments complete', complete: false });
    expect(checklist).toContainEqual({ label: 'Backend preflight run', complete: true });
  });

  it('filters preview files and formats preview metadata', () => {
    const files = [
      { path: 'README.md', category: 'Terraform', size_bytes: 1200, content: '' },
      { path: 'decision-audit.csv', category: 'Migration handoff', size_bytes: 48, content: '' },
      { path: 'network-plan.json', category: 'Carbon state', size_bytes: 24, content: '' },
    ];

    expect(previewCategories(files)).toEqual(['All', 'Terraform', 'Migration handoff', 'Carbon state']);
    expect(filterPreviewFiles({ files, category: 'Migration handoff', search: 'audit' })).toEqual([files[1]]);
    expect(previewFileSizeLabel(files[0])).toBe('2 KB');
    expect(previewFileSizeLabel()).toBe('');
    expect(handoffCsvFileCount(files)).toBe(1);
  });

  it('builds a readiness report payload with suggestions and package inventory', () => {
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
    const report = readinessReportPayload({
      generatedAt: '2026-07-14T12:00:00Z',
      selectedProjectId: 'project-1',
      projectName: 'Export Project',
      workbookFilename: 'rvtools.xlsx',
      activeAssignmentGapCount: 0,
      preflight: {
        project_id: 'project-1',
        project_name: 'Export Project',
        summary: { blockers: 0, warnings: 0, info: 0, total: 0 },
        findings: [],
      },
      exportChecklist: [{ label: 'Network plan saved', complete: true }],
      findings: [['Missing subnet assignments', 0]],
      assignmentSuggestions: [suggestion],
      suggestionAudit: [],
    });

    expect(report).toMatchObject({
      schema_version: 'carbon-export-readiness-report-1.0',
      generated_at: '2026-07-14T12:00:00Z',
      project: { id: 'project-1', name: 'Export Project', workbook: 'rvtools.xlsx' },
      readiness: { status: 'Ready' },
    });
    expect(report.suggestions.available[0]).toMatchObject({
      vm_id: sampleRows[0].id,
      field: 'subnet',
      suggested_value: 'prod-app-us-south-1',
    });
    expect(report.package_inventory.total_files).toBeGreaterThan(0);
    expect(report.package_inventory.handoff_files).toBeGreaterThan(0);
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

  it('infers assignment suggestions from matching existing VM assignments', () => {
    const rows = [
      {
        ...sampleRows[0],
        id: 'payments-app-01',
        name: 'payments-app-01',
        application: 'Payments',
        network: 'payments-net',
        subnet: 'prod-app-us-south-1',
      },
      {
        ...sampleRows[1],
        id: 'payments-app-02',
        name: 'payments-app-02',
        application: 'Payments',
        network: 'payments-net',
        subnet: '',
      },
    ];

    const suggestion = inferAssignmentSuggestion({
      row: rows[1],
      kind: 'subnet',
      assignmentRows: rows,
      resources: { ...defaultResources, subnets: [] },
    });

    expect(suggestion).toMatchObject({
      kind: 'subnet',
      value: 'prod-app-us-south-1',
      confidence: 'High',
    });
    expect(suggestion?.evidence).toContain('Same application: Payments');
    expect(suggestion?.evidence).toContain('Same source network: payments-net');
  });

  it('infers assignment suggestions from resource names when no VM match exists', () => {
    const row = {
      ...sampleRows[0],
      id: 'web-01',
      name: 'web-01',
      application: 'Web',
      network: 'web-net',
      subnet: '',
      securityGroup: '',
    };

    const subnetSuggestion = inferAssignmentSuggestion({
      row,
      kind: 'subnet',
      assignmentRows: [row],
      resources: {
        ...defaultResources,
        subnets: [{
          ...defaultResources.subnets[0],
          name: 'prod-web-us-south-1',
          purpose: 'Web',
        }],
      },
    });
    const securitySuggestion = inferAssignmentSuggestion({
      row,
      kind: 'securityGroup',
      assignmentRows: [row],
      resources: {
        ...defaultResources,
        securityGroups: [{
          ...defaultResources.securityGroups[0],
          name: 'sg-web-private',
          purpose: 'Web',
        }],
      },
    });

    expect(subnetSuggestion).toMatchObject({
      kind: 'subnet',
      value: 'prod-web-us-south-1',
    });
    expect(securitySuggestion).toMatchObject({
      kind: 'securityGroup',
      value: 'sg-web-private',
    });
  });

  it('builds, applies, audits, and reverts assignment suggestions', () => {
    jest.spyOn(Date, 'now').mockReturnValue(111);
    const rows = [
      { ...sampleRows[0], id: 'app-01', name: 'app-01', subnet: 'prod-app-us-south-1', wave: 'Wave 1' },
      { ...sampleRows[1], id: 'app-02', name: 'app-02', subnet: '', wave: '' },
    ];
    const suggestions = buildAssignmentSuggestions({
      assignmentRows: rows,
      resources: defaultResources,
      limit: 10,
    });
    const subnetSuggestion = suggestions.find((suggestion) =>
      suggestion.row.id === 'app-02' && suggestion.kind === 'subnet',
    );

    expect(subnetSuggestion).toBeTruthy();
    const appliedRows = applySuggestionsToRows(rows, [subnetSuggestion!]);
    expect(appliedRows[1].subnet).toBe('prod-app-us-south-1');

    const audit = suggestionAuditEntries([subnetSuggestion!], '2026-07-14T12:00:00Z');
    expect(audit[0]).toMatchObject({
      id: 'app-02-subnet-prod-app-us-south-1-111',
      vmId: 'app-02',
      oldValue: '',
      newValue: 'prod-app-us-south-1',
      appliedAt: '2026-07-14T12:00:00Z',
    });

    const revertedRows = revertSuggestionInRows(appliedRows, audit[0]);
    expect(revertedRows[1].subnet).toBe('');
    expect(markSuggestionAuditReverted(audit, audit[0].id, '2026-07-14T12:05:00Z')[0].revertedAt).toBe(
      '2026-07-14T12:05:00Z',
    );
  });

  it('maps preflight and queue items to assignment suggestions', () => {
    const rows = [
      { ...sampleRows[0], id: 'app-01', name: 'app-01', securityGroup: 'sg-app-private' },
      { ...sampleRows[1], id: 'app-02', name: 'app-02', securityGroup: '' },
    ];
    const finding = {
      Severity: 'warning',
      Category: 'security_group',
      'Fix Category': 'Fix app planning',
      Subject: 'app-02',
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
    };
    const preflightSuggestion = suggestionForFinding({
      finding,
      assignmentRows: rows,
      resources: defaultResources,
    });
    const queueSuggestion = suggestionForQueueItem({
      item: {
        id: 'preflight-warning-security_group-app-02-0',
        source: 'preflight',
        severity: 'warning',
        title: 'Preflight warning',
        subject: 'app-02',
        detail: 'Security group should be reviewed.',
        tag: 'security group',
        tagType: 'warm-gray',
        route: primaryRouteForFinding(finding),
        finding,
      },
      assignmentRows: rows,
      resources: defaultResources,
    });

    expect(preflightSuggestion).toMatchObject({
      kind: 'securityGroup',
      value: 'sg-app-private',
    });
    expect(queueSuggestion).toMatchObject({
      kind: 'securityGroup',
      value: 'sg-app-private',
    });
  });
});
