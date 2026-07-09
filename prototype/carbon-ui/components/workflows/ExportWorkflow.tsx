'use client';

import React, { useMemo, useRef, useState } from 'react';
import { Button, Checkbox, InlineNotification, Layer, Search, Select, SelectItem, Tag, Tile } from '@carbon/react';
import { Close, CloudUpload, Download, Renew, View } from '@carbon/icons-react';
import { useAppState } from '../../store/AppContext';
import type { AssignmentVm, SuggestionConfidence, Workflow } from '../../types/network-planning';
import {
  generateTerraform,
  previewTerraform,
  runProjectPreflight,
  saveNetworkPlan,
  type PreflightResponse,
  type TerraformPreviewResponse,
} from '../../hooks/useApi';
import {
  carbonPackageFiles,
  handoffPackageFiles,
  packageFileCount,
  terraformPackageFiles,
} from '../../utils/package-inventory';
import {
  buildNetworkPlanBody,
  exportNetworkPlanJson,
  parseNetworkPlanJson,
  resourcesFromNetworkPlan,
  rowsFromNetworkPlan,
} from '../../utils/planning-state';

const packageGroups = [
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

const packageParitySummary = [
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

function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

function readFileText(file: File): Promise<string> {
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

type PreflightRoute = {
  workflow: Workflow;
  assignmentMode?: 'network' | 'security' | 'storage' | 'wave';
  label: string;
  status: string;
  readinessFilter?: string;
};

type AssignmentSuggestionKind = 'subnet' | 'securityGroup' | 'storage' | 'wave';

type AssignmentSuggestion = {
  kind: AssignmentSuggestionKind;
  row: AssignmentVm;
  value: string;
  label: string;
  reason: string;
  confidence: SuggestionConfidence;
  score: number;
  evidence: string[];
};

type RemediationQueueItem =
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

const suggestionLabels: Record<AssignmentSuggestionKind, string> = {
  subnet: 'subnet',
  securityGroup: 'security group',
  storage: 'storage/IOPS',
  wave: 'wave',
};

function tokenize(value: string | undefined) {
  return new Set(
    (value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .split(/\s+/)
      .map((token) => token.replace(/\d+$/, ''))
      .filter((token) => token.length > 1),
  );
}

function sharedTokenCount(target: AssignmentVm, candidate: AssignmentVm) {
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

function confidenceFromScore(score: number): SuggestionConfidence {
  if (score >= 7) return 'High';
  if (score >= 3) return 'Medium';
  return 'Low';
}

function confidenceTagType(confidence: SuggestionConfidence) {
  if (confidence === 'High') return 'green' as const;
  if (confidence === 'Medium') return 'blue' as const;
  return 'warm-gray' as const;
}

function rowAssignmentValue(row: AssignmentVm, kind: AssignmentSuggestionKind) {
  if (kind === 'subnet') return row.subnet;
  if (kind === 'securityGroup') return row.securityGroup;
  if (kind === 'storage') return row.overrideStorageTier || row.storageTier;
  return row.wave;
}

function suggestionKey(suggestion: AssignmentSuggestion) {
  return `${suggestion.row.id}:${suggestion.kind}:${suggestion.value}`;
}

function suggestionKindForMode(mode: 'network' | 'security' | 'storage' | 'wave'): AssignmentSuggestionKind {
  if (mode === 'network') return 'subnet';
  if (mode === 'security') return 'securityGroup';
  if (mode === 'storage') return 'storage';
  return 'wave';
}

function planningGapLabel(mode: 'network' | 'security' | 'storage' | 'wave') {
  if (mode === 'network') return 'subnet';
  if (mode === 'security') return 'security group';
  if (mode === 'storage') return 'storage/IOPS';
  return 'wave';
}

function buildAuditId(row: AssignmentVm, kind: AssignmentSuggestionKind, value: string) {
  return `${row.id}-${kind}-${value}-${Date.now()}`;
}

export default function ExportWorkflow() {
  const { state, dispatch } = useAppState();
  const planningStateInputRef = useRef<HTMLInputElement>(null);
  const [preflight, setPreflight] = useState<PreflightResponse | null>(null);
  const [runningPreflight, setRunningPreflight] = useState(false);
  const [terraformPreview, setTerraformPreview] = useState<TerraformPreviewResponse | null>(null);
  const [selectedPreviewPath, setSelectedPreviewPath] = useState('');
  const [previewSearch, setPreviewSearch] = useState('');
  const [previewCategory, setPreviewCategory] = useState('All');
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [selectedQueueSuggestionIds, setSelectedQueueSuggestionIds] = useState<string[]>([]);
  const {
    assignmentRows,
    resources,
    selectedProjectId,
    projectName,
    summary,
    terraformStatus,
    terraformError,
    generatingTerraform,
    suggestionAudit,
  } = state;

  const planningCompleteness = useMemo(() => {
    const total = assignmentRows.length || 1;
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
  }, [assignmentRows, resources]);

  const findings: [string, number][] = [
    ['Missing subnet assignments', planningCompleteness.missingSubnet],
    ['Missing security group assignments', planningCompleteness.missingSg],
    ['Missing storage/IOPS assignments', planningCompleteness.missingStorage],
    ['Missing wave assignments', planningCompleteness.missingWave],
    ['Subnets missing CIDR', planningCompleteness.missingCidr],
    ['Labels needing Terraform cleanup', planningCompleteness.invalidLabels],
  ];
  const blockingFindingCount = findings.reduce((total, [, count]) => total + count, 0);
  const preflightSummary = preflight?.summary;
  const visiblePreflightFindings = preflight?.findings.slice(0, 5) || [];
  const exportChecklist = [
    {
      label: 'Network plan saved',
      complete: !!selectedProjectId && !state.isDirty,
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
      complete: !!preflight,
    },
  ];
  const exportChecklistComplete = exportChecklist.filter((item) => item.complete).length;
  const selectedPreviewFile = terraformPreview?.files.find((file) =>
    file.path === selectedPreviewPath,
  ) || terraformPreview?.files[0];
  const previewCategories = useMemo(() => {
    const categories = new Set(terraformPreview?.files.map((file) => file.category) || []);
    return ['All', ...Array.from(categories)];
  }, [terraformPreview]);
  const filteredPreviewFiles = useMemo(() => {
    const query = previewSearch.trim().toLowerCase();
    return terraformPreview?.files.filter((file) => {
      const matchesCategory = previewCategory === 'All' || file.category === previewCategory;
      const matchesSearch = !query || file.path.toLowerCase().includes(query);
      return matchesCategory && matchesSearch;
    }) || [];
  }, [previewCategory, previewSearch, terraformPreview]);
  const selectedPreviewSize = selectedPreviewFile
    ? `${Math.max(1, Math.ceil(selectedPreviewFile.size_bytes / 1024))} KB`
    : '';
  const handoffCsvCount = terraformPreview?.files.filter((file) =>
    file.category === 'Migration handoff' && file.path.endsWith('.csv'),
  ).length || 0;

  function inferAssignmentSuggestion(
    row: AssignmentVm,
    kind: AssignmentSuggestionKind,
  ): AssignmentSuggestion | null {
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

  const assignmentSuggestions = useMemo(() => {
    const suggestions: AssignmentSuggestion[] = [];
    for (const row of assignmentRows) {
      for (const kind of ['subnet', 'securityGroup', 'storage', 'wave'] as const) {
        const suggestion = inferAssignmentSuggestion(row, kind);
        if (suggestion) suggestions.push(suggestion);
      }
    }
    return suggestions.slice(0, 6);
  // inferAssignmentSuggestion intentionally closes over current resources and rows.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assignmentRows, resources]);
  const highConfidenceSuggestions = assignmentSuggestions.filter((suggestion) => suggestion.confidence === 'High');
  const recentSuggestionAudit = suggestionAudit.slice(0, 6);
  const activeAuditCount = suggestionAudit.filter((entry) => !entry.revertedAt).length;
  const activeAssignmentGapCount = findings.reduce((total, [, count]) => total + count, 0);

  function applyAssignmentSuggestions(suggestions: AssignmentSuggestion[]) {
    if (suggestions.length === 0) return;
    const suggestionByRowAndKind = new Map(
      suggestions.map((suggestion) => [`${suggestion.row.id}:${suggestion.kind}`, suggestion]),
    );
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => {
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
      }),
    });
    dispatch({
      type: 'APPEND_SUGGESTION_AUDIT',
      payload: suggestions.map((suggestion) => ({
        id: buildAuditId(suggestion.row, suggestion.kind, suggestion.value),
        vmId: suggestion.row.id,
        vmName: suggestion.row.name,
        field: suggestion.kind,
        oldValue: rowAssignmentValue(suggestion.row, suggestion.kind),
        newValue: suggestion.value,
        confidence: suggestion.confidence,
        reason: suggestion.reason,
        evidence: suggestion.evidence,
        appliedAt: new Date().toISOString(),
      })),
    });
    const highConfidenceCount = suggestions.filter((suggestion) => suggestion.confidence === 'High').length;
    dispatch({
      type: 'SET_TERRAFORM_STATUS',
      payload: suggestions.length === 1
        ? `Applied suggested ${suggestionLabels[suggestions[0].kind]} for ${suggestions[0].row.name}. Save the project to persist it.`
        : `Applied ${suggestions.length} suggested assignment(s), including ${highConfidenceCount} high-confidence item(s). Save the project to persist them.`,
    });
  }

  function applyAssignmentSuggestion(suggestion: AssignmentSuggestion) {
    applyAssignmentSuggestions([suggestion]);
  }

  function applyHighConfidenceSuggestions() {
    applyAssignmentSuggestions(assignmentSuggestions.filter((suggestion) => suggestion.confidence === 'High'));
  }

  function revertSuggestionAuditEntry(entryId: string) {
    const entry = suggestionAudit.find((candidate) => candidate.id === entryId);
    if (!entry || entry.revertedAt) return;
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: assignmentRows.map((row) => {
        if (row.id !== entry.vmId) return row;
        if (entry.field === 'subnet') return { ...row, subnet: entry.oldValue };
        if (entry.field === 'securityGroup') return { ...row, securityGroup: entry.oldValue };
        if (entry.field === 'storage') return { ...row, storageTier: entry.oldValue };
        return { ...row, wave: entry.oldValue };
      }),
    });
    dispatch({
      type: 'SET_SUGGESTION_AUDIT',
      payload: suggestionAudit.map((candidate) =>
        candidate.id === entryId
          ? { ...candidate, revertedAt: new Date().toISOString() }
          : candidate,
      ),
    });
    dispatch({
      type: 'SET_TERRAFORM_STATUS',
      payload: `Reverted suggested ${suggestionLabels[entry.field]} change for ${entry.vmName}. Save the project to persist it.`,
    });
  }

  function suggestionKindForFinding(
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

  function suggestionForFinding(finding: PreflightResponse['findings'][number]) {
    const matchingVm = assignmentRows.find((row) =>
      row.name === finding.Subject || row.id === finding.Subject,
    );
    const kind = suggestionKindForFinding(finding);
    return matchingVm && kind ? inferAssignmentSuggestion(matchingVm, kind) : null;
  }

  function routeStatus(finding: PreflightResponse['findings'][number], fallback: string) {
    const action = finding['Suggested Action'];
    return action ? `${fallback} ${action}` : fallback;
  }

  function primaryRouteForFinding(finding: PreflightResponse['findings'][number]): PreflightRoute {
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

  function routesForFinding(finding: PreflightResponse['findings'][number]): PreflightRoute[] {
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

  function openPreflightFinding(
    finding: PreflightResponse['findings'][number],
    route: PreflightRoute,
  ) {
    const matchingVm = assignmentRows.find((row) =>
      row.name === finding.Subject || row.id === finding.Subject,
    );
    if (matchingVm) {
      dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [matchingVm.id] });
      dispatch({ type: 'SET_SEARCH_VALUE', payload: matchingVm.name });
    } else {
      dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [] });
      dispatch({ type: 'SET_SEARCH_VALUE', payload: finding.Subject === 'package' ? '' : finding.Subject });
    }
    if (route.assignmentMode) {
      dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: route.assignmentMode });
    }
    if (route.readinessFilter) {
      dispatch({ type: 'SET_READINESS_FILTER', payload: route.readinessFilter });
    }
    dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: route.workflow });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: route.status });
  }

  function openVmPlanningGap(row: AssignmentVm, mode: 'network' | 'security' | 'storage' | 'wave') {
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [row.id] });
    dispatch({ type: 'SET_SEARCH_VALUE', payload: row.name });
    dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: mode });
    dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: mode === 'storage' ? 'overrides' : mode === 'wave' ? 'waves' : 'assignment' });
    dispatch({
      type: 'SET_PROJECT_STATUS',
      payload: `Resolve missing ${planningGapLabel(mode)} for ${row.name}.`,
    });
  }

  function openPlanGap(workflow: Workflow, status: string, assignmentMode?: 'network' | 'security' | 'storage' | 'wave') {
    if (assignmentMode) {
      dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: assignmentMode });
    }
    dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [] });
    dispatch({ type: 'SET_SEARCH_VALUE', payload: '' });
    dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: workflow });
    dispatch({ type: 'SET_PROJECT_STATUS', payload: status });
  }

  function preflightQueueItem(
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

  const remediationQueue: RemediationQueueItem[] = [
    ...(preflight?.findings || [])
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
    ...(preflight?.findings || [])
      .filter((finding) => finding.Severity !== 'blocker')
      .map(preflightQueueItem),
  ];
  const hasResolvableIssue = remediationQueue.length > 0;

  function suggestionForQueueItem(item: RemediationQueueItem) {
    if (item.source === 'preflight') {
      return suggestionForFinding(item.finding);
    }
    if (item.source === 'vm-gap') {
      return inferAssignmentSuggestion(item.row, suggestionKindForMode(item.mode));
    }
    return null;
  }

  const queueSuggestionEntries = remediationQueue
    .map((item) => {
      const suggestion = suggestionForQueueItem(item);
      return suggestion ? { item, suggestion, key: suggestionKey(suggestion) } : null;
    })
    .filter((entry): entry is { item: RemediationQueueItem; suggestion: AssignmentSuggestion; key: string } =>
      Boolean(entry),
    );
  const uniqueQueueSuggestionEntries = Array.from(
    new Map(queueSuggestionEntries.map((entry) => [entry.key, entry])).values(),
  );
  const selectedQueueSuggestions = uniqueQueueSuggestionEntries
    .filter((entry) => selectedQueueSuggestionIds.includes(entry.key))
    .map((entry) => entry.suggestion);
  const highConfidenceQueueSuggestionIds = uniqueQueueSuggestionEntries
    .filter((entry) => entry.suggestion.confidence === 'High')
    .map((entry) => entry.key);

  function toggleQueueSuggestion(suggestion: AssignmentSuggestion, checked: boolean) {
    const key = suggestionKey(suggestion);
    setSelectedQueueSuggestionIds((current) =>
      checked
        ? Array.from(new Set([...current, key]))
        : current.filter((candidate) => candidate !== key),
    );
  }

  function selectHighConfidenceQueueSuggestions() {
    setSelectedQueueSuggestionIds(highConfidenceQueueSuggestionIds);
  }

  function clearQueueSuggestionSelection() {
    setSelectedQueueSuggestionIds([]);
  }

  function applySelectedQueueSuggestions() {
    applyAssignmentSuggestions(selectedQueueSuggestions);
    setSelectedQueueSuggestionIds([]);
  }

  function reviewRemediationIssue(item: RemediationQueueItem) {
    if (item.source === 'preflight') {
      openPreflightFinding(item.finding, item.route);
      return;
    }
    if (item.source === 'vm-gap') {
      openVmPlanningGap(item.row, item.mode);
      return;
    }
    openPlanGap(item.workflow, item.status, item.assignmentMode);
  }

  function handleResolveNextIssue() {
    const nextIssue = remediationQueue[0];
    if (nextIssue) {
      reviewRemediationIssue(nextIssue);
      return;
    }
    dispatch({ type: 'SET_PROJECT_STATUS', payload: 'No unresolved export readiness issues found.' });
  }

  async function saveLatestNetworkPlan() {
    if (!selectedProjectId) throw new Error('Save or load a persisted project before exporting Terraform.');
    await saveNetworkPlan(
      selectedProjectId,
      buildNetworkPlanBody({ resources, assignmentRows, projectName, summary }),
    );
  }

  async function handleRunPreflight() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    setRunningPreflight(true);
    try {
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Saving latest network plan before preflight...' });
      await saveLatestNetworkPlan();
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Running package preflight...' });
      const result = await runProjectPreflight(selectedProjectId);
      setPreflight(result);
      dispatch({
        type: 'SET_TERRAFORM_STATUS',
        payload: `Preflight complete: ${result.summary.blockers} blocker(s), ${result.summary.warnings} warning(s).`,
      });
    } catch (error) {
      dispatch({
        type: 'SET_TERRAFORM_ERROR',
        payload: error instanceof Error ? error.message : 'Preflight check failed.',
      });
    } finally {
      setRunningPreflight(false);
    }
  }

  async function handlePreviewTerraform() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    setLoadingPreview(true);
    try {
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Saving latest network plan before preview...' });
      await saveLatestNetworkPlan();
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Generating Terraform preview...' });
      const result = await previewTerraform(selectedProjectId);
      setTerraformPreview(result);
      setSelectedPreviewPath(result.files[0]?.path || '');
      setPreviewSearch('');
      setPreviewCategory('All');
      dispatch({
        type: 'SET_TERRAFORM_STATUS',
        payload: `Package preview generated for ${result.files.length} file(s).`,
      });
    } catch (error) {
      dispatch({
        type: 'SET_TERRAFORM_ERROR',
        payload: error instanceof Error ? error.message : 'Terraform preview failed.',
      });
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleDownloadTerraform() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    dispatch({ type: 'SET_GENERATING_TERRAFORM', payload: true });
    try {
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Saving latest network plan before export preflight...' });
      await saveLatestNetworkPlan();
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Running package preflight before ZIP download...' });
      const preflightResult = await runProjectPreflight(selectedProjectId);
      setPreflight(preflightResult);
      if (preflightResult.summary.blockers > 0) {
        dispatch({
          type: 'SET_TERRAFORM_ERROR',
          payload: `Terraform ZIP blocked by ${preflightResult.summary.blockers} preflight blocker(s). Resolve or route the findings below, then try again.`,
        });
        return;
      }
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Generating Terraform ZIP...' });
      const blob = await generateTerraform(selectedProjectId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${projectName.replace(/\s+/g, '-')}-terraform-${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      dispatch({
        type: 'SET_TERRAFORM_STATUS',
        payload: preflightResult.summary.warnings > 0
          ? `Terraform ZIP downloaded with ${preflightResult.summary.warnings} warning(s).`
          : 'Terraform ZIP downloaded.',
      });
      dispatch({ type: 'SET_IS_DIRTY', payload: false });
    } catch (error) {
      dispatch({
        type: 'SET_TERRAFORM_ERROR',
        payload: error instanceof Error ? error.message : 'Terraform export failed.',
      });
    } finally {
      dispatch({ type: 'SET_GENERATING_TERRAFORM', payload: false });
    }
  }

  function downloadPreviewFile(file: TerraformPreviewResponse['files'][number]) {
    const blob = new Blob([file.content], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = file.path.replace(/\//g, '__');
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: `Downloaded ${file.path}.` });
  }

  function handleDownloadReadinessReport() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    const generatedAt = new Date().toISOString();
    const report = {
      schema_version: 'carbon-export-readiness-report-1.0',
      generated_at: generatedAt,
      project: {
        id: selectedProjectId || null,
        name: projectName,
        workbook: summary?.filename || null,
      },
      readiness: {
        status: activeAssignmentGapCount === 0 && (preflightSummary?.blockers || 0) === 0 ? 'Ready' : 'Needs review',
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
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${projectName.replace(/\s+/g, '-')}-carbon-export-readiness-${generatedAt.split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Export readiness report downloaded.' });
  }

  function showHandoffCsvs() {
    setPreviewCategory('Migration handoff');
    setPreviewSearch('.csv');
    const firstCsv = terraformPreview?.files.find((file) =>
      file.category === 'Migration handoff' && file.path.endsWith('.csv'),
    );
    if (firstCsv) {
      setSelectedPreviewPath(firstCsv.path);
    }
  }

  function handleExportPlanningState() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    const json = exportNetworkPlanJson({ resources, assignmentRows, projectName, summary });
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${projectName.replace(/\s+/g, '-')}-planning-state-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Planning state JSON downloaded.' });
  }

  async function handleImportPlanningState(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    try {
      const plan = parseNetworkPlanJson(await readFileText(file));
      const importedResources = resourcesFromNetworkPlan(plan);
      dispatch({ type: 'SET_RESOURCES', payload: importedResources });
      dispatch({
        type: 'SET_ASSIGNMENT_ROWS',
        payload: rowsFromNetworkPlan(plan, assignmentRows),
      });
      dispatch({
        type: 'SET_TERRAFORM_STATUS',
        payload: `Imported planning state from ${file.name}. Review and save the project to persist it.`,
      });
    } catch (error) {
      dispatch({
        type: 'SET_TERRAFORM_ERROR',
        payload: error instanceof Error ? error.message : 'Planning state import failed.',
      });
    }
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Export readiness</h2>
          <p>Review planning gaps, then save the latest Carbon network plan and download a Terraform ZIP from FastAPI.</p>
        </div>
        <div className="network-actions">
          <Tag type={blockingFindingCount === 0 ? 'green' : 'warm-gray'}>{blockingFindingCount === 0 ? 'Ready' : 'Needs review'}</Tag>
          <Button
            kind="tertiary"
            size="sm"
            renderIcon={Renew}
            disabled={!hasResolvableIssue}
            onClick={handleResolveNextIssue}
          >
            Resolve next issue
          </Button>
          <Button
            kind="tertiary"
            size="sm"
            renderIcon={CloudUpload}
            onClick={() => planningStateInputRef.current?.click()}
          >
            Import planning JSON
          </Button>
          <input
            ref={planningStateInputRef}
            aria-label="Import planning state JSON"
            type="file"
            accept="application/json,.json"
            className="sr-only"
            onChange={handleImportPlanningState}
          />
          <Button
            kind="secondary"
            size="sm"
            renderIcon={Download}
            onClick={handleExportPlanningState}
          >
            Export planning JSON
          </Button>
          <Button
            kind="secondary"
            size="sm"
            renderIcon={Download}
            onClick={handleDownloadReadinessReport}
          >
            Download readiness report
          </Button>
          <Button
            kind="secondary"
            size="sm"
            renderIcon={Renew}
            onClick={handleRunPreflight}
            disabled={!selectedProjectId || runningPreflight}
          >
            {runningPreflight ? 'Running...' : 'Run preflight'}
          </Button>
          <Button
            kind="secondary"
            size="sm"
            renderIcon={View}
            onClick={handlePreviewTerraform}
            disabled={!selectedProjectId || loadingPreview}
          >
            {loadingPreview ? 'Previewing...' : 'Preview Terraform'}
          </Button>
          <Button
            kind="primary"
            size="sm"
            renderIcon={Download}
            onClick={handleDownloadTerraform}
            disabled={!selectedProjectId || generatingTerraform}
          >
            {generatingTerraform ? 'Generating...' : 'Download Terraform ZIP'}
          </Button>
        </div>
      </div>
      {terraformStatus && (
        <InlineNotification
          kind="success"
          lowContrast
          title="Export status"
          subtitle={terraformStatus}
        />
      )}
      {terraformError && (
        <InlineNotification
          kind="error"
          lowContrast
          title="Export failed"
          subtitle={terraformError}
        />
      )}
      <div className="export-package">
        <div className="section-header compact">
          <div>
            <h2>Export checklist</h2>
            <p>{exportChecklistComplete}/{exportChecklist.length} readiness item(s) complete before Terraform handoff.</p>
          </div>
          <Tag type={exportChecklistComplete === exportChecklist.length ? 'green' : 'warm-gray'}>
            {exportChecklistComplete === exportChecklist.length ? 'Ready' : 'In progress'}
          </Tag>
        </div>
        <div className="resource-list">
          {exportChecklist.map((item) => (
            <Tile key={item.label} className="resource-tile">
              <div className="package-tile__header">
                <h3>{item.label}</h3>
                <Tag type={item.complete ? 'green' : 'warm-gray'}>
                  {item.complete ? 'Complete' : 'Needs review'}
                </Tag>
              </div>
            </Tile>
          ))}
        </div>
      </div>
      <div className="resource-list">
        {findings.map(([label, count]) => (
          <Tile key={label} className="resource-tile">
            <h3>{label}</h3>
            <p>{count === 0 ? 'Ready' : `${count} item(s) need attention`}</p>
          </Tile>
        ))}
      </div>
      <div className="export-package">
        <div className="section-header compact">
          <div>
            <h2>Remediation queue</h2>
            <p>{remediationQueue.length === 0 ? 'No unresolved export readiness issues.' : `${remediationQueue.length} issue(s) sorted by export priority.`}</p>
          </div>
          <div className="network-actions">
            <Tag type={remediationQueue.length === 0 ? 'green' : 'warm-gray'}>
              {remediationQueue.length === 0 ? 'Clear' : 'Action needed'}
            </Tag>
            <Tag type={uniqueQueueSuggestionEntries.length === 0 ? 'gray' : 'blue'}>
              {uniqueQueueSuggestionEntries.length} suggested
            </Tag>
            <Tag type={selectedQueueSuggestions.length === 0 ? 'gray' : 'green'}>
              {selectedQueueSuggestions.length} selected
            </Tag>
            <Button
              kind="tertiary"
              size="sm"
              disabled={highConfidenceQueueSuggestionIds.length === 0}
              onClick={selectHighConfidenceQueueSuggestions}
            >
              Select high confidence
            </Button>
            <Button
              kind="tertiary"
              size="sm"
              disabled={selectedQueueSuggestions.length === 0}
              onClick={clearQueueSuggestionSelection}
            >
              Clear selection
            </Button>
            <Button
              kind="secondary"
              size="sm"
              disabled={selectedQueueSuggestions.length === 0}
              onClick={applySelectedQueueSuggestions}
            >
              Apply selected fixes
            </Button>
          </div>
        </div>
        {remediationQueue.length > 0 ? (
          <div className="remediation-queue">
            {remediationQueue.map((item, index) => {
              const suggestion = suggestionForQueueItem(item);
              const key = suggestion ? suggestionKey(suggestion) : '';
              const selected = selectedQueueSuggestionIds.includes(key);
              return (
                <Tile key={item.id} className="remediation-queue__item">
                  <div className="remediation-queue__rank">P{index + 1}</div>
                  <div className="remediation-queue__body">
                    <div className="package-tile__header">
                      <div>
                        <h3>{item.title}</h3>
                        <p>{item.subject}</p>
                      </div>
                      <div className="network-actions">
                        <Tag type={item.tagType}>{item.severity}</Tag>
                        <Tag type="gray">{item.tag}</Tag>
                      </div>
                    </div>
                    <p>{item.detail}</p>
                    {suggestion ? (
                      <div className="remediation-queue__suggestion">
                        <Checkbox
                          id={`queue-suggestion-${key}`}
                          labelText={`Select suggested ${suggestionLabels[suggestion.kind]} for ${suggestion.row.name}`}
                          checked={selected}
                          onChange={(_, data) => toggleQueueSuggestion(suggestion, Boolean(data.checked))}
                        />
                        <div>
                          <p>
                            Suggested {suggestionLabels[suggestion.kind]}: {suggestion.label}
                          </p>
                          <div className="network-actions">
                            <Tag type={confidenceTagType(suggestion.confidence)}>
                              {suggestion.confidence} confidence
                            </Tag>
                            {suggestion.evidence.slice(0, 2).map((evidence) => (
                              <Tag key={evidence} type="gray">{evidence}</Tag>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p>No automatic suggestion is available for this issue.</p>
                    )}
                  </div>
                  <div className="remediation-queue__action">
                    {suggestion && (
                      <Button
                        kind="tertiary"
                        size="sm"
                        onClick={() => applyAssignmentSuggestion(suggestion)}
                      >
                        Apply fix
                      </Button>
                    )}
                    <Button
                      kind="tertiary"
                      size="sm"
                      onClick={() => reviewRemediationIssue(item)}
                    >
                      Review issue
                    </Button>
                  </div>
                </Tile>
              );
            })}
          </div>
        ) : (
          <Tile className="resource-tile">
            <h3>Ready</h3>
            <p>All tracked export readiness items are clear.</p>
          </Tile>
        )}
      </div>
      {assignmentSuggestions.length > 0 && (
        <div className="export-package">
          <div className="section-header compact">
            <div>
              <h2>Suggested assignment fixes</h2>
              <p>Review likely fixes inferred from matching VM names, applications, networks, and existing assignments.</p>
            </div>
            <div className="network-actions">
              {suggestionAudit.length > 0 && <Tag type="gray">{suggestionAudit.length} audited</Tag>}
              <Tag type="blue">{assignmentSuggestions.length} suggestion(s)</Tag>
              <Tag type="green">{highConfidenceSuggestions.length} high confidence</Tag>
              <Button
                kind="tertiary"
                size="sm"
                disabled={highConfidenceSuggestions.length === 0}
                onClick={applyHighConfidenceSuggestions}
              >
                Apply high-confidence suggestions
              </Button>
            </div>
          </div>
          <div className="resource-list">
            {assignmentSuggestions.map((suggestion) => (
              <Tile
                key={`${suggestion.row.id}-${suggestion.kind}-${suggestion.value}`}
                className="resource-tile"
              >
                <div className="package-tile__header">
                  <h3>{suggestion.row.name}</h3>
                  <div className="network-actions">
                    <Tag type="blue">{suggestionLabels[suggestion.kind]}</Tag>
                    <Tag type={confidenceTagType(suggestion.confidence)}>
                      {suggestion.confidence} confidence
                    </Tag>
                  </div>
                </div>
                <p>{suggestion.label}</p>
                <p>{suggestion.reason}</p>
                {suggestion.evidence.length > 0 && (
                  <p>{suggestion.evidence.join(' | ')}</p>
                )}
                <div className="network-actions">
                  <Button
                    kind="tertiary"
                    size="sm"
                    onClick={() => applyAssignmentSuggestion(suggestion)}
                  >
                    Apply suggestion
                  </Button>
                </div>
              </Tile>
            ))}
          </div>
        </div>
      )}
      {recentSuggestionAudit.length > 0 && (
        <div className="export-package">
          <div className="section-header compact">
            <div>
              <h2>Suggestion audit</h2>
              <p>Review applied recommendation changes and revert any active suggestion before export.</p>
            </div>
            <div className="network-actions">
              <Tag type="blue">{suggestionAudit.length} total</Tag>
              <Tag type={activeAuditCount === 0 ? 'gray' : 'green'}>{activeAuditCount} active</Tag>
            </div>
          </div>
          <div className="resource-list">
            {recentSuggestionAudit.map((entry) => (
              <Tile key={entry.id} className="resource-tile">
                <div className="package-tile__header">
                  <h3>{entry.vmName}</h3>
                  <div className="network-actions">
                    <Tag type="blue">{suggestionLabels[entry.field]}</Tag>
                    <Tag type={confidenceTagType(entry.confidence)}>
                      {entry.confidence} confidence
                    </Tag>
                    {entry.revertedAt && <Tag type="gray">Reverted</Tag>}
                  </div>
                </div>
                <p>{entry.oldValue || '(blank)'} to {entry.newValue || '(blank)'}</p>
                <p>{entry.reason}</p>
                {entry.evidence.length > 0 && <p>{entry.evidence.slice(0, 2).join(' | ')}</p>}
                <p>Applied {entry.appliedAt}</p>
                <div className="network-actions">
                  <Button
                    kind="tertiary"
                    size="sm"
                    disabled={Boolean(entry.revertedAt)}
                    onClick={() => revertSuggestionAuditEntry(entry.id)}
                  >
                    Undo suggestion
                  </Button>
                </div>
              </Tile>
            ))}
          </div>
        </div>
      )}
      {preflightSummary && (
        <div className="export-package">
          <div className="section-header compact">
            <div>
              <h2>Package preflight</h2>
              <p>{preflightSummary.total} backend finding(s) from the saved Carbon network plan.</p>
            </div>
            <div className="network-actions">
              <Tag type={preflightSummary.blockers === 0 ? 'green' : 'red'}>
                {preflightSummary.blockers} blocker(s)
              </Tag>
              <Tag type={preflightSummary.warnings === 0 ? 'green' : 'warm-gray'}>
                {preflightSummary.warnings} warning(s)
              </Tag>
              <Tag type="gray">{preflightSummary.info} info</Tag>
            </div>
          </div>
          {visiblePreflightFindings.length > 0 ? (
            <div className="resource-list">
              {visiblePreflightFindings.map((finding, index) => (
                <Tile key={`${finding.Subject}-${finding.Category}-${index}`} className="resource-tile">
                  {(() => {
                    const suggestion = suggestionForFinding(finding);
                    return (
                      <>
                        <div className="package-tile__header">
                          <h3>{finding.Subject || 'Package'}</h3>
                          <Tag type={finding.Severity === 'blocker' ? 'red' : finding.Severity === 'warning' ? 'warm-gray' : 'gray'}>
                            {finding.Severity}
                          </Tag>
                        </div>
                        <p>{finding.Message}</p>
                        {finding['Fix Category'] && <p>{finding['Fix Category']}</p>}
                        {suggestion && (
                          <>
                            <p>
                              Suggested {suggestionLabels[suggestion.kind]}: {suggestion.label}. {suggestion.reason}
                            </p>
                            <div className="network-actions">
                              <Tag type={confidenceTagType(suggestion.confidence)}>
                                {suggestion.confidence} confidence
                              </Tag>
                              {suggestion.evidence.slice(0, 2).map((item) => (
                                <Tag key={item} type="gray">{item}</Tag>
                              ))}
                            </div>
                          </>
                        )}
                        <div className="network-actions">
                          {suggestion && (
                            <Button
                              kind="tertiary"
                              size="sm"
                              onClick={() => applyAssignmentSuggestion(suggestion)}
                            >
                              Apply suggested {suggestionLabels[suggestion.kind]}
                            </Button>
                          )}
                          {routesForFinding(finding).map((route) => (
                            <Button
                              key={route.label}
                              kind="tertiary"
                              size="sm"
                              onClick={() => openPreflightFinding(finding, route)}
                            >
                              {route.label}
                            </Button>
                          ))}
                        </div>
                      </>
                    );
                  })()}
                </Tile>
              ))}
            </div>
          ) : (
            <Tile className="resource-tile">
              <h3>Ready</h3>
              <p>No package preflight findings returned.</p>
            </Tile>
          )}
        </div>
      )}
      {terraformPreview && selectedPreviewFile && (
        <div className="export-package">
          <div className="section-header compact">
            <div>
              <h2>Package preview</h2>
              <p>{terraformPreview.files.length} generated file(s) from the saved Carbon network plan.</p>
            </div>
            <div className="network-actions">
              <Tag type="blue">{selectedPreviewFile.category}</Tag>
              <Tag type="gray">{selectedPreviewSize}</Tag>
              <Button
                kind="tertiary"
                size="sm"
                renderIcon={Download}
                onClick={showHandoffCsvs}
              >
                Show handoff CSVs
              </Button>
              <Button
                kind="secondary"
                size="sm"
                renderIcon={Download}
                onClick={() => downloadPreviewFile(selectedPreviewFile)}
              >
                Download selected
              </Button>
              <Button
                kind="tertiary"
                size="sm"
                renderIcon={Close}
                onClick={() => {
                  setTerraformPreview(null);
                  setSelectedPreviewPath('');
                  setPreviewSearch('');
                  setPreviewCategory('All');
                }}
              >
                Close preview
              </Button>
            </div>
          </div>
          <div className="preview-browser">
            <div className="preview-browser__sidebar">
              <Search
                id="terraform-preview-search"
                labelText="Search package files"
                placeholder="Search file path"
                value={previewSearch}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  setPreviewSearch(event.target.value)
                }
              />
              <Select
                id="terraform-preview-category"
                labelText="Package section"
                value={previewCategory}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                  setPreviewCategory(event.target.value)
                }
              >
                {previewCategories.map((category) => (
                  <SelectItem key={category} value={category} text={category} />
                ))}
              </Select>
              <div className="preview-file-list" aria-label="Package preview files">
                {filteredPreviewFiles.map((file) => (
                  <button
                    key={file.path}
                    className={`preview-file-row${file.path === selectedPreviewFile.path ? ' preview-file-row--selected' : ''}`}
                    type="button"
                    onClick={() => setSelectedPreviewPath(file.path)}
                  >
                    <span>{file.path}</span>
                    <small>{file.category}</small>
                  </button>
                ))}
                {filteredPreviewFiles.length === 0 && (
                  <p className="preview-empty">No package files match this filter.</p>
                )}
              </div>
            </div>
            <div className="preview-browser__content">
              <div className="preview-file-header">
                <div>
                  <strong>{selectedPreviewFile.path}</strong>
                  <span>{selectedPreviewSize}</span>
                </div>
                <Tag type="blue">{handoffCsvCount} handoff CSVs</Tag>
              </div>
              <pre className="terraform-preview" aria-label={`Terraform preview ${selectedPreviewFile.path}`}>
                <code>{selectedPreviewFile.content}</code>
              </pre>
            </div>
          </div>
        </div>
      )}
      <div className="export-package">
        <div className="section-header compact">
          <div>
            <h2>Package parity status</h2>
            <p>{packageFileCount} files are included in the generated ZIP.</p>
          </div>
          <Tag type="green">Streamlit handoff set covered</Tag>
        </div>
        <div className="package-parity-grid">
          {packageParitySummary.map((item) => (
            <Tile key={item.label} className="package-parity-tile">
              <div>
                <h3>{item.label}</h3>
                <p>{item.detail}</p>
              </div>
              <div className="package-parity-tile__status">
                <strong>{item.value}</strong>
                <Tag type={item.tagType}>{item.tag}</Tag>
              </div>
            </Tile>
          ))}
        </div>
        <div className="package-grid">
          {packageGroups.map((group) => (
            <Tile key={group.title} className="package-tile">
              <div className="package-tile__header">
                <h3>{group.title}</h3>
                <Tag type={group.tagType}>{group.status}</Tag>
              </div>
              <p>{group.files.length} file(s)</p>
              <ul>
                {group.files.map((file) => (
                  <li key={file}>{file}</li>
                ))}
              </ul>
            </Tile>
          ))}
        </div>
      </div>
    </Layer>
  );
}

// Made with Bob
