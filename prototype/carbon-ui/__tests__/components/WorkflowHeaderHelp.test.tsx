import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WorkflowHeaderHelp from '../../components/ui/WorkflowHeaderHelp';

describe('WorkflowHeaderHelp', () => {
  const openSpy = jest.fn();

  beforeEach(() => {
    jest.spyOn(window, 'open').mockImplementation(openSpy);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    openSpy.mockReset();
  });

  it('opens workflow-specific step guidance from an inline header button', async () => {
    const user = userEvent.setup();
    render(<WorkflowHeaderHelp workflow="migrationOps" />);

    await user.click(screen.getByRole('button', { name: 'Step help for Migration Ops' }));

    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(screen.getByText('Migration Ops step help')).toBeTruthy();
    expect(screen.getByText('Before continuing')).toBeTruthy();
    expect(screen.getByText('Complete when')).toBeTruthy();
    expect(screen.getByText('Common mistakes')).toBeTruthy();
    expect(screen.getByText('Recommended next step')).toBeTruthy();
  });

  it('opens the full user guide from the inline help modal', async () => {
    const user = userEvent.setup();
    render(<WorkflowHeaderHelp workflow="export" />);

    await user.click(screen.getByRole('button', { name: 'Step help for Export Readiness' }));
    await user.click(screen.getByRole('button', { name: 'Open full user guide in a new window' }));

    expect(openSpy).toHaveBeenCalledWith('/help/user-guide', '_blank', 'noopener,noreferrer');
  });
});
