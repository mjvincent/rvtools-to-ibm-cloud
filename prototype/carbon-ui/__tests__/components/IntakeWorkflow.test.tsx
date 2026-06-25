import React from 'react';
import { render, screen } from '@testing-library/react';
import IntakeWorkflow from '../../components/workflows/IntakeWorkflow';
import { AppProvider } from '../../store/AppContext';

// Mock the useApi module
jest.mock('../../hooks/useApi', () => ({
  uploadWorkbook: jest.fn(),
}));

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe('IntakeWorkflow', () => {
  it('renders the intake heading', () => {
    renderWithProvider(<IntakeWorkflow />);
    expect(screen.getByText('Workbook intake')).toBeTruthy();
  });

  it('renders the file drop area', () => {
    renderWithProvider(<IntakeWorkflow />);
    expect(screen.getByTestId('file-drop')).toBeTruthy();
  });

  it('renders Real API integration tag', () => {
    renderWithProvider(<IntakeWorkflow />);
    expect(screen.getByText('Real API integration')).toBeTruthy();
  });

  it('shows no upload status initially', () => {
    renderWithProvider(<IntakeWorkflow />);
    // No success notification should be visible at start
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('shows upload instructions', () => {
    renderWithProvider(<IntakeWorkflow />);
    expect(screen.getByText(/Drag and drop RVTools .xlsx/)).toBeTruthy();
  });
});
