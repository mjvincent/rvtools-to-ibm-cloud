import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExportWorkflow from '../../components/workflows/ExportWorkflow';
import { AppProvider, defaultResources, useAppState } from '../../store/AppContext';
import * as api from '../../hooks/useApi';

jest.mock('../../hooks/useApi', () => ({
  saveNetworkPlan: jest.fn(),
  generateTerraform: jest.fn(),
  runProjectPreflight: jest.fn(),
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

function readBlobText(blob: Blob) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('Could not read blob.'));
    reader.readAsText(blob);
  });
}

describe('ExportWorkflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.saveNetworkPlan as jest.Mock).mockResolvedValue(undefined);
    (api.generateTerraform as jest.Mock).mockResolvedValue(new Blob(['zip']));
    (api.runProjectPreflight as jest.Mock).mockResolvedValue({
      project_id: 'project-1',
      project_name: 'Export Project',
      summary: { blockers: 1, warnings: 2, info: 0, total: 3 },
      findings: [
        {
          Severity: 'blocker',
          Category: 'readiness',
          'Fix Category': 'Fix source RVTools/vSphere data',
          Subject: 'sample-db-01',
          Message: 'Image readiness is blocked.',
          Remediation: 'Resolve the source finding.',
          'Fix Location': 'Source',
          'Suggested Action': 'Review source VM.',
          'Valid Options': '',
          'Recommended Option': '',
          'Quick Fix Type': '',
          Field: 'Image Readiness',
          'Current Value': 'Blocked',
          Constraint: '',
        },
      ],
    });
    Object.defineProperty(window.URL, 'createObjectURL', {
      configurable: true,
      value: jest.fn(() => 'blob:terraform'),
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      configurable: true,
      value: jest.fn(),
    });
    jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders export readiness findings', () => {
    renderWithProvider(<ExportWorkflow />);
    expect(screen.getByText('Export readiness')).toBeTruthy();
    expect(screen.getByText('Missing subnet assignments')).toBeTruthy();
  });

  it('renders ZIP package parity status before download', () => {
    renderWithProvider(<ExportWorkflow />);

    expect(screen.getByText('Package parity status')).toBeTruthy();
    expect(screen.getByText('37 files are included in the generated ZIP.')).toBeTruthy();
    expect(screen.getByText('Streamlit handoff set covered')).toBeTruthy();
    expect(screen.getByText('Handoff parity')).toBeTruthy();
    expect(screen.getByText('20/20')).toBeTruthy();
    expect(screen.getByText('Terraform layout')).toBeTruthy();
    expect(screen.getByText('16/16')).toBeTruthy();
    expect(screen.getByText('Carbon additions')).toBeTruthy();
    expect(screen.getByText('Terraform project')).toBeTruthy();
    expect(screen.getByText('Migration handoff')).toBeTruthy();
    expect(screen.getByText('Carbon state')).toBeTruthy();
    expect(screen.getByText('terraform.tfvars.example')).toBeTruthy();
    expect(screen.getByText('provider.tf')).toBeTruthy();
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

  it('saves the network plan before running backend preflight', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Run preflight'));

    await waitFor(() => expect(api.saveNetworkPlan).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.runProjectPreflight).toHaveBeenCalledWith('project-1'));
    expect(screen.getByText('Package preflight')).toBeTruthy();
    expect(screen.getByText('3 backend finding(s) from the saved Carbon network plan.')).toBeTruthy();
    expect(screen.getByText('1 blocker(s)')).toBeTruthy();
    expect(screen.getByText('2 warning(s)')).toBeTruthy();
    expect(screen.getByText('sample-db-01')).toBeTruthy();
    expect(screen.getByText('Image readiness is blocked.')).toBeTruthy();
  });

  it('downloads the current planning-state JSON', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Export planning JSON'));

    await waitFor(() => expect(window.URL.createObjectURL).toHaveBeenCalledTimes(1));
    const blob = (window.URL.createObjectURL as jest.Mock).mock.calls[0][0] as Blob;
    const payload = JSON.parse(await readBlobText(blob));
    expect(payload.vm_assignments).toHaveLength(3);
    expect(payload.metadata.project_name).toBe('Export Project');
    expect(screen.getByText('Planning state JSON downloaded.')).toBeTruthy();
  });

  it('imports planning-state JSON before saving Terraform', async () => {
    renderWithProvider(<ExportWorkflow />);
    const importedPlan = {
      version: '1.0',
      vpcs: defaultResources.vpcs,
      subnets: defaultResources.subnets,
      security_groups: defaultResources.securityGroups,
      storage_profiles: defaultResources.storageProfiles,
      waves: defaultResources.waves,
      network_components: defaultResources.networkComponents,
      vm_assignments: [
        {
          vm_key: 'sample-app-01',
          vm_name: 'app-01',
          primary_subnet_id: 'subnet-db',
          primary_security_group_id: 'sg-db',
          secondary_nics: [],
          storage_profile_id: 'storage-db',
          wave_id: 'wave-2',
          excluded: false,
          exclusion_reason: null,
          override_profile: 'mx2-16x128',
          override_profile_reason: 'Memory validation complete',
          storage_tier: '10iops-tier',
          override_storage_tier_reason: 'Database latency target',
          owner: 'DB owner',
          application: 'Database',
          network: 'db-net',
        },
      ],
      metadata: {
        project_name: 'Imported Project',
        target_region: 'us-south',
        target_zone: 'us-south-1',
      },
    };
    const file = new File([JSON.stringify(importedPlan)], 'planning-state.json', {
      type: 'application/json',
    });

    await userEvent.upload(screen.getByLabelText('Import planning state JSON'), file);
    await waitFor(() =>
      expect(screen.getByText('Imported planning state from planning-state.json. Review and save the project to persist it.')).toBeTruthy(),
    );
    await userEvent.click(screen.getByText('Download Terraform ZIP'));

    await waitFor(() => expect(api.saveNetworkPlan).toHaveBeenCalledTimes(1));
    const [, payload] = (api.saveNetworkPlan as jest.Mock).mock.calls[0];
    expect(payload.vm_assignments[0]).toMatchObject({
      primary_subnet_id: 'subnet-db',
      primary_security_group_id: 'sg-db',
      storage_profile_id: 'storage-db',
      wave_id: 'wave-2',
      override_profile: 'mx2-16x128',
      override_profile_reason: 'Memory validation complete',
      owner: 'DB owner',
      application: 'Database',
      network: 'db-net',
    });
  });
});
