import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import WavesWorkflow, {
  applyWaveBulkAssignment,
  detectApplicationCutoverConflicts,
  detectDependencyWaveConflicts,
  importWavePlanningCsv,
  waveCompletion,
  wavePlanningCsv,
} from '../../components/workflows/WavesWorkflow';
import { AppProvider, sampleRows } from '../../store/AppContext';

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe('WavesWorkflow', () => {
  it('calculates completion for required wave fields', () => {
    const rows = [
      { ...sampleRows[0], wave: 'Wave 1', cutoverGroup: 'CG-A', owner: 'Owner', application: 'App' },
      { ...sampleRows[1], wave: 'Wave 1', cutoverGroup: '', owner: 'Owner', application: 'DB' },
    ];

    expect(waveCompletion(rows)).toEqual({
      total: 2,
      complete: 1,
      incomplete: 1,
    });
  });

  it('detects application cutover conflicts', () => {
    const rows = [
      { ...sampleRows[0], application: 'Billing', cutoverGroup: 'CG-A' },
      { ...sampleRows[1], application: 'Billing', cutoverGroup: 'CG-B' },
    ];

    expect(detectApplicationCutoverConflicts(rows)).toEqual([{
      application: 'Billing',
      cutoverGroups: ['CG-A', 'CG-B'],
    }]);
  });

  it('detects dependency wave conflicts', () => {
    const rows = [
      { ...sampleRows[0], dependencyGroup: 'dep-a', wave: 'Wave 1' },
      { ...sampleRows[1], dependencyGroup: 'dep-a', wave: 'Wave 2' },
    ];

    expect(detectDependencyWaveConflicts(rows)).toEqual([{
      dependencyGroup: 'dep-a',
      waves: ['Wave 1', 'Wave 2'],
    }]);
  });

  it('exports and imports wave planning CSV rows', () => {
    const csv = wavePlanningCsv([
      { ...sampleRows[0], wave: 'Wave 1', cutoverGroup: 'CG-A', owner: 'Owner', application: 'App', priority: 'High', dependencyGroup: 'dep-a' },
    ]);

    const result = importWavePlanningCsv(csv, sampleRows);

    expect(result.applied).toBe(1);
    expect(result.rows[0]).toMatchObject({
      wave: 'Wave 1',
      cutoverGroup: 'CG-A',
      owner: 'Owner',
      application: 'App',
      priority: 'High',
      dependencyGroup: 'dep-a',
    });
  });

  it('applies bulk wave fields to incomplete rows without clearing existing values', () => {
    const rows = [
      { ...sampleRows[0], wave: '', cutoverGroup: '', owner: '', application: '', priority: '', dependencyGroup: '' },
      { ...sampleRows[1], wave: 'Wave 2', cutoverGroup: 'CG-B', owner: 'DB', application: 'Database', priority: 'Low', dependencyGroup: 'db' },
    ];

    const result = applyWaveBulkAssignment(rows, {
      Wave: 'Wave 1',
      'Cutover Group': 'CG-A',
      Owner: 'App owner',
      Application: 'Orders',
      Priority: 'High',
      'Dependency Group': '',
    }, 'incomplete');

    expect(result.applied).toBe(1);
    expect(result.rows[0]).toMatchObject({
      wave: 'Wave 1',
      cutoverGroup: 'CG-A',
      owner: 'App owner',
      application: 'Orders',
      priority: 'High',
      dependencyGroup: '',
    });
    expect(result.rows[1]).toMatchObject({
      wave: 'Wave 2',
      cutoverGroup: 'CG-B',
      owner: 'DB',
      application: 'Database',
      priority: 'Low',
      dependencyGroup: 'db',
    });
  });

  it('applies bulk wave fields to selected rows only', () => {
    const result = applyWaveBulkAssignment(sampleRows, {
      Wave: 'Wave 3',
      'Cutover Group': 'CG-C',
      Owner: '',
      Application: '',
      Priority: '',
      'Dependency Group': '',
    }, 'selected', [sampleRows[1].id]);

    expect(result.applied).toBe(1);
    expect(result.rows[0].wave).toBe(sampleRows[0].wave);
    expect(result.rows[1]).toMatchObject({
      wave: 'Wave 3',
      cutoverGroup: 'CG-C',
    });
  });

  it('reports unmatched wave planning CSV rows during import', () => {
    const csv = [
      'VM Key,VM Name,Wave,Cutover Group,Owner,Application,Priority,Dependency Group',
      '"missing-vm","missing","Wave 9","CG-X","Owner","App","Low","dep-x"',
      `"${sampleRows[0].id}","${sampleRows[0].name}","Wave 1","CG-A","Owner","App","High","dep-a"`,
    ].join('\n');

    const result = importWavePlanningCsv(csv, sampleRows);

    expect(result.applied).toBe(1);
    expect(result.skipped).toBe(1);
    expect(result.rows[0]).toMatchObject({
      wave: 'Wave 1',
      cutoverGroup: 'CG-A',
      owner: 'Owner',
      application: 'App',
      priority: 'High',
      dependencyGroup: 'dep-a',
    });
  });

  it('renders editable wave planning rows', () => {
    renderWithProvider(<WavesWorkflow />);

    expect(screen.getByText('Wave Planning')).toBeTruthy();
    expect(screen.getByText('Export wave planning CSV')).toBeTruthy();
    expect(screen.getByText('Apply bulk wave fields')).toBeTruthy();

    const waveInput = screen.getAllByLabelText('Wave')[1] as HTMLInputElement;
    fireEvent.change(waveInput, { target: { value: 'Pilot' } });

    expect(waveInput.value).toBe('Pilot');
  });

  it('applies bulk wave fields from the rendered workflow', () => {
    renderWithProvider(<WavesWorkflow />);

    fireEvent.change(screen.getAllByLabelText('Wave')[0], { target: { value: 'Wave 1' } });
    fireEvent.change(screen.getAllByLabelText('Cutover Group')[0], { target: { value: 'CG-A' } });
    fireEvent.change(screen.getAllByLabelText('Owner')[0], { target: { value: 'Migration owner' } });
    fireEvent.change(screen.getAllByLabelText('Application')[0], { target: { value: 'Orders' } });
    fireEvent.change(screen.getAllByLabelText('Priority')[0], { target: { value: 'High' } });
    fireEvent.change(screen.getAllByLabelText('Dependency Group')[0], { target: { value: 'orders-core' } });
    fireEvent.click(screen.getByText('Apply bulk wave fields'));

    expect(screen.getByText(/3\s+of\s+3\s+complete/)).toBeTruthy();
    expect(screen.getByText('Applied bulk wave planning to 3 VM(s).')).toBeTruthy();
    expect((screen.getAllByLabelText('Wave')[1] as HTMLInputElement).value).toBe('Wave 1');
    expect((screen.getAllByLabelText('Priority')[1] as HTMLSelectElement).value).toBe('High');
  });

  it('edits all wave planning fields and surfaces conflicts', () => {
    renderWithProvider(<WavesWorkflow />);

    expect(screen.getByText(/0\s+of\s+3\s+complete/)).toBeTruthy();

    const waveInputs = screen.getAllByLabelText('Wave').slice(1) as HTMLInputElement[];
    const cutoverInputs = screen.getAllByLabelText('Cutover Group').slice(1) as HTMLInputElement[];
    const ownerInputs = screen.getAllByLabelText('Owner').slice(1) as HTMLInputElement[];
    const applicationInputs = screen.getAllByLabelText('Application').slice(1) as HTMLInputElement[];
    const prioritySelects = screen.getAllByLabelText('Priority').slice(1) as HTMLSelectElement[];
    const dependencyInputs = screen.getAllByLabelText('Dependency Group').slice(1) as HTMLInputElement[];

    fireEvent.change(waveInputs[0], { target: { value: 'Wave 1' } });
    fireEvent.change(cutoverInputs[0], { target: { value: 'CG-A' } });
    fireEvent.change(ownerInputs[0], { target: { value: 'app-team' } });
    fireEvent.change(applicationInputs[0], { target: { value: 'Orders' } });
    fireEvent.change(prioritySelects[0], { target: { value: 'High' } });
    fireEvent.change(dependencyInputs[0], { target: { value: 'orders-core' } });

    fireEvent.change(waveInputs[1], { target: { value: 'Wave 2' } });
    fireEvent.change(cutoverInputs[1], { target: { value: 'CG-B' } });
    fireEvent.change(ownerInputs[1], { target: { value: 'db-team' } });
    fireEvent.change(applicationInputs[1], { target: { value: 'Orders' } });
    fireEvent.change(prioritySelects[1], { target: { value: 'Medium' } });
    fireEvent.change(dependencyInputs[1], { target: { value: 'orders-core' } });

    expect(screen.getByText(/2\s+of\s+3\s+complete/)).toBeTruthy();
    expect(screen.getByText('Application Orders spans multiple cutover groups')).toBeTruthy();
    expect(screen.getByText('Dependency group orders-core spans multiple waves')).toBeTruthy();
    expect(prioritySelects[0].value).toBe('High');
    expect(prioritySelects[1].value).toBe('Medium');
  });
});
