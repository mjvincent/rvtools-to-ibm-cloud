import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WorkflowProgressGuide from '../../components/ui/WorkflowProgressGuide';
import type { WorkflowProgressStep } from '../../utils/workflow-progress';

const steps: WorkflowProgressStep[] = [
  {
    workflow: 'intake',
    label: 'Load workbook',
    status: 'Complete',
    reason: 'Workbook loaded.',
    nextAction: 'Review the estate summary and VM rows.',
  },
  {
    workflow: 'assignment',
    label: 'Place VMs',
    status: 'Needs attention',
    reason: 'Two VMs are missing placement.',
    nextAction: 'Assign missing subnet and security group values.',
  },
  {
    workflow: 'export',
    label: 'Build package',
    status: 'Ready',
    reason: 'Planning state is ready for package preflight.',
    nextAction: 'Run preflight, preview Terraform, then download the ZIP.',
  },
];

describe('WorkflowProgressGuide', () => {
  it('shows workflow statuses and the next recommended action', () => {
    render(<WorkflowProgressGuide steps={steps} activeWorkflow="intake" onSelectWorkflow={jest.fn()} />);

    expect(screen.getByText('Progress guide')).toBeTruthy();
    expect(screen.getByText('Next recommended action')).toBeTruthy();
    expect(screen.getByText('Assign missing subnet and security group values.')).toBeTruthy();
    expect(screen.getByText('Load workbook')).toBeTruthy();
    expect(screen.getByText('Place VMs')).toBeTruthy();
    expect(screen.getByText('Build package')).toBeTruthy();
    expect(screen.getByText('Needs attention')).toBeTruthy();
  });

  it('routes users to a selected workflow', async () => {
    const user = userEvent.setup();
    const onSelectWorkflow = jest.fn();
    render(<WorkflowProgressGuide steps={steps} activeWorkflow="intake" onSelectWorkflow={onSelectWorkflow} />);

    await user.click(screen.getByRole('button', { name: 'Open Place VMs' }));
    expect(onSelectWorkflow).toHaveBeenCalledWith('assignment');

    await user.click(screen.getByRole('button', { name: 'Build package' }));
    expect(onSelectWorkflow).toHaveBeenCalledWith('export');
  });
});
