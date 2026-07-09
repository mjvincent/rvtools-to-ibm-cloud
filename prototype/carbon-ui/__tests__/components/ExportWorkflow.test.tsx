import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExportWorkflow from '../../components/workflows/ExportWorkflow';
import { AppProvider, defaultResources, useAppState } from '../../store/AppContext';
import * as api from '../../hooks/useApi';
import type { AssignmentVm } from '../../types/network-planning';

jest.mock('../../hooks/useApi', () => ({
  saveNetworkPlan: jest.fn(),
  generateTerraform: jest.fn(),
  previewTerraform: jest.fn(),
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

function StateProbe() {
  const { state } = useAppState();
  return (
    <div data-testid="state-probe">
      {state.activeWorkflow}|{state.searchValue}|{state.selectedVmIds.join(',')}|{state.assignmentMode}
    </div>
  );
}

function SeedAssignments({ rows }: { rows: AssignmentVm[] }) {
  const { dispatch } = useAppState();
  React.useEffect(() => {
    dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: rows });
  }, [dispatch, rows]);
  return null;
}

function AssignmentProbe({ vmId }: { vmId: string }) {
  const { state } = useAppState();
  const row = state.assignmentRows.find((assignment) => assignment.id === vmId);
  return (
    <div data-testid="assignment-probe">
      {row ? `${row.subnet}|${row.securityGroup}|${row.storageTier}|${row.wave}|audit:${state.suggestionAudit.length}` : ''}
    </div>
  );
}

function renderWithProvider(ui: React.ReactElement) {
  return render(
    <AppProvider>
      <SeedProject>
        {ui}
        <StateProbe />
      </SeedProject>
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
    (api.previewTerraform as jest.Mock).mockResolvedValue({
      project_id: 'project-1',
      project_name: 'Export Project',
      files: [
        {
          path: 'README.md',
          category: 'Terraform',
          size_bytes: 35,
          content: '# Terraform Package: Export Project',
        },
        {
          path: 'main.tf',
          category: 'Terraform',
          size_bytes: 42,
          content: 'terraform {\n  required_version = ">= 1.0"\n}',
        },
        {
          path: 'decision-audit.csv',
          category: 'Migration handoff',
          size_bytes: 48,
          content: 'VM Name,Original Profile,Chosen Profile\napp-01,bx2-2x8,bx2-4x16\n',
        },
        {
          path: 'network-plan.json',
          category: 'Carbon state',
          size_bytes: 24,
          content: '{\n  "version": "1.0"\n}',
        },
      ],
    });
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
          'Quick Fix Type': 'exclude_vm',
          Field: 'Image Readiness',
          'Current Value': 'Blocked',
          Constraint: '',
        },
        {
          Severity: 'warning',
          Category: 'network_mapping',
          'Fix Category': 'Fix app planning',
          Subject: 'sample-web-01',
          Message: 'VM subnet mapping is blank.',
          Remediation: 'Review target subnet mapping before applying Terraform.',
          'Fix Location': 'VM Review tab > Subnet',
          'Suggested Action': 'Select a target subnet for this VM.',
          'Valid Options': '',
          'Recommended Option': '',
          'Quick Fix Type': '',
          Field: 'Subnet',
          'Current Value': '',
          Constraint: 'Expected module.networking.<network>_id output.',
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
    expect(screen.getByText('Export checklist')).toBeTruthy();
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
    (api.runProjectPreflight as jest.Mock).mockResolvedValueOnce({
      project_id: 'project-1',
      project_name: 'Export Project',
      summary: { blockers: 0, warnings: 1, info: 0, total: 1 },
      findings: [],
    });
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Download Terraform ZIP'));

    await waitFor(() => expect(api.saveNetworkPlan).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.runProjectPreflight).toHaveBeenCalledWith('project-1'));
    await waitFor(() => expect(api.generateTerraform).toHaveBeenCalledWith('project-1'));
    const [, payload] = (api.saveNetworkPlan as jest.Mock).mock.calls[0];
    expect(payload.vm_assignments).toHaveLength(3);
    expect(payload.metadata.project_name).toBe('Export Project');
    expect(screen.getByText('Terraform ZIP downloaded with 1 warning(s).')).toBeTruthy();
  });

  it('blocks Terraform ZIP download when export preflight has blockers', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Download Terraform ZIP'));

    await waitFor(() => expect(api.runProjectPreflight).toHaveBeenCalledWith('project-1'));
    expect(api.generateTerraform).not.toHaveBeenCalled();
    expect(screen.getByText('Terraform ZIP blocked by 1 preflight blocker(s). Resolve or route the findings below, then try again.')).toBeTruthy();
    expect(screen.getByText('Package preflight')).toBeTruthy();
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
    expect(screen.getByText('Review scope decision')).toBeTruthy();
  });

  it('saves the network plan before rendering the package preview', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Preview Terraform'));

    await waitFor(() => expect(api.saveNetworkPlan).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.previewTerraform).toHaveBeenCalledWith('project-1'));
    expect(screen.getByText('Package preview')).toBeTruthy();
    expect(screen.getByText('4 generated file(s) from the saved Carbon network plan.')).toBeTruthy();
    expect(screen.getByLabelText('Terraform preview README.md').textContent).toContain('Terraform Package');

    await userEvent.click(screen.getByRole('button', { name: /main.tf/ }));
    expect(screen.getByLabelText('Terraform preview main.tf').textContent).toContain('required_version');

    await userEvent.selectOptions(screen.getByLabelText('Package section'), 'Migration handoff');
    expect(screen.getByRole('button', { name: /decision-audit.csv/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /network-plan.json/ })).toBeNull();

    await userEvent.selectOptions(screen.getByLabelText('Package section'), 'All');
    await userEvent.type(screen.getByLabelText('Search package files'), 'network');
    expect(screen.getByRole('button', { name: /network-plan.json/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /decision-audit.csv/ })).toBeNull();

    await userEvent.click(screen.getByText('Close preview'));
    expect(screen.queryByText('Package preview')).toBeNull();
    expect(screen.queryByLabelText('Terraform preview README.md')).toBeNull();
  });

  it('downloads the selected package preview file', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Preview Terraform'));
    await waitFor(() => expect(api.previewTerraform).toHaveBeenCalledWith('project-1'));

    await userEvent.click(screen.getByText('Show handoff CSVs'));
    expect(screen.getByRole('button', { name: /decision-audit.csv/ })).toBeTruthy();
    expect(screen.getByLabelText('Terraform preview decision-audit.csv').textContent).toContain('Original Profile');

    await userEvent.click(screen.getByText('Download selected'));

    await waitFor(() => expect(window.URL.createObjectURL).toHaveBeenCalledTimes(1));
    const blob = (window.URL.createObjectURL as jest.Mock).mock.calls[0][0] as Blob;
    await expect(readBlobText(blob)).resolves.toContain('VM Name,Original Profile,Chosen Profile');
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:terraform');
  });

  it('routes preflight findings to the right review workflow', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Run preflight'));
    await waitFor(() => expect(screen.getByText('Open remediation')).toBeTruthy());
    await userEvent.click(screen.getByText('Open remediation'));

    expect(screen.getByTestId('state-probe').textContent).toBe(
      'remediation|db-01|sample-db-01|network',
    );
  });

  it('routes network preflight findings to assignment mode with the affected VM selected', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Run preflight'));
    await waitFor(() => expect(screen.getByText('Open network assignment')).toBeTruthy());
    await userEvent.click(screen.getByText('Open network assignment'));

    expect(screen.getByTestId('state-probe').textContent).toBe(
      'assignment|web-01|sample-web-01|network',
    );
  });

  it('routes resolve next issue to the first local assignment gap', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Resolve next issue'));

    expect(screen.getByTestId('state-probe').textContent).toBe(
      'assignment|app-01|sample-app-01|network',
    );
  });

  it('prioritizes preflight blockers when resolving the next issue', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Run preflight'));
    await waitFor(() => expect(screen.getByText('Package preflight')).toBeTruthy());
    await userEvent.click(screen.getByText('Resolve next issue'));

    expect(screen.getByTestId('state-probe').textContent).toBe(
      'remediation|db-01|sample-db-01|network',
    );
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

  it('downloads an export readiness report with checklist, gaps, and package inventory', async () => {
    renderWithProvider(<ExportWorkflow />);

    await userEvent.click(screen.getByText('Download readiness report'));

    await waitFor(() => expect(window.URL.createObjectURL).toHaveBeenCalledTimes(1));
    const blob = (window.URL.createObjectURL as jest.Mock).mock.calls[0][0] as Blob;
    const payload = JSON.parse(await readBlobText(blob));
    expect(payload.schema_version).toBe('carbon-export-readiness-report-1.0');
    expect(payload.project.name).toBe('Export Project');
    expect(payload.readiness.status).toBe('Needs review');
    expect(payload.readiness.checklist).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: 'VM assignments complete', complete: false }),
      ]),
    );
    expect(payload.readiness.planning_gaps['Missing subnet assignments']).toBe(3);
    expect(payload.package_inventory.total_files).toBe(37);
    expect(payload.suggestions.available.length).toBeGreaterThan(0);
    expect(screen.getByText('Export readiness report downloaded.')).toBeTruthy();
  });

  it('imports planning-state JSON before saving Terraform', async () => {
    (api.runProjectPreflight as jest.Mock).mockResolvedValueOnce({
      project_id: 'project-1',
      project_name: 'Export Project',
      summary: { blockers: 0, warnings: 0, info: 0, total: 0 },
      findings: [],
    });
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

  it('applies an inferred assignment from a similarly named VM', async () => {
    const rows: AssignmentVm[] = [
      {
        id: 'app-01',
        name: 'app-01',
        image: 'Ready',
        imageReasons: '',
        migration: 'Ready',
        migrationReasons: '',
        memory: 'Ready',
        memoryReasons: '',
        networkReadiness: 'Ready',
        networkReasons: '',
        profile: 'bx2-2x8',
        overrideProfile: '',
        storageTier: '5iops-tier',
        overrideStorageTier: '',
        network: 'app-net',
        subnet: 'prod-app-us-south-1',
        securityGroup: 'sg-app-private',
        power: 'poweredOn',
        owner: 'App owner',
        application: 'App tier',
        wave: 'Wave 1',
        cutoverGroup: 'app-cutover',
        priority: '',
        dependencyGroup: '',
      },
      {
        id: 'app-02',
        name: 'app-02',
        image: 'Ready',
        imageReasons: '',
        migration: 'Ready',
        migrationReasons: '',
        memory: 'Ready',
        memoryReasons: '',
        networkReadiness: 'Ready',
        networkReasons: '',
        profile: 'bx2-2x8',
        overrideProfile: '',
        storageTier: '5iops-tier',
        overrideStorageTier: '',
        network: 'app-net',
        subnet: '',
        securityGroup: '',
        power: 'poweredOn',
        owner: 'App owner',
        application: 'App tier',
        wave: '',
        cutoverGroup: 'app-cutover',
        priority: '',
        dependencyGroup: '',
      },
    ];
    render(
      <AppProvider>
        <SeedProject>
          <SeedAssignments rows={rows} />
          <ExportWorkflow />
          <AssignmentProbe vmId="app-02" />
        </SeedProject>
      </AppProvider>,
    );

    await waitFor(() => expect(screen.getByText('Suggested assignment fixes')).toBeTruthy());
    expect(screen.getAllByText('High confidence').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Same application: App tier/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Same source network: app-net/).length).toBeGreaterThan(0);
    await userEvent.click(screen.getAllByText('Apply suggestion')[0]);

    await waitFor(() =>
      expect(screen.getByTestId('assignment-probe').textContent).toContain('prod-app-us-south-1'),
    );
    expect(screen.getByTestId('assignment-probe').textContent).toContain('audit:1');
    expect(screen.getByText('Applied suggested subnet for app-02. Save the project to persist it.')).toBeTruthy();
    expect(screen.getByText('Suggestion audit')).toBeTruthy();
    expect(screen.getByText('(blank) to prod-app-us-south-1')).toBeTruthy();

    await userEvent.click(screen.getByText('Undo suggestion'));

    await waitFor(() =>
      expect(screen.getByTestId('assignment-probe').textContent).toContain('||5iops-tier||audit:1'),
    );
    expect(screen.getByTestId('assignment-probe').textContent).not.toContain('prod-app-us-south-1');
    expect(screen.getByText('Reverted')).toBeTruthy();
    expect(screen.getByText('Reverted suggested subnet change for app-02. Save the project to persist it.')).toBeTruthy();
  });

  it('bulk applies high-confidence inferred assignments and audits each change', async () => {
    const rows: AssignmentVm[] = [
      {
        id: 'app-01',
        name: 'app-01',
        image: 'Ready',
        imageReasons: '',
        migration: 'Ready',
        migrationReasons: '',
        memory: 'Ready',
        memoryReasons: '',
        networkReadiness: 'Ready',
        networkReasons: '',
        profile: 'bx2-2x8',
        overrideProfile: '',
        storageTier: '5iops-tier',
        overrideStorageTier: '',
        network: 'app-net',
        subnet: 'prod-app-us-south-1',
        securityGroup: 'sg-app-private',
        power: 'poweredOn',
        owner: 'App owner',
        application: 'App tier',
        wave: 'Wave 1',
        cutoverGroup: 'app-cutover',
        priority: '',
        dependencyGroup: '',
      },
      {
        id: 'app-02',
        name: 'app-02',
        image: 'Ready',
        imageReasons: '',
        migration: 'Ready',
        migrationReasons: '',
        memory: 'Ready',
        memoryReasons: '',
        networkReadiness: 'Ready',
        networkReasons: '',
        profile: 'bx2-2x8',
        overrideProfile: '',
        storageTier: '5iops-tier',
        overrideStorageTier: '',
        network: 'app-net',
        subnet: '',
        securityGroup: '',
        power: 'poweredOn',
        owner: 'App owner',
        application: 'App tier',
        wave: '',
        cutoverGroup: 'app-cutover',
        priority: '',
        dependencyGroup: '',
      },
    ];
    render(
      <AppProvider>
        <SeedProject>
          <SeedAssignments rows={rows} />
          <ExportWorkflow />
          <AssignmentProbe vmId="app-02" />
        </SeedProject>
      </AppProvider>,
    );

    await waitFor(() => expect(screen.getByText('Apply high-confidence suggestions')).toBeTruthy());
    await userEvent.click(screen.getByText('Apply high-confidence suggestions'));

    await waitFor(() =>
      expect(screen.getByTestId('assignment-probe').textContent).toContain('prod-app-us-south-1|sg-app-private|5iops-tier|Wave 1'),
    );
    expect(screen.getByTestId('assignment-probe').textContent).toContain('audit:3');
    expect(screen.getByText('Applied 3 suggested assignment(s), including 3 high-confidence item(s). Save the project to persist them.')).toBeTruthy();
  });
});
