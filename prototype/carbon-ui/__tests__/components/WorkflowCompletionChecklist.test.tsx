import React from 'react';
import { render, screen } from '@testing-library/react';
import WorkflowCompletionChecklist from '../../components/ui/WorkflowCompletionChecklist';

describe('WorkflowCompletionChecklist', () => {
  it('renders complete-when guidance for the selected workflow', () => {
    render(<WorkflowCompletionChecklist workflow="assignment" />);

    expect(screen.getByRole('heading', { name: 'Complete when' })).toBeTruthy();
    expect(screen.getByText('In-scope VMs have subnet and security group assignments.')).toBeTruthy();
    expect(screen.getByText('Storage and wave placement are reviewed or intentionally deferred.')).toBeTruthy();
  });
});
