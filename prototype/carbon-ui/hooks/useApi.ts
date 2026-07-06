import type {
  AssignmentVm,
  NetworkPlanningState,
  ResourceState,
  SavedProject,
  SavedProjectState,
  WorkbookSummary,
} from '../types/network-planning';
import type { ApiVmAssignmentPayload } from '../utils/planning-state';

// ─── Health ───────────────────────────────────────────────────────────────────

export type HealthResponse = {
  status: string;
  persistence_enabled: boolean;
};

export async function checkApiHealth(): Promise<HealthResponse> {
  const response = await fetch('/health');
  if (!response.ok) {
    throw new Error('API health check failed.');
  }
  return response.json();
}

// ─── Workbooks ────────────────────────────────────────────────────────────────

export async function uploadWorkbook(file: File): Promise<WorkbookSummary> {
  const formData = new FormData();
  formData.append('workbook', file);
  const response = await fetch('/api/workbooks/summary', {
    method: 'POST',
    body: formData,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Workbook upload failed.');
  }
  return payload;
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export async function listProjects(): Promise<SavedProject[]> {
  const response = await fetch('/api/projects');
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Could not load saved projects.');
  }
  return payload.projects || [];
}

export async function createProject(name: string, description: string): Promise<SavedProject> {
  const response = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim(), description: description.trim() }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Could not create project.');
  }
  return payload.project;
}

export async function updateProject(projectId: string, name: string, description: string): Promise<void> {
  const response = await fetch(`/api/projects/${projectId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim(), description: description.trim() }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Could not update project.');
  }
}

export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || 'Could not delete project.');
  }
}

export async function loadProject(
  projectId: string,
): Promise<{ project: SavedProject; state: SavedProjectState | null }> {
  const response = await fetch(`/api/projects/${projectId}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Could not load project.');
  }
  return { project: payload.project, state: payload.state ?? null };
}

// ─── Project state ────────────────────────────────────────────────────────────

export async function saveProjectState(
  projectId: string,
  planningState: Record<string, unknown>,
  projectName: string,
): Promise<void> {
  const response = await fetch(`/api/projects/${projectId}/state`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      planning_state: planningState,
      project_name: projectName,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Could not save project state.');
  }
}

// ─── Network plan ─────────────────────────────────────────────────────────────

export type NetworkPlanBody = {
  version: string;
  vpcs: unknown[];
  subnets: unknown[];
  security_groups: unknown[];
  storage_profiles: unknown[];
  waves: unknown[];
  network_components: unknown[];
  vm_assignments: unknown[];
  metadata: Record<string, unknown>;
};

export async function saveNetworkPlan(projectId: string, plan: NetworkPlanBody): Promise<void> {
  const response = await fetch(`/api/projects/${projectId}/network-plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan),
  });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || 'Failed to save network plan.');
  }
}

export async function loadNetworkPlan(projectId: string): Promise<NetworkPlanningState | Record<string, unknown>> {
  const response = await fetch(`/api/projects/${projectId}/network-plan`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Could not load network plan.');
  }
  return payload;
}

// ─── VM assignments ───────────────────────────────────────────────────────────

export async function updateVmAssignments(
  projectId: string,
  assignments: ApiVmAssignmentPayload[],
): Promise<void> {
  const response = await fetch(`/api/projects/${projectId}/vm-assignments`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(assignments),
  });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || 'Could not update VM assignments.');
  }
}

// ─── Terraform ────────────────────────────────────────────────────────────────

export async function generateTerraform(projectId: string): Promise<Blob> {
  const response = await fetch(`/api/projects/${projectId}/terraform`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || 'Terraform generation failed.');
  }
  return response.blob();
}

export type TerraformPreviewFile = {
  path: string;
  category: string;
  size_bytes: number;
  content: string;
};

export type TerraformPreviewResponse = {
  project_id: string;
  project_name: string;
  files: TerraformPreviewFile[];
};

export async function previewTerraform(projectId: string): Promise<TerraformPreviewResponse> {
  const response = await fetch(`/api/projects/${projectId}/terraform/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Terraform preview failed.');
  }
  return payload;
}

export type PreflightFinding = {
  Severity: string;
  Category: string;
  'Fix Category': string;
  Subject: string;
  Message: string;
  Remediation: string;
  'Fix Location': string;
  'Suggested Action': string;
  'Valid Options': string;
  'Recommended Option': string;
  'Quick Fix Type': string;
  Field: string;
  'Current Value': string;
  Constraint: string;
};

export type PreflightResponse = {
  project_id: string;
  project_name: string;
  summary: {
    blockers: number;
    warnings: number;
    info: number;
    total: number;
  };
  findings: PreflightFinding[];
};

export async function runProjectPreflight(projectId: string): Promise<PreflightResponse> {
  const response = await fetch(`/api/projects/${projectId}/preflight`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Preflight check failed.');
  }
  return payload;
}

// Made with Bob
