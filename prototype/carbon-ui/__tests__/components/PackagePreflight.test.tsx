import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PackagePreflight, {
  filterPreflightFindings,
  groupPreflightFindings,
} from '../../components/workflows/export/PackagePreflight';
import { sampleRows } from '../../store/AppContext';
import type { PreflightFinding, PreflightResponse } from '../../hooks/useApi';
import type { AssignmentSuggestion } from '../../utils/export-workflow';

function preflightFinding(overrides: Partial<PreflightFinding> = {}): PreflightFinding {
  return {
    Severity: 'blocker',
    Category: 'network_mapping',
    'Fix Category': 'Network Mapping',
    Subject: 'app-01',
    Message: 'VM has no subnet assigned.',
    Remediation: 'Assign a subnet before export.',
    'Fix Location': 'Network assignments',
    'Suggested Action': 'Assign subnet',
    'Valid Options': '',
    'Recommended Option': '',
    'Quick Fix Type': '',
    Field: 'subnet',
    'Current Value': '',
    Constraint: '',
    ...overrides,
  };
}

function renderPreflight(overrides: Partial<React.ComponentProps<typeof PackagePreflight>> = {}) {
  const summary: PreflightResponse['summary'] = {
    blockers: 1,
    warnings: 0,
    info: 0,
    total: 1,
  };
  const finding = preflightFinding();
  const suggestion: AssignmentSuggestion = {
    kind: 'subnet',
    row: sampleRows[0],
    value: 'prod-app-us-south-1',
    label: 'prod-app-us-south-1',
    reason: 'Best matching subnet from VM metadata.',
    confidence: 'High',
    score: 4,
    evidence: ['network: app', 'zone: us-south-1'],
  };
  const props: React.ComponentProps<typeof PackagePreflight> = {
    summary,
    findings: [finding],
    suggestionForFinding: jest.fn(() => suggestion),
    onApplySuggestion: jest.fn(),
    onOpenFinding: jest.fn(),
    ...overrides,
  };
  render(<PackagePreflight {...props} />);
  return { props, finding, suggestion };
}

describe('PackagePreflight', () => {
  it('filters findings by search text and severity', () => {
    const findings = [
      preflightFinding({
        Severity: 'blocker',
        Category: 'readiness',
        Subject: 'db-01',
        Message: 'Image readiness is blocked.',
      }),
      preflightFinding({
        Severity: 'warning',
        Category: 'storage_mapping',
        Subject: 'app-02',
        Message: 'Storage tier should be reviewed.',
      }),
    ];

    expect(filterPreflightFindings(findings, { search: 'image', severity: 'all' })).toHaveLength(1);
    expect(filterPreflightFindings(findings, { search: '', severity: 'warning' })).toEqual([
      expect.objectContaining({ Subject: 'app-02' }),
    ]);
    expect(filterPreflightFindings(findings, { search: 'storage', severity: 'blocker' })).toEqual([]);
  });

  it('groups findings by severity first and category second', () => {
    const groups = groupPreflightFindings([
      preflightFinding({
        Severity: 'warning',
        Category: 'storage_mapping',
        Subject: 'app-02',
      }),
      preflightFinding({
        Severity: 'info',
        Category: 'package',
        Subject: 'package',
      }),
      preflightFinding({
        Severity: 'blocker',
        Category: 'readiness',
        Subject: 'db-01',
      }),
      preflightFinding({
        Severity: 'blocker',
        Category: 'network_mapping',
        Subject: 'web-01',
      }),
    ]);

    expect(groups.map((group) => `${group.severity}:${group.category}:${group.findings.length}`)).toEqual([
      'blocker:network_mapping:1',
      'blocker:readiness:1',
      'warning:storage_mapping:1',
      'info:package:1',
    ]);
  });

  it('renders preflight summary, finding details, and suggested assignment actions', async () => {
    const { props, finding, suggestion } = renderPreflight();

    expect(screen.getByText('Package preflight')).toBeTruthy();
    expect(screen.getByText('1 backend finding(s) from the saved Carbon network plan.')).toBeTruthy();
    expect(screen.getByText('1 blocker(s)')).toBeTruthy();
    expect(screen.getByLabelText('Blockers network_mapping')).toBeTruthy();
    expect(screen.getByText('network_mapping')).toBeTruthy();
    expect(screen.getByText('1 finding(s)')).toBeTruthy();
    expect(screen.getByText('app-01')).toBeTruthy();
    expect(screen.getByText('VM has no subnet assigned.')).toBeTruthy();
    expect(screen.getByText('Suggested subnet: prod-app-us-south-1. Best matching subnet from VM metadata.')).toBeTruthy();
    expect(screen.getByText('High confidence')).toBeTruthy();
    expect(screen.getByText('network: app')).toBeTruthy();

    await userEvent.click(screen.getByText('Apply suggested subnet'));
    expect(props.onApplySuggestion).toHaveBeenCalledWith(suggestion);

    await userEvent.click(screen.getByText('Open network assignment'));
    expect(props.onOpenFinding).toHaveBeenCalledWith(
      finding,
      expect.objectContaining({ assignmentMode: 'network', workflow: 'assignment' }),
    );
  });

  it('renders grouped blocker and warning sections', () => {
    renderPreflight({
      summary: { blockers: 1, warnings: 1, info: 0, total: 2 },
      findings: [
        preflightFinding({
          Severity: 'warning',
          Category: 'storage_mapping',
          Subject: 'app-02',
          Message: 'Storage tier should be reviewed.',
        }),
        preflightFinding({
          Severity: 'blocker',
          Category: 'readiness',
          Subject: 'db-01',
          Message: 'Image readiness is blocked.',
        }),
      ],
      suggestionForFinding: jest.fn(() => null),
    });

    expect(screen.getByLabelText('Blockers readiness')).toBeTruthy();
    expect(screen.getByLabelText('Warnings storage_mapping')).toBeTruthy();
    expect(screen.getByText('Image readiness is blocked.')).toBeTruthy();
    expect(screen.getByText('Storage tier should be reviewed.')).toBeTruthy();
  });

  it('shows when additional findings are hidden and exposes an expand action', async () => {
    const onToggleFindings = jest.fn();
    renderPreflight({
      summary: { blockers: 6, warnings: 0, info: 0, total: 6 },
      findings: Array.from({ length: 6 }, (_, index) =>
        preflightFinding({ Subject: `app-0${index + 1}` }),
      ),
      showingAllFindings: false,
      onToggleFindings,
      suggestionForFinding: jest.fn(() => null),
    });

    expect(screen.getByText(/Showing top 5; 1 additional finding\(s\) are hidden\./)).toBeTruthy();
    await userEvent.click(screen.getByText('Show all findings'));

    expect(onToggleFindings).toHaveBeenCalledTimes(1);
  });

  it('can collapse the full finding list back to top findings', async () => {
    const onToggleFindings = jest.fn();
    renderPreflight({
      summary: { blockers: 6, warnings: 0, info: 0, total: 6 },
      findings: Array.from({ length: 6 }, (_, index) =>
        preflightFinding({ Subject: `app-0${index + 1}` }),
      ),
      showingAllFindings: true,
      onToggleFindings,
      suggestionForFinding: jest.fn(() => null),
    });

    expect(screen.getByText(/Showing all findings\./)).toBeTruthy();
    await userEvent.click(screen.getByText('Show top findings'));

    expect(onToggleFindings).toHaveBeenCalledTimes(1);
  });

  it('filters rendered findings by search and severity controls', async () => {
    renderPreflight({
      summary: { blockers: 1, warnings: 1, info: 0, total: 2 },
      findings: [
        preflightFinding({
          Severity: 'blocker',
          Category: 'readiness',
          Subject: 'db-01',
          Message: 'Image readiness is blocked.',
        }),
        preflightFinding({
          Severity: 'warning',
          Category: 'storage_mapping',
          Subject: 'app-02',
          Message: 'Storage tier should be reviewed.',
        }),
      ],
      suggestionForFinding: jest.fn(() => null),
    });

    await userEvent.type(screen.getByLabelText('Search findings'), 'storage');

    expect(screen.getByLabelText('Active preflight filters')).toBeTruthy();
    expect(screen.getByText('Search: storage')).toBeTruthy();
    expect(screen.getByText('Storage tier should be reviewed.')).toBeTruthy();
    expect(screen.queryByText('Image readiness is blocked.')).toBeNull();
    expect(screen.getByText(/1 matching finding\(s\)\./)).toBeTruthy();

    await userEvent.selectOptions(screen.getByLabelText('Severity'), 'blocker');

    expect(screen.getByText('Severity: Blockers')).toBeTruthy();
    expect(screen.getByText('No matches')).toBeTruthy();
    expect(screen.getByText('No package preflight findings match the current filter.')).toBeTruthy();
  });

  it('clears active search and severity filters', async () => {
    renderPreflight({
      summary: { blockers: 1, warnings: 1, info: 0, total: 2 },
      findings: [
        preflightFinding({
          Severity: 'blocker',
          Category: 'readiness',
          Subject: 'db-01',
          Message: 'Image readiness is blocked.',
        }),
        preflightFinding({
          Severity: 'warning',
          Category: 'storage_mapping',
          Subject: 'app-02',
          Message: 'Storage tier should be reviewed.',
        }),
      ],
      suggestionForFinding: jest.fn(() => null),
    });

    await userEvent.type(screen.getByLabelText('Search findings'), 'storage');
    await userEvent.selectOptions(screen.getByLabelText('Severity'), 'blocker');
    expect(screen.getByText('No matches')).toBeTruthy();

    await userEvent.click(screen.getByText('Clear filters'));

    expect(screen.queryByLabelText('Active preflight filters')).toBeNull();
    expect((screen.getByLabelText('Search findings') as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText('Severity') as HTMLSelectElement).value).toBe('all');
    expect(screen.getByText('Image readiness is blocked.')).toBeTruthy();
    expect(screen.getByText('Storage tier should be reviewed.')).toBeTruthy();
  });

  it('shows a ready state when preflight returns no visible findings', () => {
    renderPreflight({
      summary: { blockers: 0, warnings: 0, info: 0, total: 0 },
      findings: [],
      suggestionForFinding: jest.fn(() => null),
    });

    expect(screen.getByText('Ready')).toBeTruthy();
    expect(screen.getByText('No package preflight findings returned.')).toBeTruthy();
    expect(screen.getByText('0 blocker(s)')).toBeTruthy();
  });
});
