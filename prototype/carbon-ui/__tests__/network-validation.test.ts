/**
 * Unit tests for network validation utilities
 *
 * Note: These tests require Jest to be configured.
 * Run: npm install --save-dev @types/jest jest ts-jest
 */

import {
  isValidCidr,
  validateSecurityRule,
  validateVmAssignment,
  validateNetworkPlan,
  validateResourceNetworkPlan,
  detectCidrOverlaps,
} from '../utils/network-validation';
import { createInitialNetworkPlan, createEmptyNetworkPlan } from '../types/network-planning';
import type { ResourceState, SecurityRule, VmNetworkAssignment, NetworkPlanningState } from '../types/network-planning';

describe('Network Validation Utilities', () => {
  describe('isValidCidr', () => {
    it('should validate correct CIDR notations', () => {
      const validCidrs = [
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
        '10.240.0.0/16',
        '10.240.10.0/24',
        '0.0.0.0/0',
        '255.255.255.255/32',
      ];

      validCidrs.forEach(cidr => {
        expect(isValidCidr(cidr)).toBe(true);
      });
    });

    it('should reject invalid CIDR notations', () => {
      const invalidCidrs = [
        '10.0.0.0',           // Missing prefix
        '10.0.0.0/',          // Missing prefix length
        '10.0.0.0/33',        // Invalid prefix length
        '10.0.0.0/-1',        // Negative prefix
        '256.0.0.0/8',        // Invalid octet
        '10.0.0/8',           // Missing octet
        '10.0.0.0.0/8',       // Too many octets
        'not-a-cidr',         // Not a CIDR
        '',                   // Empty string
        '10.0.0.0/8/16',      // Multiple prefixes
      ];

      invalidCidrs.forEach(cidr => {
        expect(isValidCidr(cidr)).toBe(false);
      });
    });

    it('should handle edge cases', () => {
      expect(isValidCidr('0.0.0.0/0')).toBe(true);
      expect(isValidCidr('255.255.255.255/32')).toBe(true);
      expect(isValidCidr('10.0.0.0/0')).toBe(true);
      expect(isValidCidr('10.0.0.0/32')).toBe(true);
    });
  });

  describe('validateSecurityRule', () => {
    it('should validate a correct TCP rule', () => {
      const rule: SecurityRule = {
        id: 'rule-1',
        direction: 'inbound',
        protocol: 'tcp',
        portMin: 80,
        portMax: 80,
        source: '0.0.0.0/0',
        description: 'Allow HTTP',
      };

      const errors = validateSecurityRule(rule);
      expect(errors).toEqual([]);
    });

    it('should validate a correct UDP rule', () => {
      const rule: SecurityRule = {
        id: 'rule-2',
        direction: 'outbound',
        protocol: 'udp',
        portMin: 53,
        portMax: 53,
        destination: '8.8.8.8/32',
        description: 'Allow DNS',
      };

      const errors = validateSecurityRule(rule);
      expect(errors).toEqual([]);
    });

    it('should validate an ICMP rule without ports', () => {
      const rule: SecurityRule = {
        id: 'rule-3',
        direction: 'inbound',
        protocol: 'icmp',
        source: '10.0.0.0/8',
        description: 'Allow ping',
      };

      const errors = validateSecurityRule(rule);
      expect(errors).toEqual([]);
    });

    it('should validate an "all" protocol rule', () => {
      const rule: SecurityRule = {
        id: 'rule-4',
        direction: 'outbound',
        protocol: 'all',
        destination: '0.0.0.0/0',
        description: 'Allow all outbound',
      };

      const errors = validateSecurityRule(rule);
      expect(errors).toEqual([]);
    });

    it('should detect invalid port ranges', () => {
      const rule: SecurityRule = {
        id: 'rule-5',
        direction: 'inbound',
        protocol: 'tcp',
        portMin: 80,
        portMax: 79,  // Max less than min
        source: '0.0.0.0/0',
        description: 'Invalid port range',
      };

      const errors = validateSecurityRule(rule);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0]).toContain('portMax');
    });

    it('should detect ports out of valid range', () => {
      const rule: SecurityRule = {
        id: 'rule-6',
        direction: 'inbound',
        protocol: 'tcp',
        portMin: 0,
        portMax: 65536,  // Out of range
        source: '0.0.0.0/0',
        description: 'Invalid port',
      };

      const errors = validateSecurityRule(rule);
      expect(errors.length).toBeGreaterThan(0);
    });

    it('should detect invalid CIDR in source', () => {
      const rule: SecurityRule = {
        id: 'rule-7',
        direction: 'inbound',
        protocol: 'tcp',
        portMin: 443,
        portMax: 443,
        source: 'invalid-cidr',
        description: 'Invalid source',
      };

      const errors = validateSecurityRule(rule);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0]).toContain('source');
    });

    it('should detect invalid CIDR in destination', () => {
      const rule: SecurityRule = {
        id: 'rule-8',
        direction: 'outbound',
        protocol: 'tcp',
        portMin: 443,
        portMax: 443,
        destination: '256.0.0.0/8',
        description: 'Invalid destination',
      };

      const errors = validateSecurityRule(rule);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0]).toContain('destination');
    });

    it('should require source or destination', () => {
      const rule: SecurityRule = {
        id: 'rule-9',
        direction: 'inbound',
        protocol: 'tcp',
        portMin: 80,
        portMax: 80,
        description: 'Missing source/destination',
      };

      const errors = validateSecurityRule(rule);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  describe('validateVmAssignment', () => {
    it('should validate a correct VM assignment', () => {
      const assignment: VmNetworkAssignment = {
        vmKey: 'vm-1',
        vmName: 'web-server-1',
        primarySubnetId: 'subnet-1',
        primarySecurityGroupId: 'sg-1',
        secondaryNics: [],
        excluded: false,
      };

      const errors = validateVmAssignment(assignment);
      expect(errors).toEqual([]);
    });

    it('should validate VM assignment with secondary NICs', () => {
      const assignment: VmNetworkAssignment = {
        vmKey: 'vm-2',
        vmName: 'multi-nic-server',
        primarySubnetId: 'subnet-1',
        primarySecurityGroupId: 'sg-1',
        secondaryNics: [
          {
            id: 'nic-1',
            subnetId: 'subnet-2',
            securityGroupId: 'sg-2',
            order: 1,
          },
          {
            id: 'nic-2',
            subnetId: 'subnet-3',
            securityGroupId: 'sg-3',
            order: 2,
          },
        ],
        excluded: false,
      };

      const errors = validateVmAssignment(assignment);
      expect(errors).toEqual([]);
    });

    it('should validate excluded VM with reason', () => {
      const assignment: VmNetworkAssignment = {
        vmKey: 'vm-3',
        vmName: 'excluded-vm',
        primarySubnetId: 'subnet-1',
        primarySecurityGroupId: 'sg-1',
        secondaryNics: [],
        excluded: true,
        exclusionReason: 'Not migrating this VM',
      };

      const errors = validateVmAssignment(assignment);
      expect(errors).toEqual([]);
    });

    it('should detect missing required fields', () => {
      const assignment: VmNetworkAssignment = {
        vmKey: '',  // Empty
        vmName: 'test-vm',
        primarySubnetId: 'subnet-1',
        primarySecurityGroupId: 'sg-1',
        secondaryNics: [],
        excluded: false,
      };

      const errors = validateVmAssignment(assignment);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0]).toContain('vmKey');
    });

    it('should detect duplicate secondary NIC orders', () => {
      const assignment: VmNetworkAssignment = {
        vmKey: 'vm-4',
        vmName: 'duplicate-order-vm',
        primarySubnetId: 'subnet-1',
        primarySecurityGroupId: 'sg-1',
        secondaryNics: [
          {
            id: 'nic-1',
            subnetId: 'subnet-2',
            securityGroupId: 'sg-2',
            order: 1,
          },
          {
            id: 'nic-2',
            subnetId: 'subnet-3',
            securityGroupId: 'sg-3',
            order: 1,  // Duplicate order
          },
        ],
        excluded: false,
      };

      const errors = validateVmAssignment(assignment);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0]).toContain('order');
    });
  });

  describe('validateNetworkPlan', () => {
    it('should validate a correct network plan', () => {
      const plan = createInitialNetworkPlan('Test Project');
      const errors = validateNetworkPlan(plan);
      expect(errors).toEqual([]);
    });

    it('should validate an empty network plan', () => {
      const plan = createEmptyNetworkPlan();
      const errors = validateNetworkPlan(plan);
      expect(errors).toEqual([]);
    });

    it('should detect invalid VPC CIDR', () => {
      const plan = createInitialNetworkPlan('Test');
      plan.vpcs[0].addressPrefixes[0].cidr = 'invalid-cidr';

      const errors = validateNetworkPlan(plan);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.includes('CIDR'))).toBe(true);
    });

    it('should detect invalid subnet CIDR', () => {
      const plan = createInitialNetworkPlan('Test');
      plan.subnets[0].cidr = '256.0.0.0/24';

      const errors = validateNetworkPlan(plan);
      expect(errors.length).toBeGreaterThan(0);
    });

    it('should detect invalid security rules', () => {
      const plan = createInitialNetworkPlan('Test');
      plan.securityGroups[0].rules.push({
        id: 'bad-rule',
        direction: 'inbound',
        protocol: 'tcp',
        portMin: 80,
        portMax: 79,  // Invalid range
        source: '0.0.0.0/0',
        description: 'Bad rule',
      });

      const errors = validateNetworkPlan(plan);
      expect(errors.length).toBeGreaterThan(0);
    });

    it('should detect orphaned subnets', () => {
      const plan = createInitialNetworkPlan('Test');
      plan.subnets[0].vpcId = 'non-existent-vpc';

      const errors = validateNetworkPlan(plan);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.includes('VPC'))).toBe(true);
    });

    it('should detect orphaned security groups', () => {
      const plan = createInitialNetworkPlan('Test');
      plan.securityGroups[0].vpcId = 'non-existent-vpc';

      const errors = validateNetworkPlan(plan);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  describe('validateResourceNetworkPlan', () => {
    const validResources: ResourceState = {
      vpcs: [{
        id: 'vpc-1',
        name: 'prod-vpc',
        label: 'prod_vpc',
        region: 'us-south',
        addressPrefixMode: 'manual',
        addressPrefixes: [],
        tags: {},
        notes: '',
        createdAt: '',
        updatedAt: '',
      }],
      subnets: [{
        id: 'subnet-1',
        name: 'prod-app',
        label: 'prod_app',
        vpcId: 'vpc-1',
        zone: 'us-south-1',
        cidr: '10.40.10.0/24',
        purpose: 'Application',
        publicGateway: false,
        tags: {},
        notes: '',
        createdAt: '',
        updatedAt: '',
      }],
      securityGroups: [{
        id: 'sg-1',
        name: 'sg-app',
        label: 'sg_app',
        vpcId: 'vpc-1',
        purpose: 'Application',
        rules: [],
        tags: {},
        notes: '',
        createdAt: '',
        updatedAt: '',
      }],
      storageProfiles: [],
      waves: [],
      networkComponents: [{
        id: 'component-1',
        name: 'prod-public-gateway',
        label: 'prod_public_gateway',
        type: 'public_gateway',
        vpcId: 'vpc-1',
        attachment: 'prod-app',
        config: {},
        tags: {},
        notes: '',
        createdAt: '',
        updatedAt: '',
      }],
    };

    it('returns no findings for a valid resource network plan', () => {
      expect(validateResourceNetworkPlan(validResources)).toEqual([]);
    });

    it('flags missing VPC references and component attachment warnings', () => {
      const findings = validateResourceNetworkPlan({
        ...validResources,
        subnets: [{ ...validResources.subnets[0], vpcId: 'missing-vpc', cidr: '' }],
        securityGroups: [{ ...validResources.securityGroups[0], vpcId: 'missing-vpc' }],
        networkComponents: [{
          ...validResources.networkComponents[0],
          vpcId: '',
          attachment: '',
        }],
      });

      expect(findings.map((finding) => finding.id)).toEqual(expect.arrayContaining([
        'subnet-missing-cidr-subnet-1',
        'subnet-missing-vpc-subnet-1',
        'security-group-missing-vpc-sg-1',
        'component-no-vpc-component-1',
        'component-missing-attachment-component-1',
      ]));
      expect(findings.find((finding) => finding.id === 'component-missing-attachment-component-1')?.severity).toBe('warning');
    });

    it('flags invalid subnet CIDR and duplicate Terraform labels', () => {
      const findings = validateResourceNetworkPlan({
        ...validResources,
        subnets: [
          { ...validResources.subnets[0], cidr: 'not-a-cidr' },
          {
            ...validResources.subnets[0],
            id: 'subnet-2',
            name: 'prod-app-copy',
            label: 'prod_app',
            cidr: '10.40.20.0/24',
          },
        ],
        networkComponents: [
          validResources.networkComponents[0],
          {
            ...validResources.networkComponents[0],
            id: 'component-2',
            name: 'duplicate-component',
            label: 'prod_public_gateway',
          },
        ],
      });

      expect(findings.map((finding) => finding.id)).toEqual(expect.arrayContaining([
        'subnet-invalid-cidr-subnet-1',
        'duplicate-label-Subnet-prod_app',
        'duplicate-label-Network component-prod_public_gateway',
      ]));
      expect(findings.every((finding) => finding.recommendedAction.length > 0)).toBe(true);
    });
  });

  describe('detectCidrOverlaps', () => {
    it('should detect no overlaps in non-overlapping CIDRs', () => {
      const cidrs = [
        '10.240.0.0/24',
        '10.240.1.0/24',
        '10.240.2.0/24',
      ];

      const overlaps = detectCidrOverlaps(cidrs);
      expect(overlaps).toEqual([]);
    });

    it('should detect exact duplicate CIDRs', () => {
      const cidrs = [
        '10.240.0.0/24',
        '10.240.0.0/24',
      ];

      const overlaps = detectCidrOverlaps(cidrs);
      expect(overlaps.length).toBeGreaterThan(0);
    });

    it('should detect overlapping CIDRs', () => {
      const cidrs = [
        '10.240.0.0/16',    // Larger range
        '10.240.10.0/24',   // Contained within first
      ];

      const overlaps = detectCidrOverlaps(cidrs);
      expect(overlaps.length).toBeGreaterThan(0);
    });

    it('should handle empty CIDR list', () => {
      const overlaps = detectCidrOverlaps([]);
      expect(overlaps).toEqual([]);
    });

    it('should handle single CIDR', () => {
      const overlaps = detectCidrOverlaps(['10.240.0.0/24']);
      expect(overlaps).toEqual([]);
    });

    it('should detect multiple overlaps', () => {
      const cidrs = [
        '10.0.0.0/8',
        '10.240.0.0/16',
        '10.240.10.0/24',
      ];

      const overlaps = detectCidrOverlaps(cidrs);
      // All three overlap with each other
      expect(overlaps.length).toBeGreaterThan(0);
    });
  });

  describe('Integration Tests', () => {
    it('should validate a complete migration plan', () => {
      const plan = createInitialNetworkPlan('Production Migration');

      // Add additional resources
      plan.subnets.push({
        id: 'subnet-2',
        name: 'app-tier',
        label: 'Application Tier',
        vpcId: plan.vpcs[0].id,
        zone: 'us-south-2',
        cidr: '10.240.20.0/24',
        purpose: 'application',
        publicGateway: false,
        tags: { tier: 'app' },
        notes: '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      plan.securityGroups.push({
        id: 'sg-2',
        name: 'app-sg',
        label: 'Application Security Group',
        vpcId: plan.vpcs[0].id,
        purpose: 'application',
        rules: [
          {
            id: 'rule-1',
            direction: 'inbound',
            protocol: 'tcp',
            portMin: 8080,
            portMax: 8080,
            source: '10.240.10.0/24',
            description: 'Allow from web tier',
          },
        ],
        tags: {},
        notes: '',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      const errors = validateNetworkPlan(plan);
      expect(errors).toEqual([]);
    });

    it('should catch multiple validation errors', () => {
      const plan = createInitialNetworkPlan('Bad Plan');

      // Introduce multiple errors
      plan.vpcs[0].addressPrefixes[0].cidr = 'invalid';
      plan.subnets[0].cidr = '256.0.0.0/24';
      plan.securityGroups[0].rules[0].protocol = 'tcp' as any;
      plan.securityGroups[0].rules[0].portMin = 80;
      plan.securityGroups[0].rules[0].portMax = 79;

      const errors = validateNetworkPlan(plan);
      expect(errors.length).toBeGreaterThan(2);
    });
  });
});

// Made with Bob
