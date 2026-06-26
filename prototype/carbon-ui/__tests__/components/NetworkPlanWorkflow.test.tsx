import React from 'react';
import { render, screen } from '@testing-library/react';
import NetworkPlanWorkflow from '../../components/workflows/NetworkPlanWorkflow';
import { AppProvider } from '../../store/AppContext';

jest.mock('../../hooks/useApi', () => ({
  generateTerraform: jest.fn(),
  saveNetworkPlan: jest.fn(),
}));

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe('NetworkPlanWorkflow', () => {
  it('renders network component creation affordance', () => {
    renderWithProvider(<NetworkPlanWorkflow />);
    expect(screen.getByRole('button', { name: 'Create network component' })).toBeTruthy();
  });

  it('renders the generated network diagram', () => {
    renderWithProvider(<NetworkPlanWorkflow />);
    expect(screen.getByLabelText('Generated network diagram')).toBeTruthy();
  });
});

