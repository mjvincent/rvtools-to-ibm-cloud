import React from 'react';
import { render, screen } from '@testing-library/react';
import OverviewWorkflow from '../../components/workflows/OverviewWorkflow';
import { AppProvider } from '../../store/AppContext';

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe('OverviewWorkflow', () => {
  it('renders the overview heading', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Planning overview')).toBeTruthy();
  });

  it('shows Prototype planner tag', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Prototype planner')).toBeTruthy();
  });

  it('renders assessment quality tile', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Assessment quality')).toBeTruthy();
  });

  it('renders assignment completeness tile', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Assignment completeness')).toBeTruthy();
  });

  it('renders open subnet assignments tile', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Open subnet assignments')).toBeTruthy();
  });

  it('renders open security assignments tile', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Open security assignments')).toBeTruthy();
  });

  it('shows Sample preview when no summary loaded', () => {
    renderWithProvider(<OverviewWorkflow />);
    expect(screen.getByText('Sample preview')).toBeTruthy();
  });

  it('shows correct VM count from default sample rows', () => {
    renderWithProvider(<OverviewWorkflow />);
    // 3 sample rows, none have subnet assigned → 3 missing
    expect(screen.getByText(/3 VMs need target subnet placement/)).toBeTruthy();
  });
});
