import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GuidedHelp from '../../components/ui/GuidedHelp';

describe('GuidedHelp', () => {
  const openSpy = jest.fn();

  beforeEach(() => {
    jest.spyOn(window, 'open').mockImplementation(openSpy);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    openSpy.mockReset();
  });

  it('opens workflow-specific guidance from the help button', async () => {
    const user = userEvent.setup();
    render(<GuidedHelp workflow="network" label="Network Plan" />);

    await user.click(screen.getByRole('button', { name: 'Help for Network Plan' }));

    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(screen.getByText('Network Plan help')).toBeTruthy();
    expect(screen.getByText('Before continuing')).toBeTruthy();
    expect(screen.getByText('Complete when')).toBeTruthy();
    expect(screen.getByText('Common mistakes')).toBeTruthy();
    expect(screen.getByText('Recommended next step')).toBeTruthy();
    expect(screen.getByText('Check the Network validation panel.')).toBeTruthy();
  });

  it('opens the full user guide in a separate window', async () => {
    const user = userEvent.setup();
    render(<GuidedHelp workflow="export" label="Export Readiness" />);

    await user.click(screen.getByRole('button', { name: 'Open user guide' }));

    expect(openSpy).toHaveBeenCalledWith('/help/user-guide', '_blank', 'noopener,noreferrer');
  });

  it('offers the user guide from inside the workflow help modal', async () => {
    const user = userEvent.setup();
    render(<GuidedHelp workflow="export" label="Export Readiness" />);

    await user.click(screen.getByRole('button', { name: 'Help for Export Readiness' }));
    await user.click(screen.getByRole('button', { name: 'Open full user guide in a new window' }));

    expect(openSpy).toHaveBeenCalledWith('/help/user-guide', '_blank', 'noopener,noreferrer');
  });
});
