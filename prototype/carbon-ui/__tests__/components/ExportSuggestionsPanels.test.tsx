import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AssignmentSuggestionsPanel from '../../components/workflows/export/AssignmentSuggestionsPanel';
import RemediationQueuePanel from '../../components/workflows/export/RemediationQueuePanel';
import SuggestionAuditPanel from '../../components/workflows/export/SuggestionAuditPanel';
import { sampleRows } from '../../store/AppContext';
import type { SuggestionAuditEntry } from '../../types/network-planning';
import {
  suggestionKey,
  type AssignmentSuggestion,
  type RemediationQueueItem,
} from '../../utils/export-workflow';

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

const remediationItem: RemediationQueueItem = {
  id: 'vm-gap-app-01-network',
  source: 'vm-gap',
  severity: 'blocker',
  title: 'Missing network assignment',
  subject: 'app-01',
  detail: 'Assign a subnet before export.',
  tag: 'Network',
  tagType: 'red',
  row: sampleRows[0],
  mode: 'network',
};

describe('RemediationQueuePanel', () => {
  it('renders queue actions and routes suggestion callbacks', async () => {
    const props: React.ComponentProps<typeof RemediationQueuePanel> = {
      remediationQueue: [remediationItem],
      uniqueSuggestionCount: 1,
      selectedSuggestionCount: 1,
      highConfidenceSuggestionCount: 1,
      selectedSuggestionIds: [suggestionKey(suggestion)],
      suggestionForItem: jest.fn(() => suggestion),
      onSelectHighConfidence: jest.fn(),
      onClearSelection: jest.fn(),
      onApplySelected: jest.fn(),
      onToggleSuggestion: jest.fn(),
      onApplySuggestion: jest.fn(),
      onReviewIssue: jest.fn(),
    };

    render(<RemediationQueuePanel {...props} />);

    expect(screen.getByText('Remediation queue')).toBeTruthy();
    expect(screen.getByText('1 issue(s) sorted by export priority.')).toBeTruthy();
    expect(screen.getByText('Missing network assignment')).toBeTruthy();
    expect(screen.getByText('Suggested subnet: prod-app-us-south-1')).toBeTruthy();
    expect(screen.getByText('High confidence')).toBeTruthy();

    await userEvent.click(screen.getByText('Select high confidence'));
    expect(props.onSelectHighConfidence).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Clear selection'));
    expect(props.onClearSelection).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Apply selected fixes'));
    expect(props.onApplySelected).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Apply fix'));
    expect(props.onApplySuggestion).toHaveBeenCalledWith(suggestion);

    await userEvent.click(screen.getByText('Review issue'));
    expect(props.onReviewIssue).toHaveBeenCalledWith(remediationItem);
  });

  it('shows the ready state when the queue is clear', () => {
    render(
      <RemediationQueuePanel
        remediationQueue={[]}
        uniqueSuggestionCount={0}
        selectedSuggestionCount={0}
        highConfidenceSuggestionCount={0}
        selectedSuggestionIds={[]}
        suggestionForItem={jest.fn(() => null)}
        onSelectHighConfidence={jest.fn()}
        onClearSelection={jest.fn()}
        onApplySelected={jest.fn()}
        onToggleSuggestion={jest.fn()}
        onApplySuggestion={jest.fn()}
        onReviewIssue={jest.fn()}
      />,
    );

    expect(screen.getByText('Ready')).toBeTruthy();
    expect(screen.getByText('All tracked export readiness items are clear.')).toBeTruthy();
  });
});

describe('AssignmentSuggestionsPanel', () => {
  it('renders assignment suggestions and applies high-confidence or single suggestions', async () => {
    const props: React.ComponentProps<typeof AssignmentSuggestionsPanel> = {
      suggestions: [suggestion],
      auditedCount: 2,
      highConfidenceCount: 1,
      onApplyHighConfidence: jest.fn(),
      onApplySuggestion: jest.fn(),
    };

    render(<AssignmentSuggestionsPanel {...props} />);

    expect(screen.getByText('Suggested assignment fixes')).toBeTruthy();
    expect(screen.getByText('2 audited')).toBeTruthy();
    expect(screen.getByText('1 suggestion(s)')).toBeTruthy();
    expect(screen.getByText('prod-app-us-south-1')).toBeTruthy();
    expect(screen.getByText('Best matching subnet from VM metadata.')).toBeTruthy();

    await userEvent.click(screen.getByText('Apply high-confidence suggestions'));
    expect(props.onApplyHighConfidence).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Apply suggestion'));
    expect(props.onApplySuggestion).toHaveBeenCalledWith(suggestion);
  });
});

describe('SuggestionAuditPanel', () => {
  it('renders suggestion audit entries and routes undo actions', async () => {
    const entry: SuggestionAuditEntry = {
      id: 'audit-app-01-subnet',
      vmId: sampleRows[0].id,
      vmName: sampleRows[0].name,
      field: 'subnet',
      oldValue: '',
      newValue: 'prod-app-us-south-1',
      confidence: 'High',
      reason: 'Applied from remediation queue.',
      evidence: ['network: app'],
      appliedAt: '2026-07-15T12:00:00.000Z',
    };
    const onRevertSuggestion = jest.fn();

    render(
      <SuggestionAuditPanel
        entries={[entry]}
        totalCount={1}
        activeCount={1}
        onRevertSuggestion={onRevertSuggestion}
      />,
    );

    expect(screen.getByText('Suggestion audit')).toBeTruthy();
    expect(screen.getByText('1 total')).toBeTruthy();
    expect(screen.getByText('1 active')).toBeTruthy();
    expect(screen.getByText(`${sampleRows[0].name}`)).toBeTruthy();
    expect(screen.getByText('(blank) to prod-app-us-south-1')).toBeTruthy();

    await userEvent.click(screen.getByText('Undo suggestion'));
    expect(onRevertSuggestion).toHaveBeenCalledWith('audit-app-01-subnet');
  });
});
