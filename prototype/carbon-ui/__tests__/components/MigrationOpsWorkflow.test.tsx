import React from 'react';
import { render, screen } from '@testing-library/react';
import MigrationOpsWorkflow, {
  buildCutoverReadinessRows,
  cutoverReadinessCsv,
  summarizeCutoverReadiness,
} from '../../components/workflows/MigrationOpsWorkflow';
import { AppProvider } from '../../store/AppContext';
import type { AssignmentVm } from '../../types/network-planning';

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

const readyVm: AssignmentVm = {
  id: 'vm-1',
  name: 'app-01',
  image: 'Ready',
  imageReasons: 'rhel-8-template',
  originalSpecs: 'rhel-9-template',
  migration: 'Ready',
  migrationReasons: '',
  memory: 'Ready',
  memoryReasons: '',
  networkReadiness: 'Ready',
  networkReasons: '',
  profile: 'bx2-2x8',
  overrideProfile: '',
  storageTier: '5iops-tier',
  overrideStorageTier: '',
  network: 'app-net',
  subnet: 'prod-app-us-south-1',
  securityGroup: 'sg-app-private',
  power: 'poweredOn',
  owner: 'App owner',
  application: 'App',
  wave: 'Wave 1',
  cutoverGroup: 'CG-A',
  priority: 'high',
  dependencyGroup: '',
};

describe('MigrationOpsWorkflow', () => {
  it('marks VM ready when planning, remediation, readiness, and image import are complete', () => {
    const rows = buildCutoverReadinessRows([readyVm], {}, {
      'rhel-9-template': {
        targetCatalogId: 'r001-12345678',
        importStatus: 'Imported',
        estimatedImportTime: '45m',
        notes: '',
      },
    });

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      cutoverStatus: 'Ready',
      blockerCategory: 'Ready',
    });
  });

  it('flags missing planning, unresolved remediation, and pending image imports', () => {
    const rows = buildCutoverReadinessRows([
      { ...readyVm, wave: '', owner: '', image: 'Review' },
    ], {
      'vm-1::migration': {
        status: 'Open',
        owner: 'App owner',
        dueDate: '2026-07-15',
        notes: 'Resolve migration blocker',
      },
    }, {});

    expect(rows.map((row) => row.blockerCategory)).toEqual(expect.arrayContaining([
      'Missing Planning',
      'Readiness Review',
      'Unresolved Remediation',
      'Image Import Pending',
    ]));
    expect(rows.every((row) => row.cutoverStatus === 'Blocked')).toBe(true);
  });

  it('summarizes cutover readiness by wave', () => {
    const rows = buildCutoverReadinessRows([readyVm], {}, {
      'rhel-9-template': {
        targetCatalogId: 'r001-12345678',
        importStatus: 'Imported',
        estimatedImportTime: '',
        notes: '',
      },
    });

    expect(summarizeCutoverReadiness(rows, 'wave')).toEqual([{
      group: 'Wave 1',
      vms: 1,
      ready: 1,
      review: 0,
      blocked: 0,
      missingPlanning: 0,
      unresolvedRemediation: 0,
      imagePending: 0,
    }]);
  });

  it('exports stable cutover readiness CSV headers', () => {
    const csv = cutoverReadinessCsv(buildCutoverReadinessRows([readyVm], {}, {}));

    expect(csv).toContain('VM Name,Wave,Cutover Group,Owner,Application,Cutover Status,Blocker Category,Blocker Reason,Recommended Next Action');
  });

  it('renders migration ops dashboard', () => {
    renderWithProvider(<MigrationOpsWorkflow />);

    expect(screen.getByText('Migration Ops')).toBeTruthy();
    expect(screen.getByText('By Wave')).toBeTruthy();
    expect(screen.getByText('By Cutover Group')).toBeTruthy();
    expect(screen.getByText('Export cutover readiness CSV')).toBeTruthy();
  });
});
