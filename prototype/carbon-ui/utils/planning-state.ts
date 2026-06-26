import type {
  AssignmentVm,
  NetworkPlanningState,
  ResourceState,
  VmNetworkAssignment,
  WorkbookSummary,
} from '../types/network-planning';

type ApiNetworkPlanBody = {
  version: string;
  vpcs: unknown[];
  subnets: unknown[];
  security_groups: unknown[];
  storage_profiles: unknown[];
  waves: unknown[];
  network_components: unknown[];
  vm_assignments: ApiVmAssignmentPayload[];
  metadata: Record<string, unknown>;
};

export type ApiVmAssignmentPayload = {
  vm_key: string;
  vm_name: string;
  primary_subnet_id: string;
  primary_security_group_id: string;
  secondary_nics: unknown[];
  storage_profile_id: string | null;
  wave_id: string | null;
  excluded: boolean;
  exclusion_reason: string | null;
  cpu_count?: number;
  memory_gb?: number;
  ibm_profile?: string | null;
  override_profile?: string | null;
  boot_disk_gb?: number;
  guest_os?: string | null;
};

function valueFrom<T extends Record<string, unknown>>(item: T, camel: string, snake: string) {
  return item[camel] ?? item[snake];
}

function findResourceId<T extends { id: string; name: string; label?: string }>(
  resources: T[],
  value: string | undefined,
) {
  if (!value) return '';
  return resources.find((resource) =>
    resource.id === value || resource.name === value || resource.label === value,
  )?.id || value;
}

function normalizeArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

function normalizeResources(plan: Partial<NetworkPlanningState> | Record<string, unknown>): ResourceState {
  return {
    vpcs: normalizeArray(valueFrom(plan, 'vpcs', 'vpcs')),
    subnets: normalizeArray(valueFrom(plan, 'subnets', 'subnets')),
    securityGroups: normalizeArray(valueFrom(plan, 'securityGroups', 'security_groups')),
    storageProfiles: normalizeArray(valueFrom(plan, 'storageProfiles', 'storage_profiles')),
    waves: normalizeArray(valueFrom(plan, 'waves', 'waves')),
    networkComponents: normalizeArray(valueFrom(plan, 'networkComponents', 'network_components')),
  } as ResourceState;
}

export function vmAssignmentsFromRows(
  rows: AssignmentVm[],
  resources: ResourceState,
): ApiVmAssignmentPayload[] {
  return rows.map((row) => ({
    vm_key: row.id,
    vm_name: row.name,
    primary_subnet_id: findResourceId(resources.subnets, row.subnet),
    primary_security_group_id: findResourceId(resources.securityGroups, row.securityGroup),
    secondary_nics: [],
    storage_profile_id: findResourceId(resources.storageProfiles, row.storageLabel || row.overrideStorageTier || row.storageTier) || null,
    wave_id: findResourceId(resources.waves, row.wave) || null,
    excluded: false,
    exclusion_reason: null,
    ibm_profile: row.profile || null,
    override_profile: row.overrideProfile || null,
  }));
}

export function buildNetworkPlanBody(params: {
  resources: ResourceState;
  assignmentRows: AssignmentVm[];
  projectName: string;
  summary?: WorkbookSummary | null;
}): ApiNetworkPlanBody {
  const now = new Date().toISOString();
  return {
    version: '1.0',
    vpcs: params.resources.vpcs,
    subnets: params.resources.subnets,
    security_groups: params.resources.securityGroups,
    storage_profiles: params.resources.storageProfiles || [],
    waves: params.resources.waves || [],
    network_components: params.resources.networkComponents || [],
    vm_assignments: vmAssignmentsFromRows(params.assignmentRows, params.resources),
    metadata: {
      project_name: params.projectName.trim(),
      target_region: params.resources.vpcs[0]?.region || 'us-south',
      target_zone: params.resources.subnets[0]?.zone || 'us-south-1',
      deployment_target: 'plain_cli',
      backend_type: 'local',
      created_by: null,
      created_at: now,
      updated_at: now,
      rvtools_filename: params.summary?.filename || null,
      rvtools_uploaded_at: null,
    },
  };
}

export function resourcesFromNetworkPlan(plan: unknown): ResourceState {
  if (!plan || typeof plan !== 'object') {
    return normalizeResources({});
  }
  return normalizeResources(plan as Record<string, unknown>);
}

export function rowsFromNetworkPlan(
  plan: unknown,
  currentRows: AssignmentVm[],
): AssignmentVm[] {
  if (!plan || typeof plan !== 'object') return currentRows;
  const record = plan as Record<string, unknown>;
  const resources = resourcesFromNetworkPlan(plan);
  const assignments = normalizeArray<Record<string, unknown>>(
    valueFrom(record, 'vmAssignments', 'vm_assignments'),
  );
  if (assignments.length === 0) return currentRows;

  return currentRows.map((row) => {
    const assignment = assignments.find((candidate) =>
      valueFrom(candidate, 'vmKey', 'vm_key') === row.id,
    );
    if (!assignment) return row;
    const subnetId = String(valueFrom(assignment, 'primarySubnetId', 'primary_subnet_id') || '');
    const sgId = String(valueFrom(assignment, 'primarySecurityGroupId', 'primary_security_group_id') || '');
    const storageId = String(valueFrom(assignment, 'storageProfileId', 'storage_profile_id') || '');
    const waveId = String(valueFrom(assignment, 'waveId', 'wave_id') || '');
    return {
      ...row,
      subnet: resources.subnets.find((subnet) => subnet.id === subnetId)?.name || subnetId || row.subnet,
      securityGroup: resources.securityGroups.find((sg) => sg.id === sgId)?.name || sgId || row.securityGroup,
      storageLabel: resources.storageProfiles.find((storage) => storage.id === storageId)?.label || row.storageLabel,
      overrideStorageTier: resources.storageProfiles.find((storage) => storage.id === storageId)?.tier || row.overrideStorageTier,
      wave: resources.waves.find((wave) => wave.id === waveId)?.name || waveId || row.wave,
    };
  });
}

