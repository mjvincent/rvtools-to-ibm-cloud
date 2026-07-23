import React from 'react';
import { render, screen } from '@testing-library/react';
import ProjectSaveGuidance, {
  buildProjectSaveGuidance,
} from '../../components/ui/ProjectSaveGuidance';

const baseInput = {
  persistenceEnabled: true,
  selectedProjectId: 'project-1',
  isDirty: false,
  autoSaveStatus: 'Planning changes saved.',
  autoSaveError: '',
  projectError: '',
  apiStatus: 'API online with persistence',
};

describe('buildProjectSaveGuidance', () => {
  it('warns users when persistence is unavailable', () => {
    const guidance = buildProjectSaveGuidance({
      ...baseInput,
      persistenceEnabled: false,
      selectedProjectId: '',
      autoSaveStatus: '',
      apiStatus: 'API unavailable',
    });

    expect(guidance.label).toBe('Persistence unavailable');
    expect(guidance.headline).toContain('temporary');
    expect(guidance.bullets).toContain(
      'Do not refresh or close the browser until persistence is restored or you have exported needed files.',
    );
  });

  it('explains browser-only work before the first project save', () => {
    const guidance = buildProjectSaveGuidance({
      ...baseInput,
      selectedProjectId: '',
      autoSaveStatus: '',
    });

    expect(guidance.label).toBe('Not saved yet');
    expect(guidance.detail).toContain('browser-side');
    expect(guidance.bullets).toContain(
      'Refresh, browser close, or switching machines can lose unsaved browser work.',
    );
  });

  it('explains queued autosave for dirty saved projects', () => {
    const guidance = buildProjectSaveGuidance({
      ...baseInput,
      isDirty: true,
      autoSaveStatus: 'Unsaved changes queued.',
    });

    expect(guidance.label).toBe('Unsaved changes');
    expect(guidance.detail).toBe('Unsaved changes queued.');
    expect(guidance.bullets).toContain(
      'Wait for the saved status or use Save project before closing the browser.',
    );
  });

  it('explains that saved projects restore planning state but not source files', () => {
    const guidance = buildProjectSaveGuidance(baseInput);

    expect(guidance.label).toBe('Project current');
    expect(guidance.headline).toContain('Postgres');
    expect(guidance.bullets).toContain(
      'You can resume saved planning state from the Saved project selector.',
    );
    expect(guidance.bullets).toContain(
      'Keep the original RVTools workbook; project save stores planning state, not the workbook as the system of record.',
    );
    expect(guidance.bullets).toContain(
      'Download and retain Terraform ZIPs and readiness reports after they are generated.',
    );
  });
});

describe('ProjectSaveGuidance', () => {
  it('renders state-aware save guidance', () => {
    render(<ProjectSaveGuidance {...baseInput} />);

    expect(screen.getByLabelText('Project save guidance')).toBeTruthy();
    expect(screen.getByText('Project current')).toBeTruthy();
    expect(screen.getByText('Planning state is saved to Postgres.')).toBeTruthy();
    expect(screen.getByText(/Keep the original RVTools workbook/)).toBeTruthy();
  });
});
