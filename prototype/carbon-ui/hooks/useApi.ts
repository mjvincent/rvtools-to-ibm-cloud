import type {
  AssignmentVm,
  NetworkPlanningState,
  ResourceState,
  SavedProject,
  SavedProjectState,
  WorkbookSummary,
} from '../types/network-planning';
import type { ApiVmAssignmentPayload } from '../utils/planning-state';

type ApiErrorPayload = {
  detail?: unknown;
};

const API_RECOVERY_HINT =
  'Confirm the FastAPI service is running, check Docker Compose or dev-server logs, then retry. Current browser-side planning state is kept unless you refresh or close the page.';

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function formatApiErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') {
    return detail.trim() || fallback;
  }
  if (typeof detail === 'number' || typeof detail === 'boolean') {
    return String(detail);
  }
  if (Array.isArray(detail)) {
    const formattedItems = detail
      .map((item) => formatApiErrorDetail(item, ''))
      .filter(Boolean);
    return formattedItems.length > 0 ? formattedItems.join('; ') : fallback;
  }
  if (detail && typeof detail === 'object') {
    const record = detail as Record<string, unknown>;
    if (typeof record.msg === 'string') {
      const loc = Array.isArray(record.loc) ? record.loc.join('.') : '';
      return loc ? `${loc}: ${record.msg}` : record.msg;
    }
    for (const key of ['message', 'error', 'detail']) {
      if (key in record) {
        const formatted = formatApiErrorDetail(record[key], '');
        if (formatted) return formatted;
      }
    }
    const entries = Object.entries(record)
      .map(([key, value]) => {
        const formatted = formatApiErrorDetail(value, '');
        return formatted ? `${humanizeKey(key)}: ${formatted}` : '';
      })
      .filter(Boolean);
    return entries.length > 0 ? entries.join('; ') : fallback;
  }
  return fallback;
}

function responseStatusLabel(response: Response): string {
  const statusText = response.statusText ? ` ${response.statusText}` : '';
  return `HTTP ${response.status}${statusText}`;
}

export function buildApiRecoveryMessage(fallback: string, statusLabel?: string): string {
  const statusPrefix = statusLabel ? `${statusLabel}. ` : '';
  return `${fallback} ${statusPrefix}${API_RECOVERY_HINT}`;
}

async function apiFetch(
  input: RequestInfo | URL,
  init: RequestInit | undefined,
  fallback: string,
): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch {
    throw new Error(buildApiRecoveryMessage(fallback));
  }
}

async function readJsonPayload(response: Response): Promise<unknown | null> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function formatApiResponseError(
  response: Response,
  payload: unknown | null,
  fallback: string,
): string {
  if (payload) {
    const apiPayload = payload as ApiErrorPayload;
    const formatted = formatApiErrorDetail(apiPayload.detail ?? apiPayload, '');
    if (formatted) return formatted;
  }
  return buildApiRecoveryMessage(fallback, responseStatusLabel(response));
}

async function readApiError(response: Response, fallback: string): Promise<string> {
  const payload = await readJsonPayload(response);
  return formatApiResponseError(response, payload, fallback);
}

async function readJsonResponse<T>(response: Response, fallback: string): Promise<T> {
  const payload = await readJsonPayload(response);
  if (!response.ok) {
    throw new Error(formatApiResponseError(response, payload, fallback));
  }
  if (payload === null) {
    throw new Error(buildApiRecoveryMessage(fallback, responseStatusLabel(response)));
  }
  return payload as T;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export type HealthResponse = {
  status: string;
  persistence_enabled: boolean;
};

export async function checkApiHealth(): Promise<HealthResponse> {
  const response = await apiFetch('/health', undefined, 'API health check failed.');
  return readJsonResponse<HealthResponse>(response, 'API health check failed.');
}

// ─── Workbooks ────────────────────────────────────────────────────────────────

export async function uploadWorkbook(file: File): Promise<WorkbookSummary> {
  const formData = new FormData();
  formData.append('workbook', file);
  const response = await apiFetch('/api/workbooks/summary', {
    method: 'POST',
    body: formData,
  }, 'Workbook upload failed.');
  return readJsonResponse<WorkbookSummary>(response, 'Workbook upload failed.');
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export async function listProjects(): Promise<SavedProject[]> {
  const response = await apiFetch('/api/projects', undefined, 'Could not load saved projects.');
  const payload = await readJsonResponse<{ projects?: SavedProject[] }>(
    response,
    'Could not load saved projects.',
  );
  return payload.projects || [];
}

export async function createProject(name: string, description: string): Promise<SavedProject> {
  const response = await apiFetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim(), description: description.trim() }),
  }, 'Could not create project.');
  const payload = await readJsonResponse<{ project: SavedProject }>(response, 'Could not create project.');
  return payload.project;
}

export async function updateProject(projectId: string, name: string, description: string): Promise<void> {
  const response = await apiFetch(`/api/projects/${projectId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim(), description: description.trim() }),
  }, 'Could not update project.');
  await readJsonResponse<unknown>(response, 'Could not update project.');
}

export async function deleteProject(projectId: string): Promise<void> {
  const response = await apiFetch(
    `/api/projects/${projectId}`,
    { method: 'DELETE' },
    'Could not delete project.',
  );
  if (!response.ok) {
    throw new Error(await readApiError(response, 'Could not delete project.'));
  }
}

export async function loadProject(
  projectId: string,
): Promise<{ project: SavedProject; state: SavedProjectState | null }> {
  const response = await apiFetch(`/api/projects/${projectId}`, undefined, 'Could not load project.');
  const payload = await readJsonResponse<{ project: SavedProject; state?: SavedProjectState | null }>(
    response,
    'Could not load project.',
  );
  return { project: payload.project, state: payload.state ?? null };
}

// ─── Project state ────────────────────────────────────────────────────────────

export async function saveProjectState(
  projectId: string,
  planningState: Record<string, unknown>,
  projectName: string,
): Promise<void> {
  const response = await apiFetch(`/api/projects/${projectId}/state`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      planning_state: planningState,
      project_name: projectName,
    }),
  }, 'Could not save project state.');
  await readJsonResponse<unknown>(response, 'Could not save project state.');
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
  const response = await apiFetch(`/api/projects/${projectId}/network-plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan),
  }, 'Failed to save network plan.');
  if (!response.ok) {
    throw new Error(await readApiError(response, 'Failed to save network plan.'));
  }
}

export async function loadNetworkPlan(projectId: string): Promise<NetworkPlanningState | Record<string, unknown>> {
  const response = await apiFetch(`/api/projects/${projectId}/network-plan`, undefined, 'Could not load network plan.');
  return readJsonResponse<NetworkPlanningState | Record<string, unknown>>(
    response,
    'Could not load network plan.',
  );
}

// ─── VM assignments ───────────────────────────────────────────────────────────

export async function updateVmAssignments(
  projectId: string,
  assignments: ApiVmAssignmentPayload[],
): Promise<void> {
  const response = await apiFetch(`/api/projects/${projectId}/vm-assignments`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(assignments),
  }, 'Could not update VM assignments.');
  if (!response.ok) {
    throw new Error(await readApiError(response, 'Could not update VM assignments.'));
  }
}

// ─── Terraform ────────────────────────────────────────────────────────────────

export async function generateTerraform(projectId: string): Promise<Blob> {
  const response = await apiFetch(`/api/projects/${projectId}/terraform`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }, 'Terraform generation failed.');
  if (!response.ok) {
    throw new Error(await readApiError(response, 'Terraform generation failed.'));
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
  const response = await apiFetch(`/api/projects/${projectId}/terraform/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }, 'Terraform preview failed.');
  return readJsonResponse<TerraformPreviewResponse>(response, 'Terraform preview failed.');
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
  const response = await apiFetch(`/api/projects/${projectId}/preflight`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  }, 'Preflight check failed.');
  return readJsonResponse<PreflightResponse>(response, 'Preflight check failed.');
}

// Made with Bob
