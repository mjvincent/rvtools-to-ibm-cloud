import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExportWorkflow from '../../components/workflows/ExportWorkflow';
import { AppProvider, useAppState } from '../../store/AppContext';
import * as api from '../../hooks/useApi';

jest.mock('../../hooks/useApi', () => ({
  saveNetworkPlan: jest.fn(),
  generateTerraform: jest.fn(),
}));

function SeedProject({ children }: { children: React.ReactNode }) {
  const { dispatch } = useAppState();
  React.useEffect(() => {
    dispatch({ type: 'SET_SELECTED_PROJECT_ID', payload: 'project-1' });
    dispatch({ type: 'SET_PROJECT_NAME', payload: 'Export Project' });
  }, [dispatch]);
  return <>{children}</>;
}

function renderWithProvider(ui: React.ReactElement) {
  return render(
    <AppProvider>
      <SeedProject>{ui}</SeedProject>
    </AppProvider>,
  );
}

describe('ExportWorkflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.saveNetworkPlan as jest.Mock).mockResolvedValue(undefined);
    (api.generateTerraform as jest.Mock).mockResolvedValue(new Blob(['zip']));
    Object.defineProperty(window.URL, 'createObjectURL', {
      configurable: true,
      value: jest.fn(() => 'blob:terraform'),
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      configurable: true,
      value: jest.fn(),
    });
  });

  it('renders export readiness findings', () => {
    renderWithProvider(<ExportWorkflow />);
    expect(screen.getByText('Export readiness')).toBeTruthy();
    expect(screen.getByText('Missing subnet assignments')).toBeTruthy();
  });

  it('renders ZIP package parity contents before download', () => {
    renderWithProvider(<ExportWorkflow />);

    expect(screen.getByText('Package contents')).toBeTruthy();
    expect(screen.getByText('35 files are included in the generated ZIP.')).toBeTruthy();
    expect(screen.getByText('Streamlit handoff parity')).toBeTruthy();
    expect(screen.getByText('Terraform project')).toBeTruthy();
    expect(screen.getByText('Migration handoff')).toBeTruthy();
    expect(screen.getByText('Carbon state')).toBeTruthy();
    expect(screen.getByText('decision-audit.csv')).toBeTruthy();
    expect(screen.getByText('network-plan.json')).toBeTruthy();
  });

  it('saves the network plan before downloading Terraform ZIP', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Download Terraform ZIP'));

    await waitFor(() => expect(api.saveNetworkPlan).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.generateTerraform).toHaveBeenCalledWith('project-1'));
    const [, payload] = (api.saveNetworkPlan as jest.Mock).mock.calls[0];
    expect(payload.vm_assignments).toHaveLength(3);
    expect(payload.metadata.project_name).toBe('Export Project');
  });
});
