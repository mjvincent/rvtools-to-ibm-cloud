/**
 * Network Planning Schema v1.0
 *
 * This schema defines the structure for network planning state
 * that bridges Carbon UI planning and Terraform generation.
 */

export const SCHEMA_VERSION = '1.0';

// Core Types
export type NetworkPlanningState = {
  version: string;
  vpcs: VpcBucket[];
  subnets: SubnetBucket[];
  securityGroups: SecurityBucket[];
  storageProfiles: StorageBucket[];
  waves: WaveBucket[];
  networkComponents: NetworkComponent[];
  vmAssignments: VmNetworkAssignment[];
  metadata: PlanningMetadata;
};

export type VpcBucket = {
  id: string;
  name: string;
  label: string;
  region: string;
  addressPrefixMode: 'manual' | 'auto';
  addressPrefixes: AddressPrefix[];
  resourceGroupId?: string;
  tags: Record<string, string>;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type AddressPrefix = {
  id: string;
  name: string;
  cidr: string;
  zone: string;
  isDefault: boolean;
};

export type SubnetBucket = {
  id: string;
  name: string;
  label: string;
  vpcId: string;
  zone: string;
  cidr: string;
  purpose: string;
  sourceNetwork?: string;
  publicGateway: boolean;
  publicGatewayId?: string;
  aclId?: string;
  routeTableId?: string;
  ipv4CidrCount?: number;
  tags: Record<string, string>;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type SecurityBucket = {
  id: string;
  name: string;
  label: string;
  vpcId: string;
  purpose: string;
  rules: SecurityRule[];
  tags: Record<string, string>;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type SecurityRule = {
  id: string;
  direction: 'inbound' | 'outbound';
  protocol: 'tcp' | 'udp' | 'icmp' | 'all';
  portMin?: number;
  portMax?: number;
  source?: string;
  destination?: string;
  description: string;
};

export type StorageBucket = {
  id: string;
  name: string;
  label: string;
  tier: string;
  iopsIntent: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type WaveBucket = {
  id: string;
  name: string;
  owner: string;
  targetWindow: string;
  priority: 'high' | 'medium' | 'low';
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type NetworkComponent = {
  id: string;
  name: string;
  label: string;
  type: NetworkComponentType;
  vpcId: string;
  subnetId?: string;
  attachment: string;
  config: Record<string, any>;
  tags: Record<string, string>;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type NetworkComponentType =
  | 'public_gateway'
  | 'vpn_gateway'
  | 'load_balancer'
  | 'vpe_gateway'
  | 'floating_ip'
  | 'route_table'
  | 'acl';

export type VmNetworkAssignment = {
  vmKey: string;
  vmName: string;
  primarySubnetId: string;
  primarySecurityGroupId: string;
  secondaryNics: SecondaryNic[];
  storageProfileId?: string;
  waveId?: string;
  excluded: boolean;
  exclusionReason?: string;
  // Compute specifications for VSI generation
  cpuCount?: number;
  memoryGb?: number;
  ibmProfile?: string;
  overrideProfile?: string;
  overrideProfileReason?: string;
  // Boot disk specifications
  bootDiskGb?: number;
  // Custom image reference
  customImageId?: string;
  guestOs?: string;
};

export type SecondaryNic = {
  id: string;
  subnetId: string;
  securityGroupId: string;
  order: number;
  sourceNetwork?: string;
};

export type PlanningMetadata = {
  projectName: string;
  targetRegion: string;
  targetZone: string;
  deploymentTarget: 'plain_cli' | 'schematics';
  sshPublicKey?: string;
  sshKeyName?: string;
  resourceGroupId?: string;
  backendType: 'local' | 's3' | 'cos';
  createdBy?: string;
  createdAt: string;
  updatedAt: string;
  rvtoolsFilename?: string;
  rvtoolsUploadedAt?: string;
};

// Helper Functions
export function createEmptyNetworkPlan(): NetworkPlanningState {
  return {
    version: SCHEMA_VERSION,
    vpcs: [],
    subnets: [],
    securityGroups: [],
    storageProfiles: [],
    waves: [],
    networkComponents: [],
    vmAssignments: [],
    metadata: {
      projectName: '',
      targetRegion: 'us-south',
      targetZone: 'us-south-1',
      deploymentTarget: 'plain_cli',
      backendType: 'local',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  };
}

export function createInitialNetworkPlan(projectName: string): NetworkPlanningState {
  const now = new Date().toISOString();
  const vpcId = crypto.randomUUID();
  const subnetId = crypto.randomUUID();
  const sgId = crypto.randomUUID();

  return {
    version: SCHEMA_VERSION,
    vpcs: [
      {
        id: vpcId,
        name: 'migration-vpc',
        label: 'Migration VPC',
        region: 'us-south',
        addressPrefixMode: 'manual',
        addressPrefixes: [
          {
            id: crypto.randomUUID(),
            name: 'zone-1-prefix',
            cidr: '10.240.0.0/16',
            zone: 'us-south-1',
            isDefault: true,
          },
        ],
        tags: {},
        notes: '',
        createdAt: now,
        updatedAt: now,
      },
    ],
    subnets: [
      {
        id: subnetId,
        name: 'default-subnet',
        label: 'Default Subnet',
        vpcId,
        zone: 'us-south-1',
        cidr: '10.240.10.0/24',
        purpose: 'general',
        publicGateway: false,
        tags: {},
        notes: '',
        createdAt: now,
        updatedAt: now,
      },
    ],
    securityGroups: [
      {
        id: sgId,
        name: 'default-sg',
        label: 'Default Security Group',
        vpcId,
        purpose: 'general',
        rules: [
          {
            id: crypto.randomUUID(),
            direction: 'outbound',
            protocol: 'all',
            description: 'Allow all outbound',
          },
        ],
        tags: {},
        notes: '',
        createdAt: now,
        updatedAt: now,
      },
    ],
    storageProfiles: [],
    waves: [],
    networkComponents: [],
    vmAssignments: [],
    metadata: {
      projectName,
      targetRegion: 'us-south',
      targetZone: 'us-south-1',
      deploymentTarget: 'plain_cli',
      backendType: 'local',
      createdAt: now,
      updatedAt: now,
    },
  };
}

// ─── UI-level types (moved from app/page.tsx) ───────────────────────────────

export type EstateSummary = {
  in_scope: number;
  excluded: number;
  monthly: number;
  savings: number;
  blocked: number;
  review: number;
};

export type WorkbookSummary = {
  filename: string;
  estate_summary: EstateSummary;
  overview_blockers: Record<string, number>;
  readiness_counts: Record<string, Record<string, number>>;
  assessment_quality: Record<string, string | number>;
  readiness_rows: Array<Record<string, unknown>>;
  assignment_rows?: Array<Record<string, unknown>>;
};

/** UI-level flattened view of a VM row — distinct from VmNetworkAssignment (API shape). */
export type AssignmentVm = {
  id: string;
  name: string;
  image: string;
  imageReasons: string;
  originalSpecs?: string;
  migration: string;
  migrationReasons: string;
  memory: string;
  memoryReasons: string;
  networkReadiness: string;
  networkReasons: string;
  profile: string;
  overrideProfile: string;
  overrideProfileReason?: string;
  storageTier: string;
  overrideStorageTier: string;
  overrideStorageTierReason?: string;
  network: string;
  subnet: string;
  securityGroup: string;
  power: string;
  guestOs?: string;
  sourceIp?: string;
  datacenter?: string;
  cluster?: string;
  host?: string;
  diskCount?: string;
  dataDiskCount?: string;
  totalStorageGb?: string;
  firmware?: string;
  bootDiskGb?: string;
  configuredMemoryMib?: string;
  activeMemoryMib?: string;
  consumedMemoryMib?: string;
  balloonedMemoryMib?: string;
  swappedMemoryMib?: string;
  memoryReservationMib?: string;
  memoryLimitMib?: string;
  memoryHotAdd?: string;
  sizingMemoryMib?: string;
  memorySizingBasis?: string;
  diskDetails?: unknown[];
  partitionDetails?: unknown[];
  partitionCount?: string;
  unmatchedPartitionCount?: string;
  networkDetails?: unknown[];
  readinessFindings?: unknown[];
  networkReadinessFindings?: unknown[];
  computeMonthly?: string;
  storageMonthly?: string;
  monthlyCost?: string;
  baselineCostMonthly?: string;
  savingsMonthly?: string;
  pricingSource?: string;
  pricingConfidence?: string;
  pricingLastUpdated?: string;
  pricingStatus?: string;
  profileHourly?: string;
  owner: string;
  application: string;
  wave: string;
  cutoverGroup: string;
  priority: string;
  dependencyGroup: string;
  excluded?: boolean;
  exclusionReason?: string;
  storageLabel?: string;
};

export type SavedProject = {
  id: string;
  name: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
};

export type ResourceState = {
  vpcs: VpcBucket[];
  subnets: SubnetBucket[];
  securityGroups: SecurityBucket[];
  storageProfiles: StorageBucket[];
  waves: WaveBucket[];
  networkComponents: NetworkComponent[];
};

export type SuggestionConfidence = 'High' | 'Medium' | 'Low';

export type SuggestionAuditEntry = {
  id: string;
  vmId: string;
  vmName: string;
  field: 'subnet' | 'securityGroup' | 'storage' | 'wave';
  oldValue: string;
  newValue: string;
  confidence: SuggestionConfidence;
  reason: string;
  evidence: string[];
  appliedAt: string;
  revertedAt?: string;
};

export type SavedProjectState = {
  planning_state_json?: {
    carbon_summary?: WorkbookSummary;
    carbon_assignment_rows?: AssignmentVm[];
    carbon_resources?: ResourceState;
    carbon_remediation_tracker?: RemediationTracker;
    carbon_image_import_status?: ImageImportStatus;
    carbon_suggestion_audit?: SuggestionAuditEntry[];
    remediation_tracker?: Record<string, {
      status?: string;
      owner?: string;
      due_date?: string;
      dueDate?: string;
      notes?: string;
    }>;
    image_import_status?: Record<string, {
      target_catalog_id?: string;
      targetCatalogId?: string;
      import_status?: string;
      importStatus?: string;
      estimated_import_time?: string;
      estimatedImportTime?: string;
      notes?: string;
    }>;
    suggestion_audit?: Array<{
      id?: string;
      vm_id?: string;
      vmId?: string;
      vm_name?: string;
      vmName?: string;
      field?: string;
      old_value?: string;
      oldValue?: string;
      new_value?: string;
      newValue?: string;
      confidence?: string;
      reason?: string;
      evidence?: string[];
      applied_at?: string;
      appliedAt?: string;
      reverted_at?: string | null;
      revertedAt?: string | null;
    }>;
    metadata?: Record<string, string>;
  };
};

export type AssignmentMode = 'network' | 'security' | 'storage' | 'wave';

export type RemediationStatus = 'Open' | 'In Progress' | 'Resolved' | 'Deferred';

export type RemediationTrackerEntry = {
  status: RemediationStatus;
  owner: string;
  dueDate: string;
  notes: string;
  vmKey?: string;
  vm_key?: string;
  blockerType?: string;
  blocker_type?: string;
  blockerDescription?: string;
  blocker_description?: string;
  description?: string;
  type?: string;
};

export type RemediationTracker = Record<string, RemediationTrackerEntry>;

export type RemediationBacklogItem = {
  blockerId: string;
  vmKey: string;
  vmName: string;
  owner: string;
  blockerType: string;
  blockerDescription: string;
  status: RemediationStatus;
  dueDate: string;
  notes: string;
};

export type ImageImportStatusValue =
  | ''
  | 'Pending'
  | 'Scheduled'
  | 'Imported'
  | 'Failed'
  | 'Review';

export type ImageImportEntry = {
  targetCatalogId: string;
  importStatus: ImageImportStatusValue;
  estimatedImportTime: string;
  notes: string;
};

export type ImageImportStatus = Record<string, ImageImportEntry>;

export type ImageImportRow = {
  sourceImage: string;
  vmCount: number;
  owners: string;
  targetCatalogId: string;
  importStatus: ImageImportStatusValue;
  estimatedImportTime: string;
  notes: string;
};

export type CutoverStatus = 'Ready' | 'Review' | 'Blocked';

export type CutoverReadinessRow = {
  vmName: string;
  wave: string;
  cutoverGroup: string;
  owner: string;
  application: string;
  cutoverStatus: CutoverStatus;
  blockerCategory: string;
  blockerReason: string;
  recommendedNextAction: string;
};

export type CutoverSummaryRow = {
  group: string;
  vms: number;
  ready: number;
  review: number;
  blocked: number;
  missingPlanning: number;
  unresolvedRemediation: number;
  imagePending: number;
};

export type Workflow =
  | 'overview'
  | 'intake'
  | 'assignment'
  | 'overrides'
  | 'remediation'
  | 'imageImport'
  | 'migrationOps'
  | 'network'
  | 'security'
  | 'storage'
  | 'waves'
  | 'export';

// Made with Bob
