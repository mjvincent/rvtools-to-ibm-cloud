import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import WavesWorkflow, {
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

  it('renders editable wave planning rows', () => {
    renderWithProvider(<WavesWorkflow />);

    expect(screen.getByText('Wave Planning')).toBeTruthy();
    expect(screen.getByText('Export wave planning CSV')).toBeTruthy();

    const waveInput = screen.getAllByLabelText('Wave')[0] as HTMLInputElement;
    fireEvent.change(waveInput, { target: { value: 'Pilot' } });

    expect(waveInput.value).toBe('Pilot');
  });
});
