import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
    const imageRows = buildImageImportRows([
      ...rows,
      {
        ...rows[1],
        id: 'vm-3',
        name: 'db-03',
        owner: 'Analytics team',
      },
    ], {});

    expect(imageRows).toHaveLength(1);
    expect(imageRows[0]).toMatchObject({
      sourceImage: 'rhel-9-template',
      vmCount: 3,
      owners: 'Analytics team; Data team',
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

  it('skips totals and unknown source images when importing for current rows', () => {
    const csv = [
      'Source Image,Count of VMs,Owners,Target Catalog ID,Import Status,Estimated Import Time,Notes',
      'rhel-9-template,2,Data team,r001-db-image,Imported,45m,Ready',
      'stale-template,1,Ops,r001-stale,Imported,15m,Should not apply',
      'TOTAL,3,,,,,',
    ].join('\n');

    const result = importImageImportCsv(csv, {}, ['rhel-9-template']);

    expect(result.applied).toBe(1);
    expect(result.skipped).toBe(2);
    expect(result.status).toEqual({
      'rhel-9-template': {
        targetCatalogId: 'r001-db-image',
        importStatus: 'Imported',
        estimatedImportTime: '45m',
        notes: 'Ready',
      },
    });
  });

  it('normalizes unsupported import statuses to not started', () => {
    const csv = [
      'Source Image,Count of VMs,Owners,target_catalog_id,import_status,estimated_import_time,Notes',
      'rhel-9-template,2,Data team,r001-db-image,Complete,45m,Invalid status from external CSV',
    ].join('\n');

    const result = importImageImportCsv(csv, {});

    expect(result.status['rhel-9-template']).toEqual({
      targetCatalogId: 'r001-db-image',
      importStatus: '',
      estimatedImportTime: '45m',
      notes: 'Invalid status from external CSV',
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

    const catalogControls = screen.getAllByLabelText('Target catalog ID');
    fireEvent.change(catalogControls[0], { target: { value: 'r001-sample-db-image' } });
    expect((catalogControls[0] as HTMLInputElement).value).toBe('r001-sample-db-image');

    const statusControls = screen.getAllByLabelText('Import status');
    fireEvent.change(statusControls[0], { target: { value: 'Pending' } });
    expect((statusControls[0] as HTMLSelectElement).value).toBe('Pending');

    const timeControls = screen.getAllByLabelText('Estimated import time');
    fireEvent.change(timeControls[0], { target: { value: '60m' } });
    expect((timeControls[0] as HTMLInputElement).value).toBe('60m');

    const noteControls = screen.getAllByLabelText('Notes');
    fireEvent.change(noteControls[0], { target: { value: 'Track before cutover' } });
    expect((noteControls[0] as HTMLTextAreaElement).value).toBe('Track before cutover');
  });

  it('offers CSV import and export controls', () => {
    renderWithProvider(<ImageImportWorkflow />);

    expect(screen.getByText('Import image import CSV')).toBeTruthy();
    expect(screen.getByText('Export image import CSV')).toBeTruthy();
  });

  it('imports known image rows from the rendered CSV uploader and reports skipped rows', async () => {
    renderWithProvider(<ImageImportWorkflow />);

    const csv = [
      'Source Image,Count of VMs,Owners,Target Catalog ID,Import Status,Estimated Import Time,Notes',
      'Confirm image import path,1,,r001-sample-db-image,Pending,60m,Track before migration',
      'stale-template,1,,r001-stale,Imported,15m,Should be skipped',
    ].join('\n');
    const file = new File([csv], 'image-import-plan.csv', { type: 'text/csv' });
    Object.defineProperty(file, 'text', {
      value: async () => csv,
    });

    fireEvent.change(screen.getByTestId('file-input'), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByText('Imported 1 image row(s); skipped 1 row(s).')).toBeTruthy();
    });
    expect((screen.getAllByLabelText('Target catalog ID')[1] as HTMLInputElement).value)
      .toBe('r001-sample-db-image');
    expect((screen.getAllByLabelText('Import status')[1] as HTMLSelectElement).value)
      .toBe('Pending');
  });
});
