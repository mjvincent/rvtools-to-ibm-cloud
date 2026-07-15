import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PackagePreflight from '../../components/workflows/export/PackagePreflight';
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
  it('renders preflight summary, finding details, and suggested assignment actions', async () => {
    const { props, finding, suggestion } = renderPreflight();

    expect(screen.getByText('Package preflight')).toBeTruthy();
    expect(screen.getByText('1 backend finding(s) from the saved Carbon network plan.')).toBeTruthy();
    expect(screen.getByText('1 blocker(s)')).toBeTruthy();
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
