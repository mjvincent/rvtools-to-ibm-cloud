import { filterAndSortAssignmentRows } from '../components/workflows/AssignmentWorkflow';
import { filterOverrideRows } from '../components/workflows/OverridesWorkflow';
import type { AssignmentVm } from '../types/network-planning';

const LARGE_ROW_COUNT = 5000;

function maxMs(envName: string, fallback: number) {
  const value = Number(process.env[envName]);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function largeRows(count = LARGE_ROW_COUNT): AssignmentVm[] {
  return Array.from({ length: count }, (_, index) => {
    const ordinal = index + 1;
    const tier = ordinal % 5 === 0 ? '10iops-tier' : ordinal % 3 === 0 ? '5iops-tier' : '3iops-tier';
    const profile = ordinal % 4 === 0 ? 'bx2-4x16' : 'bx2-2x8';
    const overrideProfile = ordinal % 3 === 0 ? 'mx2-16x128' : '';
    const overrideStorageTier = ordinal % 5 === 0 ? '10iops-tier' : '';
    return {
      id: `large-vm-${String(ordinal).padStart(5, '0')}`,
      name: ordinal === 4777 ? 'needle-app-4777' : `large-app-${String(ordinal).padStart(5, '0')}`,
      image: ordinal % 7 === 0 ? 'Review' : 'Ready',
      imageReasons: ordinal % 7 === 0 ? 'Validate image import path' : '',
      migration: ordinal % 11 === 0 ? 'Blocked' : 'Ready',
      migrationReasons: ordinal % 11 === 0 ? 'Owner validation needed' : '',
      memory: ordinal % 3 === 0 ? 'Review' : 'Ready',
      memoryReasons: ordinal % 3 === 0 ? 'Memory pressure review' : '',
      networkReadiness: ordinal % 13 === 0 ? 'Review' : 'Ready',
      networkReasons: ordinal % 13 === 0 ? 'Validate routing' : '',
      profile,
      overrideProfile,
      overrideProfileReason: ordinal % 6 === 0 ? 'Architect-approved rightsizing' : '',
      storageTier: tier,
      overrideStorageTier,
      overrideStorageTierReason: ordinal % 10 === 0 ? 'Database write latency target' : '',
      network: ordinal % 2 === 0 ? 'app-net' : 'db-net',
      subnet: ordinal % 2 === 0 ? 'prod-app-us-south-1' : 'prod-db-us-south-1',
      securityGroup: ordinal % 2 === 0 ? 'sg-app-private' : 'sg-db-private',
      power: 'poweredOn',
      owner: `Owner ${ordinal % 12}`,
      application: ordinal % 2 === 0 ? 'App tier' : 'Database',
      wave: ordinal % 4 === 0 ? 'Wave 1' : '',
      cutoverGroup: ordinal % 4 === 0 ? 'Wave 1' : '',
      priority: ordinal % 9 === 0 ? 'high' : 'medium',
      dependencyGroup: `dep-${ordinal % 20}`,
      excluded: ordinal % 17 === 0,
      exclusionReason: ordinal % 34 === 0 ? 'Retired before migration' : '',
    };
  });
}

describe('Carbon large UI performance guards', () => {
  it('filters and sorts assignment rows at generated large-workbook scale', () => {
    const rows = largeRows();
    const start = performance.now();
    const result = filterAndSortAssignmentRows(rows, {
      searchValue: 'needle-app-4777',
      readinessFilter: 'all',
      sortKey: 'name',
      sortDirection: 'asc',
    });
    const elapsed = performance.now() - start;

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('needle-app-4777');
    expect(elapsed).toBeLessThan(maxMs('CARBON_UI_ASSIGNMENT_FILTER_MAX_MS', 250));
  });

  it('filters override reason gaps at generated large-workbook scale', () => {
    const rows = largeRows();
    const expectedMissingCount = rows.filter((row) =>
      (row.overrideProfile && !row.overrideProfileReason?.trim())
        || (row.overrideStorageTier && !row.overrideStorageTierReason?.trim())
        || (row.excluded && !row.exclusionReason?.trim()),
    ).length;

    const start = performance.now();
    const result = filterOverrideRows(rows, '', 'missingReasons');
    const elapsed = performance.now() - start;

    expect(result).toHaveLength(expectedMissingCount);
    expect(result.every((row) =>
      (row.overrideProfile && !row.overrideProfileReason?.trim())
        || (row.overrideStorageTier && !row.overrideStorageTierReason?.trim())
        || (row.excluded && !row.exclusionReason?.trim()),
    )).toBe(true);
    expect(elapsed).toBeLessThan(maxMs('CARBON_UI_OVERRIDES_FILTER_MAX_MS', 250));
  });
});
