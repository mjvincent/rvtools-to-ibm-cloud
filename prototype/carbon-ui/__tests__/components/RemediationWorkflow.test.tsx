import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import RemediationWorkflow, { buildRemediationBacklog } from '../../components/workflows/RemediationWorkflow';
import { AppProvider } from '../../store/AppContext';
import type { AssignmentVm } from '../../types/network-planning';

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

const baseRow: AssignmentVm = {
  id: 'vm-1',
  name: 'app-01',
  image: 'Ready',
  imageReasons: '',
  migration: 'Blocked',
  migrationReasons: 'Resolve source migration finding',
  memory: 'Review',
  memoryReasons: 'Validate memory pressure',
  networkReadiness: 'Ready',
  networkReasons: '',
  profile: 'bx2-2x8',
  overrideProfile: '',
  storageTier: '5iops-tier',
  overrideStorageTier: '',
  network: 'app-net',
  subnet: '',
  securityGroup: '',
  power: 'poweredOn',
  owner: 'Migration owner',
  application: 'App',
  wave: '',
  cutoverGroup: '',
  priority: '',
  dependencyGroup: '',
};

describe('RemediationWorkflow', () => {
  it('builds backlog rows from blocked and review readiness signals', () => {
    const backlog = buildRemediationBacklog([baseRow], {});

    expect(backlog).toHaveLength(2);
    expect(backlog.map((item) => item.blockerType)).toEqual(['Migration', 'Memory']);
    expect(backlog[0]).toMatchObject({
      blockerId: 'vm-1::migration',
      owner: 'Migration owner',
      status: 'Open',
    });
  });

  it('renders remediation rows and allows status edits', () => {
    renderWithProvider(<RemediationWorkflow />);

    expect(screen.getByText('Remediation Backlog')).toBeTruthy();
    expect(screen.getByText('Resolve source migration finding')).toBeTruthy();

    const statusControls = screen.getAllByLabelText('Status');
    fireEvent.change(statusControls[0], { target: { value: 'In Progress' } });

    expect((statusControls[0] as HTMLSelectElement).value).toBe('In Progress');
  });

  it('offers CSV export when backlog items exist', () => {
    renderWithProvider(<RemediationWorkflow />);

    const exportButton = screen.getByText('Export remediation CSV');
    expect(exportButton).toBeTruthy();
    expect(exportButton.closest('button') || exportButton.closest('a')).toBeTruthy();
  });
});
