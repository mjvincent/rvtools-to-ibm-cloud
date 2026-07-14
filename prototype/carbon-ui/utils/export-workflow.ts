import type { AssignmentVm, SuggestionConfidence, Workflow } from '../types/network-planning';
import type { PreflightResponse } from '../hooks/useApi';
import {
  carbonPackageFiles,
  handoffPackageFiles,
  terraformPackageFiles,
} from './package-inventory';

export const packageGroups = [
  {
    title: 'Terraform project',
    status: 'Modular layout',
    tagType: 'green' as const,
    files: terraformPackageFiles,
  },
  {
    title: 'Migration handoff',
    status: 'Parity covered',
    tagType: 'blue' as const,
    files: handoffPackageFiles,
  },
  {
    title: 'Carbon state',
    status: 'Carbon only',
    tagType: 'purple' as const,
    files: carbonPackageFiles,
  },
];

export const packageParitySummary = [
  {
    label: 'Handoff parity',
    value: `${handoffPackageFiles.length}/${handoffPackageFiles.length}`,
    detail: 'Streamlit handoff files',
    tag: 'Covered',
    tagType: 'green' as const,
  },
  {
    label: 'Terraform layout',
    value: `${terraformPackageFiles.length}/${terraformPackageFiles.length}`,
    detail: 'Carbon modular files',
    tag: 'Covered',
    tagType: 'green' as const,
  },
  {
    label: 'Carbon additions',
    value: carbonPackageFiles.length.toString(),
    detail: 'Documented extra file',
    tag: 'Expected',
    tagType: 'purple' as const,
  },
];

export type PreflightRoute = {
  workflow: Workflow;
  assignmentMode?: 'network' | 'security' | 'storage' | 'wave';
  label: string;
  status: string;
  readinessFilter?: string;
};

export type AssignmentSuggestionKind = 'subnet' | 'securityGroup' | 'storage' | 'wave';

export type AssignmentSuggestion = {
  kind: AssignmentSuggestionKind;
  row: AssignmentVm;
  value: string;
  label: string;
  reason: string;
  confidence: SuggestionConfidence;
  score: number;
  evidence: string[];
};

export type RemediationQueueItem =
  | {
    id: string;
    source: 'preflight';
    severity: 'blocker' | 'warning' | 'info';
    title: string;
    subject: string;
    detail: string;
    tag: string;
    tagType: 'red' | 'warm-gray' | 'gray';
    route: PreflightRoute;
    finding: PreflightResponse['findings'][number];
  }
  | {
    id: string;
    source: 'vm-gap';
    severity: 'blocker';
    title: string;
    subject: string;
    detail: string;
    tag: string;
    tagType: 'red' | 'warm-gray' | 'gray';
    row: AssignmentVm;
    mode: 'network' | 'security' | 'storage' | 'wave';
  }
  | {
    id: string;
    source: 'plan-gap';
    severity: 'blocker';
    title: string;
    subject: string;
    detail: string;
    tag: string;
    tagType: 'red' | 'warm-gray' | 'gray';
    workflow: Workflow;
    assignmentMode?: 'network' | 'security' | 'storage' | 'wave';
    status: string;
  };

export const suggestionLabels: Record<AssignmentSuggestionKind, string> = {
  subnet: 'subnet',
  securityGroup: 'security group',
  storage: 'storage/IOPS',
  wave: 'wave',
};

export function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

export function readFileText(file: File): Promise<string> {
  if (typeof file.text === 'function') {
    return file.text();
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('Could not read planning state file.'));
    reader.readAsText(file);
  });
}

export function tokenize(value: string | undefined) {
  return new Set(
    (value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .split(/\s+/)
      .map((token) => token.replace(/\d+$/, ''))
      .filter((token) => token.length > 1),
  );
}

export function sharedTokenCount(target: AssignmentVm, candidate: AssignmentVm) {
  const targetTokens = tokenize([
    target.name,
    target.application,
    target.network,
    target.owner,
    target.cutoverGroup,
    target.dependencyGroup,
  ].join(' '));
  const candidateTokens = tokenize([
    candidate.name,
    candidate.application,
    candidate.network,
    candidate.owner,
    candidate.cutoverGroup,
    candidate.dependencyGroup,
  ].join(' '));
  return Array.from(targetTokens).filter((token) => candidateTokens.has(token)).length;
}

export function confidenceFromScore(score: number): SuggestionConfidence {
  if (score >= 7) return 'High';
  if (score >= 3) return 'Medium';
  return 'Low';
}

export function confidenceTagType(confidence: SuggestionConfidence) {
  if (confidence === 'High') return 'green' as const;
  if (confidence === 'Medium') return 'blue' as const;
  return 'warm-gray' as const;
}

export function rowAssignmentValue(row: AssignmentVm, kind: AssignmentSuggestionKind) {
  if (kind === 'subnet') return row.subnet;
  if (kind === 'securityGroup') return row.securityGroup;
  if (kind === 'storage') return row.overrideStorageTier || row.storageTier;
  return row.wave;
}

export function suggestionKey(suggestion: AssignmentSuggestion) {
  return `${suggestion.row.id}:${suggestion.kind}:${suggestion.value}`;
}

export function suggestionKindForMode(mode: 'network' | 'security' | 'storage' | 'wave'): AssignmentSuggestionKind {
  if (mode === 'network') return 'subnet';
  if (mode === 'security') return 'securityGroup';
  if (mode === 'storage') return 'storage';
  return 'wave';
}

export function planningGapLabel(mode: 'network' | 'security' | 'storage' | 'wave') {
  if (mode === 'network') return 'subnet';
  if (mode === 'security') return 'security group';
  if (mode === 'storage') return 'storage/IOPS';
  return 'wave';
}

export function buildAuditId(row: AssignmentVm, kind: AssignmentSuggestionKind, value: string) {
  return `${row.id}-${kind}-${value}-${Date.now()}`;
}

export type PlanningCompleteness = {
  missingSubnet: number;
  missingSg: number;
  missingStorage: number;
  missingWave: number;
  missingCidr: number;
  invalidLabels: number;
};

export function routeStatus(
  finding: PreflightResponse['findings'][number],
  fallback: string,
) {
  const action = finding['Suggested Action'];
  return action ? `${fallback} ${action}` : fallback;
}

export function primaryRouteForFinding(
  finding: PreflightResponse['findings'][number],
): PreflightRoute {
  const category = finding.Category;
  const quickFixType = finding['Quick Fix Type'];
  const field = finding.Field;
  const fixLocation = finding['Fix Location'];
  if (category === 'custom_image' || quickFixType === 'image_placeholder') {
    return {
      workflow: 'imageImport',
      label: 'Open image planning',
      status: routeStatus(finding, `Review image import planning for ${finding.Subject}.`),
    };
  }
  if (category === 'readiness' || fixLocation.includes('Readiness tab')) {
    return {
      workflow: 'remediation',
      label: 'Open remediation',
      readinessFilter: 'Blocked',
      status: routeStatus(finding, `Review remediation blockers for ${finding.Subject}.`),
    };
  }
  if (category === 'cidr') {
    return {
      workflow: 'network',
      assignmentMode: 'network',
      label: 'Open subnet CIDRs',
      status: routeStatus(finding, `Review subnet CIDR planning for ${finding.Subject}.`),
    };
  }
  if (category === 'network_mapping') {
    return {
      workflow: 'assignment',
      assignmentMode: 'network',
      label: 'Open network assignment',
      status: routeStatus(finding, `Review network placement for ${finding.Subject}.`),
    };
  }
  if (category === 'security_group') {
    return {
      workflow: 'security',
      assignmentMode: 'security',
      label: 'Open security plan',
      status: routeStatus(finding, `Review security planning for ${finding.Subject}.`),
    };
  }
  if (category === 'storage' || field === 'Override Storage Tier') {
    return {
      workflow: 'overrides',
      assignmentMode: 'storage',
      label: 'Open storage override',
      status: routeStatus(finding, `Review storage override for ${finding.Subject}.`),
    };
  }
  if (category === 'profile' || category === 'profile_region' || field === 'Override Profile') {
    return {
      workflow: 'overrides',
      label: 'Open VM overrides',
      status: routeStatus(finding, `Review profile override for ${finding.Subject}.`),
    };
  }
  if (quickFixType === 'exclude_vm' || quickFixType === 'include_vm' || field === 'Exclude?') {
    return {
      workflow: 'overrides',
      label: 'Open scope decision',
      status: routeStatus(finding, `Review include/exclude decision for ${finding.Subject}.`),
    };
  }
  if (category === 'terraform_names' && fixLocation.includes('Networks')) {
    return {
      workflow: 'network',
      assignmentMode: 'network',
      label: 'Open network plan',
      status: routeStatus(finding, `Review network naming for ${finding.Subject}.`),
    };
  }
  return {
    workflow: 'assignment',
    label: 'Open VM assignment',
    status: routeStatus(finding, `Review package finding for ${finding.Subject}.`),
  };
}

export function routesForFinding(
  finding: PreflightResponse['findings'][number],
): PreflightRoute[] {
  const routes = [primaryRouteForFinding(finding)];
  const quickFixType = finding['Quick Fix Type'];
  const hasScopeRoute = routes.some((route) => route.label === 'Open scope decision');
  if ((quickFixType === 'exclude_vm' || quickFixType === 'include_vm') && !hasScopeRoute) {
    routes.push({
      workflow: 'overrides',
      label: 'Review scope decision',
      status: routeStatus(finding, `Review include/exclude decision for ${finding.Subject}.`),
    });
  }
  return routes;
}

export function preflightQueueItem(
  finding: PreflightResponse['findings'][number],
  index: number,
): RemediationQueueItem {
  const route = routesForFinding(finding)[0];
  const severity = finding.Severity === 'blocker' || finding.Severity === 'warning'
    ? finding.Severity
    : 'info';
  return {
    id: `preflight-${finding.Severity}-${finding.Category}-${finding.Subject}-${index}`,
    source: 'preflight',
    severity,
    title: severity === 'blocker' ? 'Preflight blocker' : severity === 'warning' ? 'Preflight warning' : 'Preflight info',
    subject: finding.Subject || 'Package',
    detail: finding.Message || route.status,
    tag: finding.Category.replace(/_/g, ' '),
    tagType: severity === 'blocker' ? 'red' : severity === 'warning' ? 'warm-gray' : 'gray',
    route,
    finding,
  };
}

export function buildRemediationQueue(params: {
  preflightFindings: PreflightResponse['findings'];
  assignmentRows: AssignmentVm[];
  planningCompleteness: PlanningCompleteness;
}): RemediationQueueItem[] {
  const { preflightFindings, assignmentRows, planningCompleteness } = params;
  return [
    ...preflightFindings
      .filter((finding) => finding.Severity === 'blocker')
      .map(preflightQueueItem),
    ...assignmentRows
      .filter((row) => !row.subnet)
      .map((row) => ({
        id: `missing-subnet-${row.id}`,
        source: 'vm-gap' as const,
        severity: 'blocker' as const,
        title: 'Missing subnet assignment',
        subject: row.name,
        detail: 'Select the target subnet before Terraform export.',
        tag: 'subnet',
        tagType: 'red' as const,
        row,
        mode: 'network' as const,
      })),
    ...assignmentRows
      .filter((row) => !row.securityGroup)
      .map((row) => ({
        id: `missing-security-${row.id}`,
        source: 'vm-gap' as const,
        severity: 'blocker' as const,
        title: 'Missing security group assignment',
        subject: row.name,
        detail: 'Select the target security group before Terraform export.',
        tag: 'security group',
        tagType: 'red' as const,
        row,
        mode: 'security' as const,
      })),
    ...assignmentRows
      .filter((row) => !row.overrideStorageTier && !row.storageTier)
      .map((row) => ({
        id: `missing-storage-${row.id}`,
        source: 'vm-gap' as const,
        severity: 'blocker' as const,
        title: 'Missing storage/IOPS assignment',
        subject: row.name,
        detail: 'Select or override the storage tier before Terraform export.',
        tag: 'storage/IOPS',
        tagType: 'red' as const,
        row,
        mode: 'storage' as const,
      })),
    ...assignmentRows
      .filter((row) => !row.wave)
      .map((row) => ({
        id: `missing-wave-${row.id}`,
        source: 'vm-gap' as const,
        severity: 'blocker' as const,
        title: 'Missing wave assignment',
        subject: row.name,
        detail: 'Place the VM in a migration wave before Terraform export.',
        tag: 'wave',
        tagType: 'red' as const,
        row,
        mode: 'wave' as const,
      })),
    ...(planningCompleteness.missingCidr > 0 ? [{
      id: 'missing-subnet-cidrs',
      source: 'plan-gap' as const,
      severity: 'blocker' as const,
      title: 'Subnets missing CIDR',
      subject: `${planningCompleteness.missingCidr} subnet(s)`,
      detail: 'Complete subnet CIDR values in the Network Plan.',
      tag: 'network plan',
      tagType: 'red' as const,
      workflow: 'network' as const,
      assignmentMode: 'network' as const,
      status: 'Resolve subnet CIDR planning gaps before export.',
    }] : []),
    ...(planningCompleteness.invalidLabels > 0 ? [{
      id: 'invalid-terraform-labels',
      source: 'plan-gap' as const,
      severity: 'blocker' as const,
      title: 'Labels need Terraform cleanup',
      subject: `${planningCompleteness.invalidLabels} label(s)`,
      detail: 'Update labels so generated Terraform resource names are stable.',
      tag: 'naming',
      tagType: 'red' as const,
      workflow: 'network' as const,
      assignmentMode: 'network' as const,
      status: 'Resolve Terraform label cleanup findings before export.',
    }] : []),
    ...preflightFindings
      .filter((finding) => finding.Severity !== 'blocker')
      .map(preflightQueueItem),
  ];
}
