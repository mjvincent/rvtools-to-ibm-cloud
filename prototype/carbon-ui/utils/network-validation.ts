/**
 * Network Planning Validation Utilities
 *
 * Validation functions for network planning schema.
 */

import type {
  NetworkPlanningState,
  SecurityRule,
  VmNetworkAssignment,
  SubnetBucket,
  SecurityBucket,
} from '../types/network-planning';

/**
 * Validate CIDR format.
 */
export function isValidCidr(cidr: string): boolean {
  const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
  if (!cidrRegex.test(cidr)) return false;

  const [ip, prefix] = cidr.split('/');
  const octets = ip.split('.').map(Number);
  const prefixNum = Number(prefix);

  return (
    octets.every(o => o >= 0 && o <= 255) &&
    prefixNum >= 0 && prefixNum <= 32
  );
}

/**
 * Validate security group rule.
 */
export function validateSecurityRule(rule: SecurityRule): string[] {
  const errors: string[] = [];

  if (rule.protocol === 'tcp' || rule.protocol === 'udp') {
    if (!rule.portMin || !rule.portMax) {
      errors.push('TCP/UDP rules require port range');
    }
    if (rule.portMin && (rule.portMin < 1 || rule.portMin > 65535)) {
      errors.push('Port min must be 1-65535');
    }
    if (rule.portMax && (rule.portMax < 1 || rule.portMax > 65535)) {
      errors.push('Port max must be 1-65535');
    }
    if (rule.portMin && rule.portMax && rule.portMin > rule.portMax) {
      errors.push('Port min must be <= port max');
    }
  }

  if (rule.direction === 'inbound' && !rule.source) {
    errors.push('Inbound rules require source');
  }

  if (rule.direction === 'outbound' && !rule.destination) {
    errors.push('Outbound rules require destination');
  }

  return errors;
}

/**
 * Validate VM assignment completeness.
 */
export function validateVmAssignment(
  assignment: VmNetworkAssignment,
  subnets: SubnetBucket[],
  securityGroups: SecurityBucket[]
): string[] {
  const errors: string[] = [];

  if (!assignment.primarySubnetId) {
    errors.push('Primary subnet required');
  } else if (!subnets.find(s => s.id === assignment.primarySubnetId)) {
    errors.push('Primary subnet not found');
  }

  if (!assignment.primarySecurityGroupId) {
    errors.push('Primary security group required');
  } else if (!securityGroups.find(sg => sg.id === assignment.primarySecurityGroupId)) {
    errors.push('Primary security group not found');
  }

  // Validate secondary NICs
  assignment.secondaryNics.forEach((nic, idx) => {
    if (!subnets.find(s => s.id === nic.subnetId)) {
      errors.push(`Secondary NIC ${idx + 1}: subnet not found`);
    }
    if (!securityGroups.find(sg => sg.id === nic.securityGroupId)) {
      errors.push(`Secondary NIC ${idx + 1}: security group not found`);
    }
  });

  return errors;
}

/**
 * Validate complete network plan.
 */
export function validateNetworkPlan(plan: NetworkPlanningState): string[] {
  const errors: string[] = [];

  // Validate VPCs
  if (plan.vpcs.length === 0) {
    errors.push('At least one VPC is required');
  }

  plan.vpcs.forEach(vpc => {
    if (!vpc.name || vpc.name.length === 0) {
      errors.push(`VPC ${vpc.id}: name is required`);
    }
    if (vpc.addressPrefixMode === 'manual' && vpc.addressPrefixes.length === 0) {
      errors.push(`VPC ${vpc.name}: manual mode requires address prefixes`);
    }
    vpc.addressPrefixes.forEach(prefix => {
      if (!isValidCidr(prefix.cidr)) {
        errors.push(`VPC ${vpc.name}, prefix ${prefix.name}: invalid CIDR ${prefix.cidr}`);
      }
    });
  });

  // Validate subnets
  plan.subnets.forEach(subnet => {
    if (!subnet.name || subnet.name.length === 0) {
      errors.push(`Subnet ${subnet.id}: name is required`);
    }
    if (!isValidCidr(subnet.cidr)) {
      errors.push(`Subnet ${subnet.name}: invalid CIDR ${subnet.cidr}`);
    }
    if (!plan.vpcs.find(v => v.id === subnet.vpcId)) {
      errors.push(`Subnet ${subnet.name}: VPC ${subnet.vpcId} not found`);
    }
  });

  // Validate security groups
  plan.securityGroups.forEach(sg => {
    if (!sg.name || sg.name.length === 0) {
      errors.push(`Security group ${sg.id}: name is required`);
    }
    if (!plan.vpcs.find(v => v.id === sg.vpcId)) {
      errors.push(`Security group ${sg.name}: VPC ${sg.vpcId} not found`);
    }
    sg.rules.forEach((rule, idx) => {
      const ruleErrors = validateSecurityRule(rule);
      ruleErrors.forEach(err => {
        errors.push(`Security group ${sg.name}, rule ${idx + 1}: ${err}`);
      });
    });
  });

  // Validate VM assignments
  plan.vmAssignments.forEach(assignment => {
    if (!assignment.vmKey || assignment.vmKey.length === 0) {
      errors.push('VM assignment: vmKey is required');
    }
    const assignmentErrors = validateVmAssignment(
      assignment,
      plan.subnets,
      plan.securityGroups
    );
    assignmentErrors.forEach(err => {
      errors.push(`VM ${assignment.vmName}: ${err}`);
    });
  });

  return errors;
}

/**
 * Check if two CIDRs overlap (simplified check).
 */
export function cidrsOverlap(cidr1: string, cidr2: string): boolean {
  // This is a simplified implementation
  // For production, use a proper IP address library
  const [ip1, prefix1] = cidr1.split('/');
  const [ip2, prefix2] = cidr2.split('/');

  // If CIDRs are identical, they overlap
  if (cidr1 === cidr2) return true;

  // For now, return false for different CIDRs
  // TODO: Implement proper CIDR overlap detection
  return false;
}

/**
 * Detect CIDR overlaps within subnets.
 */
export function detectCidrOverlaps(
  subnets: SubnetBucket[]
): Array<{ subnet1: string; subnet2: string }> {
  const overlaps: Array<{ subnet1: string; subnet2: string }> = [];

  for (let i = 0; i < subnets.length; i++) {
    for (let j = i + 1; j < subnets.length; j++) {
      if (cidrsOverlap(subnets[i].cidr, subnets[j].cidr)) {
        overlaps.push({
          subnet1: subnets[i].name,
          subnet2: subnets[j].name,
        });
      }
    }
  }

  return overlaps;
}

// Made with Bob
