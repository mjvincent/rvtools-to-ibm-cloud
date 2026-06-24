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

// Made with Bob
