import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import VmRow from '../../components/ui/VmRow';
import type { AssignmentVm } from '../../types/network-planning';

const mockVm: AssignmentVm = {
  id: 'test-vm-01',
  name: 'web-server-01',
  image: 'Ready',
  imageReasons: '',
  migration: 'Review',
  migrationReasons: '',
  memory: 'Ready',
  memoryReasons: '',
  networkReadiness: 'Ready',
  networkReasons: '',
  profile: 'bx2-2x8',
  overrideProfile: '',
  storageTier: '3iops-tier',
  overrideStorageTier: '',
  network: 'web-net',
  subnet: 'prod-app-subnet',
  securityGroup: '',
  power: 'poweredOn',
  owner: 'team-a',
  application: 'Web tier',
  wave: '',
  cutoverGroup: '',
  priority: '',
  dependencyGroup: '',
};

describe('VmRow', () => {
  it('renders VM name', () => {
    render(
      <table><tbody>
        <VmRow vm={mockVm} selected={false} onToggle={() => {}} />
      </tbody></table>,
    );
    expect(screen.getByText('web-server-01')).toBeTruthy();
  });

  it('renders assigned subnet', () => {
    render(
      <table><tbody>
        <VmRow vm={mockVm} selected={false} onToggle={() => {}} />
      </tbody></table>,
    );
    expect(screen.getByText('prod-app-subnet')).toBeTruthy();
  });

  it('renders self-describing readiness labels', () => {
    render(
      <table><tbody>
        <VmRow vm={mockVm} selected={false} onToggle={() => {}} />
      </tbody></table>,
    );
    expect(screen.getByText('IMG Ready')).toBeTruthy();
    expect(screen.getByText('MIG Review')).toBeTruthy();
    expect(screen.getByText('MEM Ready')).toBeTruthy();
    expect(screen.getByText('NET Ready')).toBeTruthy();
  });

  it('shows Unassigned when securityGroup is empty', () => {
    render(
      <table><tbody>
        <VmRow vm={mockVm} selected={false} onToggle={() => {}} />
      </tbody></table>,
    );
    const cells = screen.getAllByText('Unassigned');
    expect(cells.length).toBeGreaterThan(0);
  });

  it('calls onToggle when checkbox is changed', async () => {
    const onToggle = jest.fn();
    render(
      <table><tbody>
        <VmRow vm={mockVm} selected={false} onToggle={onToggle} />
      </tbody></table>,
    );
    const checkbox = screen.getByRole('checkbox', { name: 'Select web-server-01' });
    await userEvent.click(checkbox);
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('checkbox is checked when selected is true', () => {
    render(
      <table><tbody>
        <VmRow vm={mockVm} selected={true} onToggle={() => {}} />
      </tbody></table>,
    );
    const checkbox = screen.getByRole('checkbox', { name: 'Select web-server-01' }) as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
  });
});
