import React, { useEffect } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NetworkPlanWorkflow from '../../components/workflows/NetworkPlanWorkflow';
import { AppProvider, defaultResources, useAppState } from '../../store/AppContext';

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

function InvalidNetworkResourcesSeed() {
  const { dispatch } = useAppState();
  useEffect(() => {
    dispatch({
      type: 'SET_RESOURCES',
      payload: {
        ...defaultResources,
        subnets: [{ ...defaultResources.subnets[0], cidr: 'not-a-cidr' }],
        networkComponents: [{
          ...defaultResources.networkComponents[0],
          attachment: '',
        }],
      },
    });
  }, [dispatch]);
  return null;
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

  it('renders network validation status for a clean plan', () => {
    renderWithProvider(<NetworkPlanWorkflow />);
    expect(screen.getByRole('region', { name: 'Network validation' })).toBeTruthy();
    expect(screen.getByText('No network plan validation findings.')).toBeTruthy();
  });

  it('renders network validation findings for invalid resources', async () => {
    renderWithProvider(
      <>
        <InvalidNetworkResourcesSeed />
        <NetworkPlanWorkflow />
      </>,
    );

    expect(await screen.findByText('Subnet CIDR "not-a-cidr" is not valid.')).toBeTruthy();
    expect(screen.getByText('public_gateway has no attachment or target selected.')).toBeTruthy();
    expect(screen.getByLabelText('Network validation findings')).toBeTruthy();
  });

  it('opens an existing network component for editing', async () => {
    renderWithProvider(
      <>
        <NetworkPlanWorkflow />
        <StateProbe />
      </>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Edit network component prod-public-gateway' }));

    expect(screen.getByTestId('network-plan-state').textContent).toContain(
      'assignment|component|component-public-gateway|prod-public-gateway|public_gateway|vpc-prod|prod-app-us-south-1',
    );
  });

  it('exposes network component edit actions with descriptive accessible names', () => {
    renderWithProvider(<NetworkPlanWorkflow />);

    expect(screen.getByRole('button', {
      name: 'Edit network component prod-public-gateway',
    })).toBeTruthy();
    expect(screen.getByRole('button', {
      name: 'Edit network component enterprise-transit-gateway',
    })).toBeTruthy();
  });
});
