import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import IntakeWorkflow, { rowsFromSummary } from '../../components/workflows/IntakeWorkflow';
import { AppProvider, useAppState } from '../../store/AppContext';
import { loadSampleWorkbookSummary, uploadWorkbook } from '../../hooks/useApi';
import type { WorkbookSummary } from '../../types/network-planning';

jest.mock('../../hooks/useApi', () => ({
  loadSampleWorkbookSummary: jest.fn(),
  uploadWorkbook: jest.fn(),
}));

function carbonSummary(filename = 'rvtools-upload.xlsx'): WorkbookSummary {
  return {
    filename,
    estate_summary: {
      vm_count: 1,
      total_vcpu: 2,
      total_memory_gb: 8,
      total_storage_gb: 100,
      powered_on: 1,
      powered_off: 0,
    },
    overview_blockers: {},
    readiness_counts: {},
    assessment_quality: {},
    readiness_rows: [],
    assignment_rows: [
      {
        'VM Key': 'vm-001',
        'VM Name': 'app-01',
        'Image Readiness': 'Ready',
        'Migration Readiness': 'Ready',
        'Memory Readiness': 'Ready',
        'Network Readiness': 'Ready',
        'IBM Profile': 'bx2-2x8',
        'Storage Tier': '5iops-tier',
        Network: 'app-net',
        Subnet: 'prod-app-us-south-1',
        'Security Group': 'sg-app-private',
        'Power State': 'poweredOn',
      },
    ],
  } as unknown as WorkbookSummary;
}

function StateProbe() {
  const { state } = useAppState();
  return (
    <div data-testid="intake-state">
      {[
        state.summary?.filename || 'no-summary',
        state.uploadStatus || 'no-status',
        state.uploadError || 'no-error',
        state.projectName,
        state.assignmentRows.length,
        state.assignmentRows[0]?.name || 'no-row',
      ].join('|')}
    </div>
  );
}

function renderIntake() {
  return render(
    <AppProvider>
      <IntakeWorkflow />
      <StateProbe />
    </AppProvider>,
  );
}

describe('rowsFromSummary', () => {
  it('preserves hidden workbook detail fields for handoff exports', () => {
    const rows = rowsFromSummary({
      filename: 'rvtools.xlsx',
      assignment_rows: [
        {
          'VM Key': 'vm-001',
          'VM Name': 'app-01',
          'IBM Profile': 'bx2-2x8',
          'Storage Tier': '5iops-tier',
          'Original Specs': 'rhel-9-template',
          Network: 'app-net',
          'Disk Details': [{ disk: 'Hard disk 1', capacity_gb: 80, is_boot: true }],
          'Network Details': [{ label: 'Network adapter 1', network: 'app-net' }],
          'Readiness Findings': [{ finding_type: 'VMware Tools status', evidence: 'toolsOld' }],
          'Configured Memory MiB': 8192,
          'Total Storage GB': 200,
          'Profile Hourly': 0.114,
        },
      ],
    } as unknown as WorkbookSummary);

    expect(rows[0]).toMatchObject({
      id: 'vm-001',
      name: 'app-01',
      originalSpecs: 'rhel-9-template',
      diskDetails: [{ disk: 'Hard disk 1', capacity_gb: 80, is_boot: true }],
      networkDetails: [{ label: 'Network adapter 1', network: 'app-net' }],
      readinessFindings: [{ finding_type: 'VMware Tools status', evidence: 'toolsOld' }],
      configuredMemoryMib: '8192',
      totalStorageGb: '200',
      profileHourly: '0.114',
    });
  });
});

describe('IntakeWorkflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('loads the bundled sample workbook without using the file picker', async () => {
    (loadSampleWorkbookSummary as jest.Mock).mockResolvedValueOnce(
      carbonSummary('rvtools-small-complete.xlsx'),
    );
    renderIntake();

    await userEvent.click(screen.getByRole('button', { name: /Load sample workbook/i }));

    await waitFor(() => expect(loadSampleWorkbookSummary).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByText('Loaded rvtools-small-complete.xlsx')).toBeTruthy());
    expect(screen.getByTestId('intake-state').textContent).toContain(
      'rvtools-small-complete.xlsx|Loaded rvtools-small-complete.xlsx|no-error|rvtools-small-complete|1|app-01',
    );
  });

  it('reports workbook upload failures without replacing the current workbook state', async () => {
    (uploadWorkbook as jest.Mock).mockRejectedValueOnce(
      new Error('Workbook parser unavailable during upload.'),
    );
    renderIntake();

    const file = new File(['not really xlsx'], 'broken.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    await userEvent.upload(screen.getByTestId('file-input'), file);

    await waitFor(() => expect(uploadWorkbook).toHaveBeenCalledWith(file));
    expect(screen.getByText('Upload failed')).toBeTruthy();
    expect(screen.getByText('Workbook parser unavailable during upload.')).toBeTruthy();
    expect(screen.getByTestId('intake-state').textContent).toContain(
      'no-summary|no-status|Workbook parser unavailable during upload.|Migration assessment|3|app-01',
    );
  });

  it('clears a previous upload error after a successful retry', async () => {
    (uploadWorkbook as jest.Mock)
      .mockRejectedValueOnce(new Error('Temporary workbook upload outage.'))
      .mockResolvedValueOnce(carbonSummary('retry-workbook.xlsx'));
    renderIntake();

    const badFile = new File(['bad'], 'bad.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    await userEvent.upload(screen.getByTestId('file-input'), badFile);
    await waitFor(() => expect(screen.getByText('Temporary workbook upload outage.')).toBeTruthy());

    const goodFile = new File(['good'], 'retry-workbook.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    await userEvent.upload(screen.getByTestId('file-input'), goodFile);

    await waitFor(() => expect(uploadWorkbook).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByText('Loaded retry-workbook.xlsx')).toBeTruthy());
    expect(screen.queryByText('Temporary workbook upload outage.')).toBeNull();
    expect(screen.getByTestId('intake-state').textContent).toContain(
      'retry-workbook.xlsx|Loaded retry-workbook.xlsx|no-error|retry-workbook|1|app-01',
    );
  });
});
