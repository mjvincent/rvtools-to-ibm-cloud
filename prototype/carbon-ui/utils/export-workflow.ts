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
