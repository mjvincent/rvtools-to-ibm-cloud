import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NetworkPlanWorkflow from '../../components/workflows/NetworkPlanWorkflow';
import { AppProvider, useAppState } from '../../store/AppContext';

jest.mock('../../hooks/useApi', () => ({
  generateTerraform: jest.fn(),
  saveNetworkPlan: jest.fn(),
}));

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

function StateProbe() {
  const { state } = useAppState();
  return (
    <div data-testid="network-plan-state">
      {[
        state.activeWorkflow,
        state.bucketModal,
        state.bucketDraft.id || '',
        state.bucketDraft.name || '',
        state.bucketDraft.type || '',
        state.bucketDraft.vpcId || '',
        state.bucketDraft.attachment || '',
      ].join('|')}
    </div>
  );
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

  it('opens an existing network component for editing', async () => {
    renderWithProvider(
      <>
        <NetworkPlanWorkflow />
        <StateProbe />
      </>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Edit prod-public-gateway' }));

    expect(screen.getByTestId('network-plan-state').textContent).toContain(
      'assignment|component|component-public-gateway|prod-public-gateway|public_gateway|vpc-prod|prod-app-us-south-1',
    );
  });
});
