import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import RemediationWorkflow, {
  buildRemediationBacklog,
  importRemediationCsv,
} from '../../components/workflows/RemediationWorkflow';
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

  it('builds all readiness blocker categories with saved tracker fields', () => {
    const row = {
      ...baseRow,
      image: 'Review',
      imageReasons: 'Image import path needs review',
      migration: 'Blocked',
      migrationReasons: 'Snapshot must be removed',
      memory: 'Review',
      memoryReasons: 'Memory pressure needs validation',
      networkReadiness: 'Blocked',
      networkReasons: 'Disconnected NIC requires routing decision',
    };
    const backlog = buildRemediationBacklog([row], {
      'vm-1::network': {
        status: 'In Progress',
        owner: 'net-team',
        dueDate: '2026-07-31',
        notes: 'Waiting on firewall review.',
      },
    });

    expect(backlog.map((item) => item.blockerType)).toEqual([
      'Image',
      'Migration',
      'Memory',
      'Network',
    ]);
    expect(backlog.find((item) => item.blockerId === 'vm-1::network')).toMatchObject({
      blockerDescription: 'Disconnected NIC requires routing decision',
      status: 'In Progress',
      owner: 'net-team',
      dueDate: '2026-07-31',
      notes: 'Waiting on firewall review.',
    });
  });

  it('uses saved Streamlit-compatible blocker metadata when present', () => {
    const backlog = buildRemediationBacklog([baseRow], {
      'vm-1::migration': {
        status: 'Open',
        owner: 'migration-team',
        dueDate: '2026-07-31',
        notes: 'Imported from Streamlit handoff.',
        vm_key: 'vm-1',
        blocker_type: 'Migration',
        blocker_description: 'VMware Tools status requires review',
      },
    });

    expect(backlog.find((item) => item.blockerId === 'vm-1::migration')).toMatchObject({
      vmKey: 'vm-1',
      blockerType: 'Migration',
      blockerDescription: 'VMware Tools status requires review',
      owner: 'migration-team',
      notes: 'Imported from Streamlit handoff.',
    });
  });

  it('normalizes lowercase readiness statuses into backlog rows', () => {
    const backlog = buildRemediationBacklog([{
      ...baseRow,
      migration: 'blocked' as any,
      memory: 'review' as any,
    }], {});

    expect(backlog.map((item) => item.blockerType)).toEqual(['Migration', 'Memory']);
  });

  it('renders remediation rows and allows status edits', () => {
    renderWithProvider(<RemediationWorkflow />);

    expect(screen.getByText('Remediation Backlog')).toBeTruthy();
    expect(screen.getByText('Resolve source migration finding')).toBeTruthy();

    const statusControls = screen.getAllByLabelText('Status');
    fireEvent.change(statusControls[0], { target: { value: 'In Progress' } });

    expect((statusControls[0] as HTMLSelectElement).value).toBe('In Progress');
  });

  it('edits remediation owner, due date, and notes fields', () => {
    renderWithProvider(<RemediationWorkflow />);

    expect(screen.getByText('5 active')).toBeTruthy();

    const ownerControls = screen.getAllByLabelText('Owner') as HTMLInputElement[];
    const dueDateControls = screen.getAllByLabelText('Due date') as HTMLInputElement[];
    const notesControls = screen.getAllByLabelText('Notes') as HTMLTextAreaElement[];

    fireEvent.change(ownerControls[0], { target: { value: 'migration-lead' } });
    fireEvent.change(dueDateControls[0], { target: { value: '2026-08-15' } });
    fireEvent.change(notesControls[0], { target: { value: 'Assigned during wave review.' } });

    expect(ownerControls[0].value).toBe('migration-lead');
    expect(dueDateControls[0].value).toBe('2026-08-15');
    expect(notesControls[0].value).toBe('Assigned during wave review.');
  });

  it('offers CSV export when backlog items exist', () => {
    renderWithProvider(<RemediationWorkflow />);

    const exportButton = screen.getByText('Export remediation CSV');
    expect(exportButton).toBeTruthy();
    expect(exportButton.closest('button') || exportButton.closest('a')).toBeTruthy();
  });

  it('imports remediation CSV rows by blocker id', () => {
    const backlog = buildRemediationBacklog([baseRow], {});
    const csv = [
      'blocker_id,VM Key,VM Name,Owner,Blocker Type,Blocker Description,Status,Due Date,Notes',
      'vm-1::migration,vm-1,app-01,Alex,Migration,Resolve source migration finding,In Progress,2026-07-15,Working it',
    ].join('\n');

    const result = importRemediationCsv(csv, backlog, {});

    expect(result.applied).toBe(1);
    expect(result.skipped).toBe(0);
    expect(result.tracker['vm-1::migration']).toMatchObject({
      status: 'In Progress',
      owner: 'Alex',
      dueDate: '2026-07-15',
      notes: 'Working it',
      vm_key: 'vm-1',
      blocker_type: 'Migration',
      blocker_description: 'Resolve source migration finding',
    });
  });

  it('imports remediation CSV rows by Streamlit fallback signature', () => {
    const backlog = buildRemediationBacklog([baseRow], {});
    const csv = [
      'VM Key,VM Name,Owner,Blocker Type,Blocker Description,Status,Due Date,Notes',
      '"vm-1","app-01","Blair","Memory","Validate memory pressure","Resolved","2026-07-20","Validated"',
    ].join('\n');

    const result = importRemediationCsv(csv, backlog, {});

    expect(result.applied).toBe(1);
    expect(result.tracker['vm-1::memory']).toMatchObject({
      status: 'Resolved',
      owner: 'Blair',
      dueDate: '2026-07-20',
    });
  });

  it('skips unmatched remediation CSV rows and normalizes unknown statuses', () => {
    const backlog = buildRemediationBacklog([baseRow], {});
    const csv = [
      'blocker_id,VM Key,VM Name,Owner,Blocker Type,Blocker Description,Status,Due Date,Notes',
      'missing::image,missing,missing,Alex,Image,Missing blocker,Deferred,2026-07-15,Skip me',
      'vm-1::migration,vm-1,app-01,Casey,Migration,Resolve source migration finding,Waiting,2026-07-22,Needs triage',
    ].join('\n');

    const result = importRemediationCsv(csv, backlog, {});

    expect(result.applied).toBe(1);
    expect(result.skipped).toBe(1);
    expect(result.tracker['vm-1::migration']).toMatchObject({
      status: 'Open',
      owner: 'Casey',
      dueDate: '2026-07-22',
      notes: 'Needs triage',
      blocker_type: 'Migration',
      blocker_description: 'Resolve source migration finding',
    });
  });
});
