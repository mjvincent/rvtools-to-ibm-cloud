import { rowsFromSummary } from '../../components/workflows/IntakeWorkflow';
import type { WorkbookSummary } from '../../types/network-planning';

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
      diskDetails: [{ disk: 'Hard disk 1', capacity_gb: 80, is_boot: true }],
      networkDetails: [{ label: 'Network adapter 1', network: 'app-net' }],
      readinessFindings: [{ finding_type: 'VMware Tools status', evidence: 'toolsOld' }],
      configuredMemoryMib: '8192',
      totalStorageGb: '200',
      profileHourly: '0.114',
    });
  });
});
