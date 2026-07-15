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
  ResourceState,
  NetworkComponentType,
} from '../types/network-planning';

export type NetworkValidationSeverity = 'blocker' | 'warning';

export type NetworkValidationFinding = {
  id: string;
  severity: NetworkValidationSeverity;
  subject: string;
  message: string;
  recommendedAction: string;
};

function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

function resourceLabel(resource: { name: string; label?: string }) {
  return terraformLabel(resource.label || resource.name);
}

function duplicateLabelFindings(
  resources: Array<{ id: string; name: string; label?: string }>,
  groupName: string,
): NetworkValidationFinding[] {
  const byLabel = new Map<string, Array<{ id: string; name: string }>>();
  resources.forEach((resource) => {
    const label = resourceLabel(resource);
    byLabel.set(label, [...(byLabel.get(label) || []), resource]);
  });

  return Array.from(byLabel.entries())
    .filter(([, matches]) => matches.length > 1)
    .map(([label, matches]) => ({
      id: `duplicate-label-${groupName}-${label}`,
      severity: 'blocker' as const,
      subject: `${groupName} labels`,
      message: `Duplicate Terraform label "${label}" is used by ${matches.map((item) => item.name).join(', ')}.`,
      recommendedAction: `Rename one of the ${groupName.toLowerCase()} resources or adjust its Terraform label before handoff.`,
    }));
}

function componentNeedsAttachment(type: string) {
  const normalized = type.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_') as NetworkComponentType | string;
  return [
    'public_gateway',
    'vpn_gateway',
    'load_balancer',
    'vpe_gateway',
    'floating_ip',
  ].includes(normalized);
}

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
      errors.push('portMax must be >= portMin');
    }
  }

  if (rule.direction === 'inbound') {
    if (!rule.source) {
      errors.push('Inbound rules require source');
    } else if (rule.source !== 'any' && !isValidCidr(rule.source)) {
      errors.push(`Invalid source CIDR: ${rule.source}`);
    }
  }

  // protocol 'all' matches everything — destination is not required
  if (rule.direction === 'outbound' && rule.protocol !== 'all') {
    if (!rule.destination) {
      errors.push('Outbound rules require destination');
    } else if (rule.destination !== 'any' && !isValidCidr(rule.destination)) {
      errors.push(`Invalid destination CIDR: ${rule.destination}`);
    }
  }

  return errors;
}

/**
 * Validate VM assignment completeness.
 *
 * When called standalone (without a plan context), omit subnets/securityGroups
 * and only the vmKey presence check is applied.
 */
export function validateVmAssignment(
  assignment: VmNetworkAssignment,
  subnets: SubnetBucket[] = [],
  securityGroups: SecurityBucket[] = []
): string[] {
  const errors: string[] = [];

  if (!assignment.vmKey || assignment.vmKey.trim() === '') {
    errors.push('vmKey is required');
  }

  if (!assignment.primarySubnetId) {
    errors.push('Primary subnet required');
  } else if (subnets.length > 0 && !subnets.find(s => s.id === assignment.primarySubnetId)) {
    errors.push('Primary subnet not found');
  }

  if (!assignment.primarySecurityGroupId) {
    errors.push('Primary security group required');
  } else if (securityGroups.length > 0 && !securityGroups.find(sg => sg.id === assignment.primarySecurityGroupId)) {
    errors.push('Primary security group not found');
  }

  // Validate secondary NICs
  assignment.secondaryNics.forEach((nic, idx) => {
    if (subnets.length > 0 && !subnets.find(s => s.id === nic.subnetId)) {
      errors.push(`Secondary NIC ${idx + 1}: subnet not found`);
    }
    if (securityGroups.length > 0 && !securityGroups.find(sg => sg.id === nic.securityGroupId)) {
      errors.push(`Secondary NIC ${idx + 1}: security group not found`);
    }
  });

  // Validate no duplicate secondary NIC orders
  const orders = assignment.secondaryNics.map(n => n.order);
  const seen = new Set<number>();
  orders.forEach(o => {
    if (seen.has(o)) {
      errors.push(`Duplicate secondary NIC order: ${o}`);
    }
    seen.add(o);
  });

  return errors;
}

/**
 * Validate complete network plan.
 */
export function validateNetworkPlan(plan: NetworkPlanningState): string[] {
  const errors: string[] = [];

  // Validate VPCs — only required if the plan has any other resources defined
  const hasResources =
    plan.subnets.length > 0 ||
    plan.securityGroups.length > 0 ||
    plan.vmAssignments.length > 0;
  if (hasResources && plan.vpcs.length === 0) {
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

export function validateResourceNetworkPlan(resources: ResourceState): NetworkValidationFinding[] {
  const findings: NetworkValidationFinding[] = [];
  const vpcIds = new Set(resources.vpcs.map((vpc) => vpc.id));
  const hasNetworkResources =
    resources.subnets.length > 0 ||
    resources.securityGroups.length > 0 ||
    (resources.networkComponents || []).length > 0;

  if (hasNetworkResources && resources.vpcs.length === 0) {
    findings.push({
      id: 'network-plan-missing-vpc',
      severity: 'blocker',
      subject: 'Network plan',
      message: 'Network resources exist but no VPC is defined.',
      recommendedAction: 'Create a VPC bucket before saving or exporting the Carbon network plan.',
    });
  }

  resources.subnets.forEach((subnet) => {
    if (!subnet.cidr) {
      findings.push({
        id: `subnet-missing-cidr-${subnet.id}`,
        severity: 'blocker',
        subject: subnet.name || subnet.id,
        message: 'Subnet is missing a CIDR block.',
        recommendedAction: 'Enter a valid IPv4 CIDR for the subnet before Terraform handoff.',
      });
    } else if (!isValidCidr(subnet.cidr)) {
      findings.push({
        id: `subnet-invalid-cidr-${subnet.id}`,
        severity: 'blocker',
        subject: subnet.name || subnet.id,
        message: `Subnet CIDR "${subnet.cidr}" is not valid.`,
        recommendedAction: 'Replace the subnet CIDR with a valid IPv4 CIDR such as 10.40.10.0/24.',
      });
    }

    if (!subnet.vpcId || !vpcIds.has(subnet.vpcId)) {
      findings.push({
        id: `subnet-missing-vpc-${subnet.id}`,
        severity: 'blocker',
        subject: subnet.name || subnet.id,
        message: 'Subnet references a missing VPC.',
        recommendedAction: 'Assign the subnet to an existing VPC before saving or exporting the plan.',
      });
    }
  });

  resources.securityGroups.forEach((securityGroup) => {
    if (!securityGroup.vpcId || !vpcIds.has(securityGroup.vpcId)) {
      findings.push({
        id: `security-group-missing-vpc-${securityGroup.id}`,
        severity: 'blocker',
        subject: securityGroup.name || securityGroup.id,
        message: 'Security group references a missing VPC.',
        recommendedAction: 'Assign the security group to an existing VPC before Terraform handoff.',
      });
    }
  });

  (resources.networkComponents || []).forEach((component) => {
    if (!component.vpcId) {
      findings.push({
        id: `component-no-vpc-${component.id}`,
        severity: 'blocker',
        subject: component.name || component.id,
        message: 'Network component has no VPC selected.',
        recommendedAction: 'Edit the component from the Network Plan diagram and select a VPC.',
      });
    } else if (!vpcIds.has(component.vpcId)) {
      findings.push({
        id: `component-missing-vpc-${component.id}`,
        severity: 'blocker',
        subject: component.name || component.id,
        message: 'Network component references a VPC that no longer exists.',
        recommendedAction: 'Edit the component and choose an existing VPC, or remove the stale component.',
      });
    }

    if (componentNeedsAttachment(component.type) && !component.attachment) {
      findings.push({
        id: `component-missing-attachment-${component.id}`,
        severity: 'warning',
        subject: component.name || component.id,
        message: `${component.type} has no attachment or target selected.`,
        recommendedAction: 'Edit the component and select the target subnet, VPC, or service attachment expected by the Terraform operator.',
      });
    }
  });

  findings.push(
    ...duplicateLabelFindings(resources.vpcs, 'VPC'),
    ...duplicateLabelFindings(resources.subnets, 'Subnet'),
    ...duplicateLabelFindings(resources.networkComponents || [], 'Network component'),
  );

  return findings;
}

/**
 * Check if two CIDRs overlap (simplified check).
 */
export function cidrsOverlap(cidr1: string, cidr2: string): boolean {
  if (cidr1 === cidr2) return true;
  if (!isValidCidr(cidr1) || !isValidCidr(cidr2)) return false;

  const [ip1, bits1] = cidr1.split('/');
  const [ip2, bits2] = cidr2.split('/');

  // Convert dotted-decimal IP to a 32-bit integer
  const toInt = (ip: string): number =>
    ip.split('.').reduce((acc, octet) => (acc << 8) | parseInt(octet, 10), 0) >>> 0;

  const int1 = toInt(ip1);
  const int2 = toInt(ip2);
  const prefix1 = parseInt(bits1, 10);
  const prefix2 = parseInt(bits2, 10);

  // Mask each address with the smaller prefix length to get the network base
  const minPrefix = Math.min(prefix1, prefix2);
  const mask = minPrefix === 0 ? 0 : (~0 << (32 - minPrefix)) >>> 0;

  return (int1 & mask) === (int2 & mask);
}

/**
 * Detect CIDR overlaps.
 *
 * Accepts either a string[] of CIDR strings or a SubnetBucket[] for convenience.
 * Returns pairs of overlapping CIDR strings.
 */
export function detectCidrOverlaps(
  cidrsOrSubnets: string[] | SubnetBucket[]
): Array<{ subnet1: string; subnet2: string }> {
  // Normalise to string[] of CIDRs
  const cidrs: string[] = (cidrsOrSubnets as Array<string | SubnetBucket>).map(
    item => (typeof item === 'string' ? item : item.cidr)
  );
  // Build label map for friendly names
  const labels: string[] = (cidrsOrSubnets as Array<string | SubnetBucket>).map(
    item => (typeof item === 'string' ? item : item.name)
  );

  const overlaps: Array<{ subnet1: string; subnet2: string }> = [];

  for (let i = 0; i < cidrs.length; i++) {
    for (let j = i + 1; j < cidrs.length; j++) {
      if (cidrsOverlap(cidrs[i], cidrs[j])) {
        overlaps.push({
          subnet1: labels[i],
          subnet2: labels[j],
        });
      }
    }
  }

  return overlaps;
}

// Made with Bob
