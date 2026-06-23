/**
 * Unit tests for network planning types and helper functions
 * 
 * Note: These tests require Jest to be configured.
 * Run: npm install --save-dev @types/jest jest ts-jest
 */

import {
  createEmptyNetworkPlan,
  createInitialNetworkPlan,
  SCHEMA_VERSION,
} from '../types/network-planning';

describe('Network Planning Helper Functions', () => {
  describe('createEmptyNetworkPlan', () => {
    it('should create an empty network plan with default values', () => {
      const plan = createEmptyNetworkPlan();

      expect(plan.version).toBe(SCHEMA_VERSION);
      expect(plan.vpcs).toEqual([]);
      expect(plan.subnets).toEqual([]);
      expect(plan.securityGroups).toEqual([]);
      expect(plan.storageProfiles).toEqual([]);
      expect(plan.waves).toEqual([]);
      expect(plan.networkComponents).toEqual([]);
      expect(plan.vmAssignments).toEqual([]);
    });

    it('should include metadata with default values', () => {
      const plan = createEmptyNetworkPlan();

      expect(plan.metadata).toBeDefined();
      expect(plan.metadata.projectName).toBe('');
      expect(plan.metadata.targetRegion).toBe('us-south');
      expect(plan.metadata.targetZone).toBe('us-south-1');
      expect(plan.metadata.deploymentTarget).toBe('plain_cli');
    });

    it('should create timestamps in ISO format', () => {
      const plan = createEmptyNetworkPlan();
      const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;

      expect(plan.metadata.createdAt).toMatch(isoRegex);
      expect(plan.metadata.updatedAt).toMatch(isoRegex);
    });

    it('should create unique timestamps', () => {
      const plan1 = createEmptyNetworkPlan();
      // Small delay to ensure different timestamps
      const plan2 = createEmptyNetworkPlan();

      // Timestamps should be valid ISO strings
      expect(new Date(plan1.metadata.createdAt).getTime()).toBeGreaterThan(0);
      expect(new Date(plan2.metadata.createdAt).getTime()).toBeGreaterThan(0);
    });
  });

  describe('createInitialNetworkPlan', () => {
    const projectName = 'Test Migration Project';

    it('should create an initial network plan with metadata', () => {
      const plan = createInitialNetworkPlan(projectName);

      expect(plan.version).toBe(SCHEMA_VERSION);
      expect(plan.metadata).toBeDefined();
      expect(plan.metadata.projectName).toBe(projectName);
      expect(plan.metadata.targetRegion).toBe('us-south');
      expect(plan.metadata.targetZone).toBe('us-south-1');
      expect(plan.metadata.deploymentTarget).toBe('plain_cli');
    });

    it('should create a default VPC', () => {
      const plan = createInitialNetworkPlan(projectName);

      expect(plan.vpcs).toHaveLength(1);
      
      const vpc = plan.vpcs[0];
      expect(vpc.name).toBe('migration-vpc');
      expect(vpc.label).toBe('Migration VPC');
      expect(vpc.region).toBe('us-south');
      expect(vpc.addressPrefixMode).toBe('manual');
      expect(vpc.id).toBeDefined();
      expect(vpc.id.length).toBeGreaterThan(0);
    });

    it('should create a default address prefix', () => {
      const plan = createInitialNetworkPlan(projectName);

      const vpc = plan.vpcs[0];
      expect(vpc.addressPrefixes).toHaveLength(1);
      
      const prefix = vpc.addressPrefixes[0];
      expect(prefix.name).toBe('zone-1-prefix');
      expect(prefix.cidr).toBe('10.240.0.0/16');
      expect(prefix.zone).toBe('us-south-1');
      expect(prefix.isDefault).toBe(true);
      expect(prefix.id).toBeDefined();
    });

    it('should create a default subnet', () => {
      const plan = createInitialNetworkPlan(projectName);

      expect(plan.subnets).toHaveLength(1);
      
      const subnet = plan.subnets[0];
      expect(subnet.name).toBe('default-subnet');
      expect(subnet.label).toBe('Default Subnet');
      expect(subnet.zone).toBe('us-south-1');
      expect(subnet.cidr).toBe('10.240.10.0/24');
      expect(subnet.purpose).toBe('general');
      expect(subnet.publicGateway).toBe(false);
      expect(subnet.vpcId).toBe(plan.vpcs[0].id);
    });

    it('should create a default security group', () => {
      const plan = createInitialNetworkPlan(projectName);

      expect(plan.securityGroups).toHaveLength(1);
      
      const sg = plan.securityGroups[0];
      expect(sg.name).toBe('default-sg');
      expect(sg.label).toBe('Default Security Group');
      expect(sg.purpose).toBe('general');
      expect(sg.vpcId).toBe(plan.vpcs[0].id);
      expect(sg.rules).toHaveLength(1);
    });

    it('should create a default outbound rule', () => {
      const plan = createInitialNetworkPlan(projectName);

      const sg = plan.securityGroups[0];
      const rule = sg.rules[0];
      
      expect(rule.direction).toBe('outbound');
      expect(rule.protocol).toBe('all');
      expect(rule.description).toBe('Allow all outbound');
      expect(rule.id).toBeDefined();
    });

    it('should initialize empty arrays for optional buckets', () => {
      const plan = createInitialNetworkPlan(projectName);

      expect(plan.storageProfiles).toEqual([]);
      expect(plan.waves).toEqual([]);
      expect(plan.networkComponents).toEqual([]);
      expect(plan.vmAssignments).toEqual([]);
    });

    it('should create consistent timestamps across all entities', () => {
      const plan = createInitialNetworkPlan(projectName);

      const timestamps = [
        plan.metadata.createdAt,
        plan.vpcs[0].createdAt,
        plan.subnets[0].createdAt,
        plan.securityGroups[0].createdAt,
      ];

      // All timestamps should be the same (created in same function call)
      const uniqueTimestamps = new Set(timestamps);
      expect(uniqueTimestamps.size).toBe(1);
    });

    it('should generate unique IDs for all entities', () => {
      const plan = createInitialNetworkPlan(projectName);

      const ids = [
        plan.vpcs[0].id,
        plan.vpcs[0].addressPrefixes[0].id,
        plan.subnets[0].id,
        plan.securityGroups[0].id,
        plan.securityGroups[0].rules[0].id,
      ];

      // All IDs should be unique
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });

    it('should create valid UUID format for IDs', () => {
      const plan = createInitialNetworkPlan(projectName);
      
      // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

      expect(plan.vpcs[0].id).toMatch(uuidRegex);
      expect(plan.subnets[0].id).toMatch(uuidRegex);
      expect(plan.securityGroups[0].id).toMatch(uuidRegex);
    });

    it('should link subnet to VPC via vpcId', () => {
      const plan = createInitialNetworkPlan(projectName);

      const vpcId = plan.vpcs[0].id;
      const subnetVpcId = plan.subnets[0].vpcId;
      const sgVpcId = plan.securityGroups[0].vpcId;

      expect(subnetVpcId).toBe(vpcId);
      expect(sgVpcId).toBe(vpcId);
    });

    it('should handle different project names', () => {
      const names = [
        'Simple Project',
        'Project with Numbers 123',
        'Project-with-dashes',
        'Project_with_underscores',
      ];

      names.forEach(name => {
        const plan = createInitialNetworkPlan(name);
        expect(plan.metadata.projectName).toBe(name);
      });
    });

    it('should create immutable structure (no shared references)', () => {
      const plan1 = createInitialNetworkPlan('Project 1');
      const plan2 = createInitialNetworkPlan('Project 2');

      // Modify plan1
      plan1.vpcs[0].name = 'modified-vpc';

      // plan2 should not be affected
      expect(plan2.vpcs[0].name).toBe('migration-vpc');
    });
  });

  describe('Schema Version', () => {
    it('should export schema version constant', () => {
      expect(SCHEMA_VERSION).toBe('1.0');
    });

    it('should use schema version in created plans', () => {
      const emptyPlan = createEmptyNetworkPlan();
      const initialPlan = createInitialNetworkPlan('Test');

      expect(emptyPlan.version).toBe(SCHEMA_VERSION);
      expect(initialPlan.version).toBe(SCHEMA_VERSION);
    });
  });
});

// Made with Bob
