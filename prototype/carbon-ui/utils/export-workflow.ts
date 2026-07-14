import type {
  AssignmentVm,
  ResourceState,
  SuggestionAuditEntry,
  SuggestionConfidence,
  Workflow,
} from '../types/network-planning';
import type { PreflightResponse } from '../hooks/useApi';
import {
  carbonPackageFiles,
  handoffPackageFiles,
  packageFileCount,
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

export function inferAssignmentSuggestion(params: {
  row: AssignmentVm;
  kind: AssignmentSuggestionKind;
  assignmentRows: AssignmentVm[];
  resources: ResourceState;
}): AssignmentSuggestion | null {
  const { row, kind, assignmentRows, resources } = params;
  const existing = rowAssignmentValue(row, kind);
  if (existing) return null;

  const scoredRows = assignmentRows
    .filter((candidate) => candidate.id !== row.id && rowAssignmentValue(candidate, kind))
    .map((candidate) => {
      let score = sharedTokenCount(row, candidate);
      const evidence: string[] = [];
      const sharedTokens = sharedTokenCount(row, candidate);
      if (sharedTokens > 0) {
        evidence.push(`Shared VM naming/planning tokens with ${candidate.name}`);
      }
      if (row.application && candidate.application && row.application === candidate.application) {
        score += 3;
        evidence.push(`Same application: ${row.application}`);
      }
      if (row.network && candidate.network && row.network === candidate.network) {
        score += 3;
        evidence.push(`Same source network: ${row.network}`);
      }
      if (row.owner && candidate.owner && row.owner === candidate.owner) {
        score += 2;
        evidence.push(`Same owner: ${row.owner}`);
      }
      if (row.cutoverGroup && candidate.cutoverGroup && row.cutoverGroup === candidate.cutoverGroup) {
        score += 2;
        evidence.push(`Same cutover group: ${row.cutoverGroup}`);
      }
      return { candidate, score, evidence };
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score);

  const matched = scoredRows[0];
  const matchedRow = matched?.candidate;
  if (matchedRow && matched) {
    const value = rowAssignmentValue(matchedRow, kind);
    return {
      kind,
      row,
      value,
      label: value,
      reason: `Matches ${matchedRow.name} by VM naming or planning metadata.`,
      confidence: confidenceFromScore(matched.score),
      score: matched.score,
      evidence: matched.evidence,
    };
  }

  const rowTokens = tokenize(`${row.name} ${row.application} ${row.network}`);
  if (kind === 'subnet') {
    const match = resources.subnets
      .map((subnet) => ({
        subnet,
        score: Array.from(rowTokens).filter((token) =>
          tokenize(`${subnet.name} ${subnet.purpose}`).has(token),
        ).length,
      }))
      .sort((a, b) => b.score - a.score)[0];
    if (match?.score > 0) {
      return {
        kind,
        row,
        value: match.subnet.name,
        label: match.subnet.name,
        reason: `Matches subnet name or purpose for ${row.name}.`,
        confidence: confidenceFromScore(match.score),
        score: match.score,
        evidence: [`Matched subnet name or purpose: ${match.subnet.name}`],
      };
    }
  }
  if (kind === 'securityGroup') {
    const match = resources.securityGroups
      .map((securityGroup) => ({
        securityGroup,
        score: Array.from(rowTokens).filter((token) =>
          tokenize(`${securityGroup.name} ${securityGroup.purpose}`).has(token),
        ).length,
      }))
      .sort((a, b) => b.score - a.score)[0];
    if (match?.score > 0) {
      return {
        kind,
        row,
        value: match.securityGroup.name,
        label: match.securityGroup.name,
        reason: `Matches security group name or purpose for ${row.name}.`,
        confidence: confidenceFromScore(match.score),
        score: match.score,
        evidence: [`Matched security group name or purpose: ${match.securityGroup.name}`],
      };
    }
  }
  if (kind === 'storage') {
    const match = resources.storageProfiles.find((profile) => profile.tier === row.storageTier)
      || resources.storageProfiles.find((profile) => profile.name.toLowerCase().includes(row.application.toLowerCase()));
    if (match) {
      return {
        kind,
        row,
        value: match.tier,
        label: `${match.name} (${match.tier})`,
        reason: `Matches the VM storage tier or application profile.`,
        confidence: row.storageTier === match.tier ? 'Medium' : 'Low',
        score: row.storageTier === match.tier ? 3 : 1,
        evidence: row.storageTier === match.tier
          ? [`Same storage tier: ${row.storageTier}`]
          : [`Matched storage profile name: ${match.name}`],
      };
    }
  }
  if (kind === 'wave' && resources.waves.length === 1) {
    return {
      kind,
      row,
      value: resources.waves[0].name,
      label: resources.waves[0].name,
      reason: 'Only one migration wave is defined.',
      confidence: 'Low',
      score: 1,
      evidence: ['Only one migration wave is defined.'],
    };
  }
  return null;
}

export function buildAssignmentSuggestions(params: {
  assignmentRows: AssignmentVm[];
  resources: ResourceState;
  limit?: number;
}) {
  const { assignmentRows, resources, limit = 6 } = params;
  const suggestions: AssignmentSuggestion[] = [];
  for (const row of assignmentRows) {
    for (const kind of ['subnet', 'securityGroup', 'storage', 'wave'] as const) {
      const suggestion = inferAssignmentSuggestion({ row, kind, assignmentRows, resources });
      if (suggestion) suggestions.push(suggestion);
    }
  }
  return suggestions.slice(0, limit);
}

export function applySuggestionsToRows(
  assignmentRows: AssignmentVm[],
  suggestions: AssignmentSuggestion[],
) {
  const suggestionByRowAndKind = new Map(
    suggestions.map((suggestion) => [`${suggestion.row.id}:${suggestion.kind}`, suggestion]),
  );
  return assignmentRows.map((row) => {
    let nextRow = row;
    for (const kind of ['subnet', 'securityGroup', 'storage', 'wave'] as const) {
      const suggestion = suggestionByRowAndKind.get(`${row.id}:${kind}`);
      if (!suggestion) continue;
      if (kind === 'subnet') nextRow = { ...nextRow, subnet: suggestion.value };
      if (kind === 'securityGroup') nextRow = { ...nextRow, securityGroup: suggestion.value };
      if (kind === 'storage') nextRow = { ...nextRow, storageTier: suggestion.value };
      if (kind === 'wave') nextRow = { ...nextRow, wave: suggestion.value };
    }
    return nextRow;
  });
}

export function suggestionAuditEntries(
  suggestions: AssignmentSuggestion[],
  appliedAt: string,
) {
  return suggestions.map((suggestion) => ({
    id: buildAuditId(suggestion.row, suggestion.kind, suggestion.value),
    vmId: suggestion.row.id,
    vmName: suggestion.row.name,
    field: suggestion.kind,
    oldValue: rowAssignmentValue(suggestion.row, suggestion.kind),
    newValue: suggestion.value,
    confidence: suggestion.confidence,
    reason: suggestion.reason,
    evidence: suggestion.evidence,
    appliedAt,
  }));
}

export function suggestionKindForFinding(
  finding: PreflightResponse['findings'][number],
): AssignmentSuggestionKind | null {
  const category = finding.Category;
  const field = String(finding.Field || '').toLowerCase();
  if (category === 'network_mapping' || field.includes('subnet')) return 'subnet';
  if (category === 'security_group' || field.includes('security')) return 'securityGroup';
  if (category === 'storage' || field.includes('storage') || field.includes('iops')) return 'storage';
  if (category === 'wave' || field.includes('wave')) return 'wave';
  return null;
}

export function suggestionForFinding(params: {
  finding: PreflightResponse['findings'][number];
  assignmentRows: AssignmentVm[];
  resources: ResourceState;
}) {
  const { finding, assignmentRows, resources } = params;
  const matchingVm = assignmentRows.find((row) =>
    row.name === finding.Subject || row.id === finding.Subject,
  );
  const kind = suggestionKindForFinding(finding);
  return matchingVm && kind
    ? inferAssignmentSuggestion({ row: matchingVm, kind, assignmentRows, resources })
    : null;
}

export function suggestionForQueueItem(params: {
  item: RemediationQueueItem;
  assignmentRows: AssignmentVm[];
  resources: ResourceState;
}) {
  const { item, assignmentRows, resources } = params;
  if (item.source === 'preflight') {
    return suggestionForFinding({ finding: item.finding, assignmentRows, resources });
  }
  if (item.source === 'vm-gap') {
    return inferAssignmentSuggestion({
      row: item.row,
      kind: suggestionKindForMode(item.mode),
      assignmentRows,
      resources,
    });
  }
  return null;
}

export function revertSuggestionInRows(
  assignmentRows: AssignmentVm[],
  entry: SuggestionAuditEntry,
) {
  return assignmentRows.map((row) => {
    if (row.id !== entry.vmId) return row;
    if (entry.field === 'subnet') return { ...row, subnet: entry.oldValue };
    if (entry.field === 'securityGroup') return { ...row, securityGroup: entry.oldValue };
    if (entry.field === 'storage') return { ...row, storageTier: entry.oldValue };
    return { ...row, wave: entry.oldValue };
  });
}

export function markSuggestionAuditReverted(
  suggestionAudit: SuggestionAuditEntry[],
  entryId: string,
  revertedAt: string,
) {
  return suggestionAudit.map((candidate) =>
    candidate.id === entryId
      ? { ...candidate, revertedAt }
      : candidate,
  );
}

export type ExportChecklistItem = {
  label: string;
  complete: boolean;
};

export type PreviewFile = {
  path: string;
  category: string;
  size_bytes: number;
  content: string;
};

export function calculatePlanningCompleteness(params: {
  assignmentRows: AssignmentVm[];
  resources: ResourceState;
}) {
  const { assignmentRows, resources } = params;
  const missingSubnet = assignmentRows.filter((row) => !row.subnet).length;
  const missingSg = assignmentRows.filter((row) => !row.securityGroup).length;
  const missingStorage = assignmentRows.filter((row) => !row.overrideStorageTier && !row.storageTier).length;
  const missingWave = assignmentRows.filter((row) => !row.wave).length;
  const missingCidr = resources.subnets.filter((subnet) => !subnet.cidr).length;
  const invalidLabels = [
    ...resources.vpcs,
    ...resources.subnets,
    ...resources.securityGroups,
    ...resources.storageProfiles,
    ...(resources.networkComponents || []),
  ].filter((bucket) => !bucket.label || bucket.label !== terraformLabel(bucket.label)).length;
  return { missingSubnet, missingSg, missingStorage, missingWave, missingCidr, invalidLabels };
}

export function planningFindings(planningCompleteness: PlanningCompleteness): [string, number][] {
  return [
    ['Missing subnet assignments', planningCompleteness.missingSubnet],
    ['Missing security group assignments', planningCompleteness.missingSg],
    ['Missing storage/IOPS assignments', planningCompleteness.missingStorage],
    ['Missing wave assignments', planningCompleteness.missingWave],
    ['Subnets missing CIDR', planningCompleteness.missingCidr],
    ['Labels needing Terraform cleanup', planningCompleteness.invalidLabels],
  ];
}

export function buildExportChecklist(params: {
  selectedProjectId: string;
  isDirty: boolean;
  planningCompleteness: PlanningCompleteness;
  hasPreflight: boolean;
}): ExportChecklistItem[] {
  const { selectedProjectId, isDirty, planningCompleteness, hasPreflight } = params;
  return [
    {
      label: 'Network plan saved',
      complete: !!selectedProjectId && !isDirty,
    },
    {
      label: 'VM assignments complete',
      complete: planningCompleteness.missingSubnet === 0 && planningCompleteness.missingSg === 0,
    },
    {
      label: 'Overrides reviewed',
      complete: planningCompleteness.missingStorage === 0,
    },
    {
      label: 'Wave plan complete',
      complete: planningCompleteness.missingWave === 0,
    },
    {
      label: 'Subnet CIDRs complete',
      complete: planningCompleteness.missingCidr === 0,
    },
    {
      label: 'Backend preflight run',
      complete: hasPreflight,
    },
  ];
}

export function previewCategories(files: PreviewFile[] = []) {
  const categories = new Set(files.map((file) => file.category));
  return ['All', ...Array.from(categories)];
}

export function filterPreviewFiles(params: {
  files: PreviewFile[];
  category: string;
  search: string;
}) {
  const query = params.search.trim().toLowerCase();
  return params.files.filter((file) => {
    const matchesCategory = params.category === 'All' || file.category === params.category;
    const matchesSearch = !query || file.path.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });
}

export function previewFileSizeLabel(file?: PreviewFile) {
  return file ? `${Math.max(1, Math.ceil(file.size_bytes / 1024))} KB` : '';
}

export function handoffCsvFileCount(files: PreviewFile[] = []) {
  return files.filter((file) =>
    file.category === 'Migration handoff' && file.path.endsWith('.csv'),
  ).length;
}

export function readinessReportPayload(params: {
  generatedAt: string;
  selectedProjectId: string;
  projectName: string;
  workbookFilename?: string | null;
  activeAssignmentGapCount: number;
  preflight?: PreflightResponse | null;
  exportChecklist: ExportChecklistItem[];
  findings: [string, number][];
  assignmentSuggestions: AssignmentSuggestion[];
  suggestionAudit: SuggestionAuditEntry[];
}) {
  const {
    generatedAt,
    selectedProjectId,
    projectName,
    workbookFilename,
    activeAssignmentGapCount,
    preflight,
    exportChecklist,
    findings,
    assignmentSuggestions,
    suggestionAudit,
  } = params;
  return {
    schema_version: 'carbon-export-readiness-report-1.0',
    generated_at: generatedAt,
    project: {
      id: selectedProjectId || null,
      name: projectName,
      workbook: workbookFilename || null,
    },
    readiness: {
      status: activeAssignmentGapCount === 0 && (preflight?.summary.blockers || 0) === 0 ? 'Ready' : 'Needs review',
      checklist: exportChecklist,
      planning_gaps: Object.fromEntries(findings.map(([label, count]) => [label, count])),
    },
    preflight: preflight
      ? {
        summary: preflight.summary,
        findings: preflight.findings,
      }
      : null,
    suggestions: {
      available: assignmentSuggestions.map((suggestion) => ({
        vm_id: suggestion.row.id,
        vm_name: suggestion.row.name,
        field: suggestion.kind,
        suggested_value: suggestion.value,
        label: suggestion.label,
        confidence: suggestion.confidence,
        score: suggestion.score,
        reason: suggestion.reason,
        evidence: suggestion.evidence,
      })),
      audit: suggestionAudit,
    },
    package_inventory: {
      total_files: packageFileCount,
      terraform_files: terraformPackageFiles.length,
      handoff_files: handoffPackageFiles.length,
      carbon_state_files: carbonPackageFiles.length,
    },
  };
}

export function downloadBrowserFile(params: {
  blob: Blob;
  filename: string;
  documentRef?: Document;
  urlRef?: typeof window.URL;
}) {
  const documentTarget = params.documentRef || document;
  const urlTarget = params.urlRef || window.URL;
  const url = urlTarget.createObjectURL(params.blob);
  const link = documentTarget.createElement('a');
  link.href = url;
  link.download = params.filename;
  documentTarget.body.appendChild(link);
  link.click();
  urlTarget.revokeObjectURL(url);
  documentTarget.body.removeChild(link);
}
