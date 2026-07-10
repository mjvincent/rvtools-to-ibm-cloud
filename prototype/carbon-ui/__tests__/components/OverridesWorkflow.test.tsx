import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OverridesWorkflow, {
  buildProfileOptions,
  buildDecisionAuditRows,
  decisionAuditCsv,
  profileSizeLabel,
  summarizeOverrides,
} from '../../components/workflows/OverridesWorkflow';
import { AppProvider } from '../../store/AppContext';
import type { AssignmentVm } from '../../types/network-planning';

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

const overrideVm: AssignmentVm = {
  id: 'vm-1',
  name: 'db-01',
  image: 'Ready',
  imageReasons: '',
  migration: 'Ready',
  migrationReasons: '',
  memory: 'Ready',
  memoryReasons: '',
  networkReadiness: 'Ready',
  networkReasons: '',
  profile: 'bx2-4x16',
  overrideProfile: 'mx2-16x128',
  overrideProfileReason: 'Database cache needs extra memory',
  storageTier: '3iops-tier',
  overrideStorageTier: '10iops-tier',
  overrideStorageTierReason: 'Production database write latency target',
  network: 'db-net',
  subnet: 'prod-db-us-south-1',
  securityGroup: 'sg-db-private',
  power: 'poweredOn',
  owner: 'DB owner',
  application: 'Database',
  wave: 'Wave 2',
  cutoverGroup: 'CG-B',
  priority: 'high',
  dependencyGroup: '',
  excluded: true,
  exclusionReason: 'Retired before migration',
};

describe('OverridesWorkflow', () => {
  it('builds Streamlit-compatible decision audit rows', () => {
    expect(buildDecisionAuditRows([overrideVm])[0]).toMatchObject({
      'VM Key': 'vm-1',
      'Original Profile': 'bx2-4x16',
      'Chosen Profile': 'mx2-16x128',
      'Profile Override Reason': 'Database cache needs extra memory',
      'Original Storage Tier': '3iops-tier',
      'Chosen Storage Tier': '10iops-tier',
      'Storage Tier Override Reason': 'Production database write latency target',
      'Include/Exclude': 'Exclude',
      'Exclusion Reason': 'Retired before migration',
    });
  });

  it('exports stable decision audit CSV headers', () => {
    const csv = decisionAuditCsv([overrideVm]);

    expect(csv).toContain('VM Key,VM Name,Owner,Application,Wave,Original Profile,Chosen Profile,Profile Override Reason');
    expect(csv).toContain('vm-1,db-01,DB owner,Database,Wave 2,bx2-4x16,mx2-16x128');
  });

  it('summarizes override counts and missing reasons', () => {
    expect(summarizeOverrides([
      overrideVm,
      { ...overrideVm, id: 'vm-2', overrideProfileReason: '', excluded: false },
    ])).toEqual({
      profileOverrides: 2,
      storageOverrides: 2,
      excluded: 1,
      missingReasons: 1,
    });
  });

  it('builds VSI profile options from common sizes and uploaded rows', () => {
    const options = buildProfileOptions([
      { ...overrideVm, profile: 'custom-12x48', overrideProfile: 'mx2-16x128' },
    ]);

    expect(options).toEqual(expect.arrayContaining([
      'bx2-2x8',
      'mx2-16x128',
      'custom-12x48',
    ]));
    expect(profileSizeLabel('mx2-16x128')).toBe('mx2-16x128 (16 vCPU / 128 GB)');
  });

  it('renders the override workflow and edits a VM profile override', async () => {
    renderWithProvider(<OverridesWorkflow />);

    expect(screen.getByText('VM Overrides')).toBeTruthy();
    expect(screen.getByText('Export decision audit CSV')).toBeTruthy();
    expect(screen.getAllByText('Effective: bx2-2x8 (2 vCPU / 8 GB)').length).toBeGreaterThan(0);

    const profileSelect = screen.getByLabelText('Override profile for app-01') as HTMLSelectElement;
    await userEvent.selectOptions(profileSelect, 'mx2-16x128');

    expect(profileSelect.value).toBe('mx2-16x128');
    expect(screen.getByText('Effective: mx2-16x128 (16 vCPU / 128 GB)')).toBeTruthy();
    expect(screen.getByText('Reason needed')).toBeTruthy();

    await userEvent.type(
      screen.getByLabelText('Profile override reason for app-01'),
      'Memory validation approved by workload owner',
    );
    expect(screen.queryByText('Reason needed')).toBeNull();

    await userEvent.click(screen.getAllByText('Reset profile override')[0]);
    expect(profileSelect.value).toBe('');
    expect(screen.getAllByText('Effective: bx2-2x8 (2 vCPU / 8 GB)').length).toBeGreaterThan(0);
  });

  it('bulk applies profile overrides and clears missing profile reasons', async () => {
    renderWithProvider(<OverridesWorkflow />);

    await userEvent.click(screen.getByRole('button', { name: 'Select visible' }));
    await userEvent.selectOptions(screen.getByLabelText('Bulk profile override'), 'mx2-16x128');
    await userEvent.click(screen.getByRole('button', { name: 'Apply profile' }));

    expect(screen.getAllByText('Override').length).toBeGreaterThanOrEqual(3);
    expect(screen.getAllByText('Reason needed').length).toBe(3);

    await userEvent.selectOptions(screen.getByLabelText('Override filter'), 'missingReasons');
    expect(screen.getByText('app-01')).toBeTruthy();
    expect(screen.getByText('db-01')).toBeTruthy();
    expect(screen.getByText('web-01')).toBeTruthy();

    await userEvent.type(
      screen.getByLabelText('Bulk profile reason'),
      'Bulk rightsizing approved by migration architect',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Apply profile reason' }));

    expect(screen.queryByText('Reason needed')).toBeNull();
  });
});
