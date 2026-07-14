import type {
  AssignmentVm,
  ImageImportStatus,
  ImageImportStatusValue,
  RemediationTracker,
  SavedProjectState,
  SuggestionAuditEntry,
  WorkbookSummary,
} from '../types/network-planning';

const VALID_REMEDIATION_STATUSES = ['Open', 'In Progress', 'Resolved', 'Deferred'] as const;
const VALID_IMAGE_IMPORT_STATUSES = ['', 'Pending', 'Scheduled', 'Imported', 'Failed', 'Review'] as const;
const VALID_SUGGESTION_FIELDS = ['subnet', 'securityGroup', 'storage', 'wave'] as const;
const VALID_SUGGESTION_CONFIDENCES = ['High', 'Medium', 'Low'] as const;

function normalizeBoolean(value: unknown, fallback = false): boolean {
  if (value === undefined || value === null || value === '') return fallback;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') {
    return ['true', 'yes', '1'].includes(value.toLowerCase());
  }
  return Boolean(value);
}

function asString(value: unknown): string {
  if (value === undefined || value === null) return '';
  if (typeof value === 'string') return value;
  return String(value);
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null ? value as Record<string, unknown> : {};
}

function isValidRemediationStatus(value: unknown): value is RemediationTracker[number]['status'] {
  return typeof value === 'string' && VALID_REMEDIATION_STATUSES.includes(value as any);
}

function isValidImageImportStatus(value: unknown): value is ImageImportStatusValue {
  return typeof value === 'string' && VALID_IMAGE_IMPORT_STATUSES.includes(value as any);
}

function isValidSuggestionField(value: unknown): value is SuggestionAuditEntry['field'] {
  return typeof value === 'string' && VALID_SUGGESTION_FIELDS.includes(value as any);
}

function isValidSuggestionConfidence(value: unknown): value is SuggestionAuditEntry['confidence'] {
  return typeof value === 'string' && VALID_SUGGESTION_CONFIDENCES.includes(value as any);
}

export function vmDecision(row: AssignmentVm) {
  return {
    'VM Key': row.id,
    'VM Name': row.name,
    'Exclude?': Boolean(row.excluded),
    'Exclusion Reason': row.exclusionReason,
    'Override Profile': row.overrideProfile,
    'Override Profile Reason': row.overrideProfileReason,
    'Override Storage Tier': row.overrideStorageTier,
    'Override Storage Tier Reason': row.overrideStorageTierReason,
    Network: row.network,
    Subnet: row.subnet,
    'Security Group': row.securityGroup,
  };
}

export function waveDecision(row: AssignmentVm) {
  return {
    'VM Key': row.id,
    'VM Name': row.name,
    Wave: row.wave,
    'Cutover Group': row.cutoverGroup,
    Owner: row.owner,
    Application: row.application,
    Priority: row.priority,
    'Dependency Group': row.dependencyGroup,
  };
}

export function normalizeRemediationTracker(rawTracker: unknown): RemediationTracker {
  const tracker = asRecord(rawTracker);
  return Object.fromEntries(
    Object.entries(tracker).map(([blockerId, entry]) => {
      const record = asRecord(entry);
      const status = isValidRemediationStatus(record.status) ? record.status : 'Open';
      const owner = asString(record.owner);
      const dueDate = asString(record.dueDate ?? record.due_date);
      const notes = asString(record.notes);
      const vmKey = asString(record.vm_key ?? record.vmKey ?? blockerId.split('::', 1)[0].split(':', 1)[0]);
      const blockerType = asString(record.blocker_type ?? record.blockerType ?? record.type ?? '');
      const blockerDescription = asString(record.blocker_description ?? record.blockerDescription ?? record.description ?? '');

      return [blockerId, {
        status,
        owner,
        dueDate,
        notes,
        vmKey,
        vm_key: vmKey,
        blockerType,
        blocker_type: blockerType,
        blockerDescription,
        blocker_description: blockerDescription,
      }];
    }),
  ) as RemediationTracker;
}

export function normalizeImageImportStatus(rawStatus: unknown): ImageImportStatus {
  const statusRecord = asRecord(rawStatus);
  return Object.fromEntries(
    Object.entries(statusRecord).map(([sourceImage, entry]) => {
      const record = asRecord(entry);
      const importStatus = asString(record.importStatus ?? record.import_status);
      return [sourceImage, {
        targetCatalogId: asString(record.targetCatalogId ?? record.target_catalog_id),
        importStatus: isValidImageImportStatus(importStatus) ? importStatus : '',
        estimatedImportTime: asString(record.estimatedImportTime ?? record.estimated_import_time),
        notes: asString(record.notes),
      }];
    }),
  ) as ImageImportStatus;
}

export function normalizeSuggestionAudit(rawAudit: unknown): SuggestionAuditEntry[] {
  if (!Array.isArray(rawAudit)) return [];
  return rawAudit
    .filter((entry) => typeof entry === 'object' && entry !== null)
    .map((entry) => {
      const record = entry as Record<string, unknown>;
      const fieldValue = record.field;
      const id = asString(record.id || `${asString(record.vmId ?? record.vm_id ?? 'vm')}-${asString(fieldValue ?? 'field')}-${Date.now()}`);
      const vmId = asString(record.vmId ?? record.vm_id);
      const vmName = asString(record.vmName ?? record.vm_name);
      const field = isValidSuggestionField(fieldValue) ? fieldValue as SuggestionAuditEntry['field'] : 'subnet';
      const oldValue = asString(record.oldValue ?? record.old_value);
      const newValue = asString(record.newValue ?? record.new_value);
      const confidence = isValidSuggestionConfidence(record.confidence ?? record.confidence) ? record.confidence as SuggestionAuditEntry['confidence'] : 'Low';
      const reason = asString(record.reason);
      const evidence = Array.isArray(record.evidence) ? record.evidence.map((item) => asString(item)) : [];
      const appliedAt = asString(record.appliedAt ?? record.applied_at);
      const revertedAt = asString(record.revertedAt ?? record.reverted_at);

      return {
        id,
        vmId,
        vmName,
        field,
        oldValue,
        newValue,
        confidence,
        reason,
        evidence,
        appliedAt,
        revertedAt: revertedAt || undefined,
      };
    });
}

export function suggestionAuditToPlanningState(audit: SuggestionAuditEntry[]) {
  return audit.map((entry) => ({
    id: entry.id,
    vm_id: entry.vmId,
    vm_name: entry.vmName,
    field: entry.field,
    old_value: entry.oldValue,
    new_value: entry.newValue,
    confidence: entry.confidence,
    reason: entry.reason,
    evidence: entry.evidence,
    applied_at: entry.appliedAt,
    reverted_at: entry.revertedAt ?? null,
  }));
}

export function remediationTrackerToPlanningState(tracker: RemediationTracker) {
  return Object.fromEntries(
    Object.entries(tracker).map(([blockerId, entry]) => [blockerId, {
      status: entry.status,
      due_date: entry.dueDate,
      notes: entry.notes,
      owner: entry.owner,
      vm_key: entry.vm_key || entry.vmKey || blockerId.split('::', 1)[0].split(':', 1)[0],
      blocker_type: entry.blocker_type || entry.blockerType || entry.type || '',
      blocker_description: entry.blocker_description || entry.blockerDescription || entry.description || '',
    }]),
  );
}

export function imageImportStatusToPlanningState(status: ImageImportStatus) {
  return Object.fromEntries(
    Object.entries(status).map(([sourceImage, entry]) => [sourceImage, {
      target_catalog_id: entry.targetCatalogId,
      import_status: entry.importStatus,
      estimated_import_time: entry.estimatedImportTime,
      notes: entry.notes,
    }]),
  );
}

export function buildProjectStatePayload(params: {
  assignmentRows: AssignmentVm[];
  summary: WorkbookSummary | null;
  resources: unknown;
  remediationTracker: RemediationTracker;
  imageImportStatus: ImageImportStatus;
  suggestionAudit: SuggestionAuditEntry[];
  projectName: string;
}) {
  return {
    schema_version: 'carbon-prototype-0.3',
    metadata: { project_name: params.projectName.trim(), source: 'carbon-ui-prototype' },
    vm_decisions: params.assignmentRows.map(vmDecision),
    wave_planning: params.assignmentRows.map(waveDecision),
    remediation_tracker: remediationTrackerToPlanningState(params.remediationTracker),
    image_import_status: imageImportStatusToPlanningState(params.imageImportStatus),
    suggestion_audit: suggestionAuditToPlanningState(params.suggestionAudit || []),
    carbon_summary: params.summary,
    carbon_assignment_rows: params.assignmentRows,
    carbon_resources: params.resources,
    carbon_remediation_tracker: params.remediationTracker,
    carbon_image_import_status: params.imageImportStatus,
    carbon_suggestion_audit: params.suggestionAudit || [],
  };
}

export function normalizeProjectState(savedState: SavedProjectState) {
  return {
    summary: savedState.planning_state_json?.carbon_summary ?? null,
    assignmentRows: savedState.planning_state_json?.carbon_assignment_rows ?? [],
    resources: savedState.planning_state_json?.carbon_resources,
    remediationTracker: normalizeRemediationTracker(savedState.planning_state_json?.carbon_remediation_tracker ?? savedState.planning_state_json?.remediation_tracker ?? {}),
    imageImportStatus: normalizeImageImportStatus(savedState.planning_state_json?.carbon_image_import_status ?? savedState.planning_state_json?.image_import_status ?? {}),
    suggestionAudit: normalizeSuggestionAudit(savedState.planning_state_json?.carbon_suggestion_audit ?? savedState.planning_state_json?.suggestion_audit ?? []),
  };
}
