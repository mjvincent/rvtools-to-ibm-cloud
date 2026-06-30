import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ImageImportWorkflow, {
  buildImageImportRows,
  importImageImportCsv,
} from '../../components/workflows/ImageImportWorkflow';
import { AppProvider } from '../../store/AppContext';
import type { AssignmentVm } from '../../types/network-planning';

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

const rows: AssignmentVm[] = [
  {
    id: 'vm-1',
    name: 'db-01',
    image: 'Review',
    imageReasons: 'rhel-8-template',
    originalSpecs: 'rhel-9-template',
    migration: 'Ready',
    migrationReasons: '',
    memory: 'Ready',
    memoryReasons: '',
    networkReadiness: 'Ready',
    networkReasons: '',
    profile: 'bx2-4x16',
    overrideProfile: '',
    storageTier: '10iops-tier',
    overrideStorageTier: '',
    network: 'db-net',
    subnet: '',
    securityGroup: '',
    power: 'poweredOn',
    owner: 'Data team',
    application: 'Database',
    wave: '',
    cutoverGroup: '',
    priority: '',
    dependencyGroup: '',
  },
  {
    id: 'vm-2',
    name: 'db-02',
    image: 'Review',
    imageReasons: 'rhel-8-template',
    originalSpecs: 'rhel-9-template',
    migration: 'Ready',
    migrationReasons: '',
    memory: 'Ready',
    memoryReasons: '',
    networkReadiness: 'Ready',
    networkReasons: '',
    profile: 'bx2-4x16',
    overrideProfile: '',
    storageTier: '10iops-tier',
    overrideStorageTier: '',
    network: 'db-net',
    subnet: '',
    securityGroup: '',
    power: 'poweredOn',
    owner: 'Data team',
    application: 'Database',
    wave: '',
    cutoverGroup: '',
    priority: '',
    dependencyGroup: '',
  },
];

describe('ImageImportWorkflow', () => {
  it('groups VMs by inferred source image', () => {
    const imageRows = buildImageImportRows(rows, {});

    expect(imageRows).toHaveLength(1);
    expect(imageRows[0]).toMatchObject({
      sourceImage: 'rhel-9-template',
      vmCount: 2,
      owners: 'Data team',
    });
  });

  it('imports Streamlit-compatible image import CSV rows', () => {
    const csv = [
      'Source Image,Count of VMs,Owners,Target Catalog ID,Import Status,Estimated Import Time,Notes',
      'rhel-8-template,2,Data team,r001-12345678,Imported,45m,Imported from COS',
    ].join('\n');

    const result = importImageImportCsv(csv, {});

    expect(result.applied).toBe(1);
    expect(result.status['rhel-8-template']).toEqual({
      targetCatalogId: 'r001-12345678',
      importStatus: 'Imported',
      estimatedImportTime: '45m',
      notes: 'Imported from COS',
    });
  });

  it('falls back to readiness reasons when original specs are unavailable', () => {
    const imageRows = buildImageImportRows(rows.map(({ originalSpecs, ...row }) => row), {});

    expect(imageRows[0].sourceImage).toBe('rhel-8-template');
  });

  it('renders image import planning rows and allows status edits', () => {
    renderWithProvider(<ImageImportWorkflow />);

    expect(screen.getByText('Image Import Planning')).toBeTruthy();
    expect(screen.getByText('Confirm image import path')).toBeTruthy();

    const statusControls = screen.getAllByLabelText('Import status');
    fireEvent.change(statusControls[0], { target: { value: 'Pending' } });

    expect((statusControls[0] as HTMLSelectElement).value).toBe('Pending');
  });

  it('offers CSV import and export controls', () => {
    renderWithProvider(<ImageImportWorkflow />);

    expect(screen.getByText('Import image import CSV')).toBeTruthy();
    expect(screen.getByText('Export image import CSV')).toBeTruthy();
  });
});
