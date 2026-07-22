import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WorkflowCompletionChecklist from '../../components/ui/WorkflowCompletionChecklist';

describe('WorkflowCompletionChecklist', () => {
  it('renders complete-when guidance for the selected workflow', () => {
    render(<WorkflowCompletionChecklist workflow="assignment" />);

    expect(screen.getByText('Complete when')).toBeTruthy();
    expect(screen.getByText('2 items')).toBeTruthy();
    expect(screen.getByText('In-scope VMs have subnet and security group assignments.')).toBeTruthy();
    expect(screen.getByText('Storage and wave placement are reviewed or intentionally deferred.')).toBeTruthy();
  });

  it('can collapse and expand the checklist details', async () => {
    const user = userEvent.setup();
    const { container } = render(<WorkflowCompletionChecklist workflow="export" />);
    const details = container.querySelector('details') as HTMLDetailsElement;

    expect(details.open).toBe(true);

    await user.click(screen.getByText('Complete when'));
    expect(details.open).toBe(false);

    await user.click(screen.getByText('Complete when'));
    expect(details.open).toBe(true);
  });
});
