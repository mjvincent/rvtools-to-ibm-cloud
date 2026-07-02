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
  override_profile_reason?: string | null;
  storage_tier?: string | null;
  override_storage_tier?: string | null;
  override_storage_tier_reason?: string | null;
  network?: string | null;
  owner?: string | null;
  application?: string | null;
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

function normalizeBoolean(value: unknown, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') {
    return ['true', 'yes', '1'].includes(value.toLowerCase());
  }
  return Boolean(value);
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
    excluded: Boolean(row.excluded),
    exclusion_reason: row.exclusionReason || null,
    ibm_profile: row.profile || null,
    override_profile: row.overrideProfile || null,
    override_profile_reason: row.overrideProfileReason || null,
    storage_tier: row.storageTier || null,
    override_storage_tier: row.overrideStorageTier || null,
    override_storage_tier_reason: row.overrideStorageTierReason || null,
    network: row.network || null,
    owner: row.owner || null,
    application: row.application || null,
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

export function exportNetworkPlanJson(params: {
  resources: ResourceState;
  assignmentRows: AssignmentVm[];
  projectName: string;
  summary?: WorkbookSummary | null;
}) {
  return JSON.stringify(buildNetworkPlanBody(params), null, 2);
}

export function parseNetworkPlanJson(text: string): ApiNetworkPlanBody {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error('Planning state file must be valid JSON.');
  }
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Planning state file must contain a network plan object.');
  }
  const plan = parsed as Partial<ApiNetworkPlanBody>;
  if (!Array.isArray(plan.vpcs) || !Array.isArray(plan.subnets)) {
    throw new Error('Planning state file is missing VPC or subnet resources.');
  }
  if (!Array.isArray(plan.security_groups) && !Array.isArray((plan as any).securityGroups)) {
    throw new Error('Planning state file is missing security group resources.');
  }
  if (!Array.isArray(plan.vm_assignments) && !Array.isArray((plan as any).vmAssignments)) {
    throw new Error('Planning state file is missing VM assignments.');
  }
  return parsed as ApiNetworkPlanBody;
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
    const overrideProfile = String(valueFrom(assignment, 'overrideProfile', 'override_profile') || '');
    const overrideProfileReason = String(valueFrom(assignment, 'overrideProfileReason', 'override_profile_reason') || '');
    const overrideStorageTierReason = String(valueFrom(assignment, 'overrideStorageTierReason', 'override_storage_tier_reason') || '');
    const storageTier = String(valueFrom(assignment, 'storageTier', 'storage_tier') || '');
    const owner = String(valueFrom(assignment, 'owner', 'owner') || '');
    const application = String(valueFrom(assignment, 'application', 'application') || '');
    const network = String(valueFrom(assignment, 'network', 'network') || '');
    const excluded = normalizeBoolean(
      valueFrom(assignment, 'excluded', 'excluded'),
      Boolean(row.excluded),
    );
    const exclusionReason = String(valueFrom(assignment, 'exclusionReason', 'exclusion_reason') || '');
    return {
      ...row,
      subnet: resources.subnets.find((subnet) => subnet.id === subnetId)?.name || subnetId || row.subnet,
      securityGroup: resources.securityGroups.find((sg) => sg.id === sgId)?.name || sgId || row.securityGroup,
      storageLabel: resources.storageProfiles.find((storage) => storage.id === storageId)?.label || row.storageLabel,
      overrideStorageTier: resources.storageProfiles.find((storage) => storage.id === storageId)?.tier || row.overrideStorageTier,
      wave: resources.waves.find((wave) => wave.id === waveId)?.name || waveId || row.wave,
      overrideProfile: overrideProfile || row.overrideProfile,
      overrideProfileReason: overrideProfileReason || row.overrideProfileReason,
      overrideStorageTierReason: overrideStorageTierReason || row.overrideStorageTierReason,
      storageTier: storageTier || row.storageTier,
      owner: owner || row.owner,
      application: application || row.application,
      network: network || row.network,
      excluded,
      exclusionReason: exclusionReason || row.exclusionReason,
    };
  });
}
