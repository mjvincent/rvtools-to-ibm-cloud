// @ts-nocheck
'use client';

import React, { useEffect, useRef } from 'react';
import {
  Button,
  Column,
  Content,
  Grid,
  Header,
  HeaderGlobalAction,
  HeaderGlobalBar,
  HeaderName,
  HeaderPanel,
  InlineNotification,
  Modal,
  Select,
  SelectItem,
  SideNav,
  SideNavItems,
  SideNavLink,
  Tag,
  TextArea,
  TextInput,
  Tile,
} from '@carbon/react';
import {
  CloudUpload,
  DataTable as DataTableIcon,
  DeploymentPattern,
  Information,
  Renew,
  Save,
} from '@carbon/icons-react';
import { AppProvider, useAppState } from '../store/AppContext';
import * as api from '../hooks/useApi';
import { rowsFromSummary } from '../components/workflows/IntakeWorkflow';
import {
  buildNetworkPlanBody,
  resourcesFromNetworkPlan,
  rowsFromNetworkPlan,
  vmAssignmentsFromRows,
} from '../utils/planning-state';
import type { ImageImportStatus, RemediationTracker, SuggestionAuditEntry, Workflow } from '../types/network-planning';

import OverviewWorkflow from '../components/workflows/OverviewWorkflow';
import IntakeWorkflow from '../components/workflows/IntakeWorkflow';
import AssignmentWorkflow from '../components/workflows/AssignmentWorkflow';
import OverridesWorkflow from '../components/workflows/OverridesWorkflow';
import NetworkPlanWorkflow from '../components/workflows/NetworkPlanWorkflow';
import SecurityWorkflow from '../components/workflows/SecurityWorkflow';
import StorageWorkflow from '../components/workflows/StorageWorkflow';
import WavesWorkflow from '../components/workflows/WavesWorkflow';
import RemediationWorkflow from '../components/workflows/RemediationWorkflow';
import ImageImportWorkflow from '../components/workflows/ImageImportWorkflow';
import MigrationOpsWorkflow from '../components/workflows/MigrationOpsWorkflow';
import ExportWorkflow from '../components/workflows/ExportWorkflow';

const workflows: Array<{ id: Workflow; label: string; icon?: React.ComponentType }> = [
  { id: 'overview', label: 'Overview', icon: DataTableIcon },
  { id: 'intake', label: 'Workbook Intake', icon: CloudUpload },
  { id: 'assignment', label: 'VM Assignment', icon: DeploymentPattern },
  { id: 'overrides', label: 'VM Overrides', icon: DeploymentPattern },
  { id: 'remediation', label: 'Remediation Backlog', icon: DeploymentPattern },
  { id: 'imageImport', label: 'Image Import Planning', icon: DeploymentPattern },
  { id: 'migrationOps', label: 'Migration Ops', icon: DeploymentPattern },
  { id: 'network', label: 'Network Plan', icon: DeploymentPattern },
  { id: 'security', label: 'Security Plan', icon: DeploymentPattern },
  { id: 'storage', label: 'Storage / IOPS Plan', icon: DeploymentPattern },
  { id: 'waves', label: 'Wave Plan', icon: DeploymentPattern },
  { id: 'export', label: 'Export Readiness', icon: Save },
];

function vmDecision(row) {
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

function waveDecision(row) {
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

function remediationTrackerToPlanningState(tracker: RemediationTracker) {
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

function normalizeRemediationTracker(rawTracker): RemediationTracker {
  if (!rawTracker || typeof rawTracker !== 'object') return {};
  return Object.fromEntries(
    Object.entries(rawTracker).map(([blockerId, entry]: [string, any]) => [blockerId, {
      status: ['Open', 'In Progress', 'Resolved', 'Deferred'].includes(entry?.status) ? entry.status : 'Open',
      owner: entry?.owner || '',
      dueDate: entry?.dueDate || entry?.due_date || '',
      notes: entry?.notes || '',
      vmKey: entry?.vmKey || entry?.vm_key || String(blockerId).split('::', 1)[0].split(':', 1)[0],
      vm_key: entry?.vm_key || entry?.vmKey || String(blockerId).split('::', 1)[0].split(':', 1)[0],
      blockerType: entry?.blockerType || entry?.blocker_type || entry?.type || '',
      blocker_type: entry?.blocker_type || entry?.blockerType || entry?.type || '',
      blockerDescription: entry?.blockerDescription || entry?.blocker_description || entry?.description || '',
      blocker_description: entry?.blocker_description || entry?.blockerDescription || entry?.description || '',
    }]),
  );
}

function imageImportStatusToPlanningState(status: ImageImportStatus) {
  return Object.fromEntries(
    Object.entries(status).map(([sourceImage, entry]) => [sourceImage, {
      target_catalog_id: entry.targetCatalogId,
      import_status: entry.importStatus,
      estimated_import_time: entry.estimatedImportTime,
      notes: entry.notes,
    }]),
  );
}

function normalizeImageImportStatus(rawStatus): ImageImportStatus {
  if (!rawStatus || typeof rawStatus !== 'object') return {};
  const validStatuses = ['', 'Pending', 'Scheduled', 'Imported', 'Failed', 'Review'];
  return Object.fromEntries(
    Object.entries(rawStatus).map(([sourceImage, entry]: [string, any]) => [sourceImage, {
      targetCatalogId: entry?.targetCatalogId || entry?.target_catalog_id || '',
      importStatus: validStatuses.includes(entry?.importStatus || entry?.import_status)
        ? (entry?.importStatus || entry?.import_status)
        : '',
      estimatedImportTime: entry?.estimatedImportTime || entry?.estimated_import_time || '',
      notes: entry?.notes || '',
    }]),
  );
}

function normalizeSuggestionAudit(rawAudit): SuggestionAuditEntry[] {
  if (!Array.isArray(rawAudit)) return [];
  const validFields = ['subnet', 'securityGroup', 'storage', 'wave'];
  const validConfidence = ['High', 'Medium', 'Low'];
  return rawAudit
    .filter((entry) => entry && typeof entry === 'object')
    .map((entry: any) => ({
      id: String(entry.id || `${entry.vmId || entry.vm_id || entry.vmName || entry.vm_name || 'vm'}-${entry.field || 'field'}-${entry.appliedAt || entry.applied_at || Date.now()}`),
      vmId: String(entry.vmId || entry.vm_id || ''),
      vmName: String(entry.vmName || entry.vm_name || ''),
      field: validFields.includes(entry.field) ? entry.field : 'subnet',
      oldValue: String(entry.oldValue || entry.old_value || ''),
      newValue: String(entry.newValue || entry.new_value || ''),
      confidence: validConfidence.includes(entry.confidence) ? entry.confidence : 'Low',
      reason: String(entry.reason || ''),
      evidence: Array.isArray(entry.evidence) ? entry.evidence.map(String) : [],
      appliedAt: String(entry.appliedAt || entry.applied_at || ''),
    }));
}

function suggestionAuditToPlanningState(audit: SuggestionAuditEntry[]) {
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
  }));
}

function buildProjectStatePayload({ assignmentRows, summary, resources, remediationTracker, imageImportStatus, suggestionAudit, projectName }) {
  const planningStateTracker = remediationTrackerToPlanningState(remediationTracker);
  const planningImageStatus = imageImportStatusToPlanningState(imageImportStatus);
  const planningSuggestionAudit = suggestionAuditToPlanningState(suggestionAudit || []);
  return {
    schema_version: 'carbon-prototype-0.3',
    metadata: { project_name: projectName.trim(), source: 'carbon-ui-prototype' },
    vm_decisions: assignmentRows.map(vmDecision),
    wave_planning: assignmentRows.map(waveDecision),
    remediation_tracker: planningStateTracker,
    image_import_status: planningImageStatus,
    suggestion_audit: planningSuggestionAudit,
    carbon_summary: summary,
    carbon_assignment_rows: assignmentRows,
    carbon_resources: resources,
    carbon_remediation_tracker: remediationTracker,
    carbon_image_import_status: imageImportStatus,
    carbon_suggestion_audit: suggestionAudit || [],
  };
}

function WorkbenchShell() {
  const { state, dispatch } = useAppState();
  const {
    apiStatus, panelOpen, saveModalOpen, projects, selectedProjectId,
    projectName, projectDescription, projectStatus, projectError, uploadStatus,
    activeWorkflow, assignmentRows, resources, summary, persistenceEnabled,
    isDirty, autoSaveStatus, autoSaveError, remediationTracker, imageImportStatus,
    suggestionAudit,
  } = state;
  const hasLoadedProject = useRef(false);

  // Compute estate locally (not in state — it's derived)
  const computedEstate = React.useMemo(() => {
    if (summary?.estate_summary) return summary.estate_summary;
    return {
      in_scope: assignmentRows.length,
      excluded: 0, monthly: 0, savings: 0,
      blocked: assignmentRows.filter((row) => [row.image, row.migration, row.memory, row.networkReadiness].includes('Blocked')).length,
      review: assignmentRows.filter((row) => [row.image, row.migration, row.memory, row.networkReadiness].includes('Review')).length,
    };
  }, [summary, assignmentRows]);

  const planningCompleteness = React.useMemo(() => {
    const total = assignmentRows.length || 1;
    const missingSubnet = assignmentRows.filter((row) => !row.subnet).length;
    const missingSg = assignmentRows.filter((row) => !row.securityGroup).length;
    return { total, missingSubnet, missingSg };
  }, [assignmentRows]);

  const activeRemediationCount = React.useMemo(() => (
    assignmentRows.reduce((count, row) => {
      const readiness = [
        ['image', row.image],
        ['migration', row.migration],
        ['memory', row.memory],
        ['network', row.networkReadiness],
      ];
      return count + readiness.filter(([area, status]) => {
        const tracker = remediationTracker[`${row.id}::${area}`];
        return (status === 'Blocked' || status === 'Review') && tracker?.status !== 'Resolved' && tracker?.status !== 'Deferred';
      }).length;
    }, 0)
  ), [assignmentRows, remediationTracker]);

  const saveState = React.useMemo(() => {
    if (!persistenceEnabled) {
      return {
        tagType: 'gray',
        label: 'Autosave unavailable',
        detail: 'Persistence offline',
      };
    }
    if (autoSaveError) {
      return {
        tagType: 'red',
        label: 'Autosave failed',
        detail: autoSaveError,
      };
    }
    if (!selectedProjectId) {
      return {
        tagType: 'warm-gray',
        label: 'Manual save required',
        detail: 'Create or load a project',
      };
    }
    if (isDirty) {
      return {
        tagType: 'warm-gray',
        label: 'Autosave queued',
        detail: 'Changes pending',
      };
    }
    if (autoSaveStatus) {
      return {
        tagType: 'green',
        label: 'Saved',
        detail: 'Latest plan persisted',
      };
    }
    return {
      tagType: 'gray',
      label: 'No changes',
      detail: 'Ready for edits',
    };
  }, [autoSaveError, autoSaveStatus, isDirty, persistenceEnabled, selectedProjectId]);

  useEffect(() => {
    api.checkApiHealth()
      .then((payload) => {
        dispatch({ type: 'SET_PERSISTENCE_ENABLED', payload: payload.persistence_enabled });
        dispatch({ type: 'SET_API_STATUS', payload: payload.persistence_enabled ? 'API online with persistence' : 'API online' });
        if (payload.persistence_enabled) {
          api.listProjects().then((projects) => dispatch({ type: 'SET_PROJECTS', payload: projects })).catch(() => {});
        }
      })
      .catch(() => {
        dispatch({ type: 'SET_API_STATUS', payload: 'API unavailable' });
        dispatch({ type: 'SET_PERSISTENCE_ENABLED', payload: false });
      });
  }, []);

  // Autosave full network plan after resource or assignment edits.
  useEffect(() => {
    if (!selectedProjectId || !persistenceEnabled || !isDirty || !hasLoadedProject.current) return;
    const timer = window.setTimeout(async () => {
      dispatch({ type: 'SET_AUTO_SAVE_STATUS', payload: 'Saving planning changes...' });
      dispatch({ type: 'SET_AUTO_SAVE_ERROR', payload: '' });
      try {
        await api.saveProjectState(
          selectedProjectId,
          buildProjectStatePayload({ assignmentRows, summary, resources, remediationTracker, imageImportStatus, suggestionAudit, projectName }),
          projectName.trim(),
        );
        await api.saveNetworkPlan(
          selectedProjectId,
          buildNetworkPlanBody({ resources, assignmentRows, projectName, summary }),
        );
        dispatch({ type: 'SET_AUTO_SAVE_STATUS', payload: 'Planning changes saved.' });
        dispatch({ type: 'SET_IS_DIRTY', payload: false });
      } catch (error) {
        dispatch({
          type: 'SET_AUTO_SAVE_ERROR',
          payload: error instanceof Error ? error.message : 'Autosave failed.',
        });
      }
    }, 900);
    return () => window.clearTimeout(timer);
  }, [assignmentRows, resources, remediationTracker, imageImportStatus, suggestionAudit, selectedProjectId, persistenceEnabled, isDirty, projectName, summary]);

  // Push VM placement edits through the narrower assignment endpoint.
  useEffect(() => {
    if (!selectedProjectId || !persistenceEnabled || !hasLoadedProject.current) return;
    const timer = window.setTimeout(async () => {
      try {
        await api.updateVmAssignments(
          selectedProjectId,
          vmAssignmentsFromRows(assignmentRows, resources),
        );
      } catch {
        // Full-plan autosave creates the network plan when this endpoint is not ready yet.
      }
    }, 500);
    return () => window.clearTimeout(timer);
  }, [assignmentRows, resources, selectedProjectId, persistenceEnabled]);

  async function saveProject() {
    dispatch({ type: 'SET_PROJECT_STATUS', payload: '' });
    dispatch({ type: 'SET_PROJECT_ERROR', payload: '' });
    try {
      if (!projectName.trim()) throw new Error('Enter a project name before saving.');
      let projectId = selectedProjectId;
      if (!projectId) {
        const project = await api.createProject(projectName, projectDescription);
        projectId = project.id;
        dispatch({ type: 'SET_SELECTED_PROJECT_ID', payload: projectId });
      } else {
        await api.updateProject(projectId, projectName, projectDescription);
      }
      await api.saveProjectState(projectId, {
        ...buildProjectStatePayload({ assignmentRows, summary, resources, remediationTracker, imageImportStatus, suggestionAudit, projectName }),
      }, projectName.trim());
      await api.saveNetworkPlan(
        projectId,
        buildNetworkPlanBody({ resources, assignmentRows, projectName, summary }),
      );
      dispatch({ type: 'SET_PROJECT_STATUS', payload: 'Project saved to Postgres.' });
      dispatch({ type: 'SET_AUTO_SAVE_STATUS', payload: 'Network plan saved.' });
      dispatch({ type: 'SET_IS_DIRTY', payload: false });
      hasLoadedProject.current = true;
      dispatch({ type: 'SET_SAVE_MODAL_OPEN', payload: false });
      api.listProjects().then((p) => dispatch({ type: 'SET_PROJECTS', payload: p })).catch(() => {});
    } catch (error) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: error instanceof Error ? error.message : 'Project save failed.' });
    }
  }

  async function loadProjectById(projectId: string) {
    if (!projectId) return;
    dispatch({ type: 'SET_PROJECT_STATUS', payload: '' });
    dispatch({ type: 'SET_PROJECT_ERROR', payload: '' });
    try {
      const { project, state: savedState } = await api.loadProject(projectId);
      dispatch({ type: 'SET_SELECTED_PROJECT_ID', payload: project.id });
      dispatch({ type: 'SET_PROJECT_NAME', payload: project.name || 'Migration assessment' });
      dispatch({ type: 'SET_PROJECT_DESCRIPTION', payload: project.description || '' });
      if (savedState?.planning_state_json?.carbon_summary) {
        dispatch({ type: 'SET_SUMMARY', payload: savedState.planning_state_json.carbon_summary });
      }
      if (savedState?.planning_state_json?.carbon_assignment_rows) {
        dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: savedState.planning_state_json.carbon_assignment_rows });
      } else if (savedState?.planning_state_json?.carbon_summary) {
        dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: rowsFromSummary(savedState.planning_state_json.carbon_summary) });
      }
      if (savedState?.planning_state_json?.carbon_resources) {
        dispatch({ type: 'SET_RESOURCES', payload: savedState.planning_state_json.carbon_resources });
      }
      if (savedState?.planning_state_json?.carbon_remediation_tracker || savedState?.planning_state_json?.remediation_tracker) {
        dispatch({
          type: 'SET_REMEDIATION_TRACKER',
          payload: normalizeRemediationTracker(
            savedState.planning_state_json.carbon_remediation_tracker || savedState.planning_state_json.remediation_tracker,
          ),
        });
      } else {
        dispatch({ type: 'SET_REMEDIATION_TRACKER', payload: {} });
      }
      if (savedState?.planning_state_json?.carbon_image_import_status || savedState?.planning_state_json?.image_import_status) {
        dispatch({
          type: 'SET_IMAGE_IMPORT_STATUS',
          payload: normalizeImageImportStatus(
            savedState.planning_state_json.carbon_image_import_status || savedState.planning_state_json.image_import_status,
          ),
        });
      } else {
        dispatch({ type: 'SET_IMAGE_IMPORT_STATUS', payload: {} });
      }
      if (savedState?.planning_state_json?.carbon_suggestion_audit || savedState?.planning_state_json?.suggestion_audit) {
        dispatch({
          type: 'SET_SUGGESTION_AUDIT',
          payload: normalizeSuggestionAudit(
            savedState.planning_state_json.carbon_suggestion_audit || savedState.planning_state_json.suggestion_audit,
          ),
        });
      } else {
        dispatch({ type: 'SET_SUGGESTION_AUDIT', payload: [] });
      }
      try {
        const networkPlan = await api.loadNetworkPlan(projectId);
        const nextResources = resourcesFromNetworkPlan(networkPlan);
        const baseRows = savedState?.planning_state_json?.carbon_assignment_rows
          || (savedState?.planning_state_json?.carbon_summary ? rowsFromSummary(savedState.planning_state_json.carbon_summary) : assignmentRows);
        const hasPersistedResources = [
          nextResources.vpcs,
          nextResources.subnets,
          nextResources.securityGroups,
          nextResources.storageProfiles,
          nextResources.waves,
          nextResources.networkComponents,
        ].some((bucket) => bucket.length > 0);
        if (hasPersistedResources) {
          dispatch({ type: 'SET_RESOURCES', payload: nextResources });
        }
        dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: rowsFromNetworkPlan(networkPlan, baseRows) });
      } catch {
        // Legacy project state may not have a Carbon network plan yet.
      }
      dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [] });
      dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
      dispatch({ type: 'SET_IS_DIRTY', payload: false });
      dispatch({ type: 'SET_AUTO_SAVE_ERROR', payload: '' });
      hasLoadedProject.current = true;
      dispatch({ type: 'SET_PROJECT_STATUS', payload: `Loaded ${project.name}. Assignment buckets and VM planning state restored.` });
    } catch (error) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: error instanceof Error ? error.message : 'Project load failed.' });
    }
  }

  function renderWorkflow() {
    switch (activeWorkflow) {
      case 'intake': return <IntakeWorkflow />;
      case 'assignment': return <AssignmentWorkflow />;
      case 'overrides': return <OverridesWorkflow />;
      case 'remediation': return <RemediationWorkflow />;
      case 'imageImport': return <ImageImportWorkflow />;
      case 'migrationOps': return <MigrationOpsWorkflow />;
      case 'network': return <NetworkPlanWorkflow />;
      case 'security': return <SecurityWorkflow />;
      case 'storage': return <StorageWorkflow />;
      case 'waves': return <WavesWorkflow />;
      case 'export': return <ExportWorkflow />;
      default: return <OverviewWorkflow />;
    }
  }

  return (
    <>
      <Header aria-label="RVTools to IBM Cloud">
        <HeaderName href="#" prefix="IBM Cloud">
          RVTools migration workbench
        </HeaderName>
        <HeaderGlobalBar>
          <HeaderGlobalAction
            aria-label="API status"
            tooltipAlignment="end"
            onClick={() => dispatch({ type: 'SET_PANEL_OPEN', payload: !panelOpen })}
          >
            <Information size={20} />
          </HeaderGlobalAction>
        </HeaderGlobalBar>
        <HeaderPanel expanded={panelOpen} aria-label="API status panel">
          <div className="status-panel">
            <p className="status-title">Prototype status</p>
            <Tag type={apiStatus.includes('online') ? 'green' : 'red'}>{apiStatus}</Tag>
            <p>
              Streamlit remains the supported app. This Carbon shell evaluates a
              future IBM Cloud-style planning experience.
            </p>
          </div>
        </HeaderPanel>
      </Header>

      <SideNav aria-label="Workbench navigation" expanded isPersistent>
        <SideNavItems>
          {workflows.map((workflow) => (
            <SideNavLink
              key={workflow.id}
              renderIcon={workflow.icon}
              href={`#${workflow.id}`}
              isActive={activeWorkflow === workflow.id}
              onClick={(event) => {
                event.preventDefault();
                dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: workflow.id });
              }}
            >
              {workflow.label}
            </SideNavLink>
          ))}
        </SideNavItems>
      </SideNav>

      <Content className="workbench-content">
        <Grid fullWidth className="workbench-grid">
          <Column lg={16} md={8} sm={4}>
            <div className="page-heading">
              <div>
                <p className="eyebrow">Experimental Carbon prototype</p>
                <h1>RVTools to IBM Cloud VPC</h1>
              </div>
              <div className="project-controls">
                <div className="save-state-indicator" aria-label="Project save state">
                  <Tag type={saveState.tagType}>{saveState.label}</Tag>
                  <span>{saveState.detail}</span>
                </div>
                <Select
                  id="project"
                  labelText="Saved project"
                  value={selectedProjectId}
                  onChange={(event) => dispatch({ type: 'SET_SELECTED_PROJECT_ID', payload: event.target.value })}
                >
                  <SelectItem text="New project" value="" />
                  {projects.map((project) => (
                    <SelectItem
                      key={project.id}
                      text={`${project.name} (${project.id.slice(0, 8)})`}
                      value={project.id}
                    />
                  ))}
                </Select>
                <Button kind="tertiary" renderIcon={Renew} onClick={() => loadProjectById(selectedProjectId)} disabled={!selectedProjectId}>
                  Load
                </Button>
                <Button kind="secondary" renderIcon={Save} onClick={() => dispatch({ type: 'SET_SAVE_MODAL_OPEN', payload: true })}>
                  Save project
                </Button>
              </div>
            </div>
            {projectStatus && (
              <InlineNotification
                kind="success"
                lowContrast
                title={projectStatus}
                subtitle="Carbon project save uses the same FastAPI/Postgres persistence layer as the prototype API."
              />
            )}
            {projectError && (
              <InlineNotification
                kind="error"
                lowContrast
                title="Project action failed"
                subtitle={projectError}
              />
            )}
            {!persistenceEnabled && apiStatus !== 'Checking API' && (
              <InlineNotification
                kind="warning"
                lowContrast
                title="Persistence unavailable"
                subtitle="Postgres persistence is disabled or the API is offline. Save, load, autosave, assignment sync, and Terraform ZIP export need the FastAPI persistence layer."
              />
            )}
            {autoSaveStatus && persistenceEnabled && (
              <InlineNotification
                kind="info"
                lowContrast
                title={autoSaveStatus}
                subtitle={isDirty ? 'Unsaved changes are queued.' : 'Latest Carbon network-plan payload is persisted.'}
              />
            )}
            {autoSaveError && (
              <InlineNotification
                kind="error"
                lowContrast
                title="Autosave failed"
                subtitle={autoSaveError}
              />
            )}
            {uploadStatus && activeWorkflow !== 'intake' && (
              <InlineNotification
                kind="success"
                lowContrast
                title={uploadStatus}
                subtitle="Workbook data is loaded into the VM Assignment Workbench."
              />
            )}
          </Column>

          <Column lg={4} md={4} sm={4}>
            <MetricTileInline label="In scope" value={computedEstate.in_scope} helper="Active VM candidates" onClick={() => {
              dispatch({ type: 'SET_READINESS_FILTER', payload: 'all' });
              dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
            }} />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTileInline label="Remediation items" value={activeRemediationCount} helper="Active blocker tracking" onClick={() => {
              dispatch({ type: 'SET_READINESS_FILTER', payload: 'Blocked' });
              dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'remediation' });
            }} />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTileInline label="Missing subnet" value={planningCompleteness.missingSubnet} helper="Target placement gaps" onClick={() => {
              dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: 'network' });
              dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
            }} />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTileInline label="Missing SG" value={planningCompleteness.missingSg} helper="Security group gaps" onClick={() => {
              dispatch({ type: 'SET_ASSIGNMENT_MODE', payload: 'security' });
              dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
            }} />
          </Column>

          <Column lg={16} md={8} sm={4}>
            {renderWorkflow()}
          </Column>
        </Grid>
      </Content>

      <Modal
        open={saveModalOpen}
        modalHeading="Save project"
        primaryButtonText={selectedProjectId ? 'Update project' : 'Create project'}
        secondaryButtonText="Cancel"
        onRequestClose={() => dispatch({ type: 'SET_SAVE_MODAL_OPEN', payload: false })}
        onRequestSubmit={saveProject}
      >
        <p>
          Save the current Carbon assignment rows, resource buckets, and
          planning-state compatible decisions to the shared FastAPI/Postgres
          persistence layer.
        </p>
        <TextInput
          id="carbon-project-name"
          labelText="Project name"
          value={projectName}
          onChange={(event) => dispatch({ type: 'SET_PROJECT_NAME', payload: event.target.value })}
        />
        <TextArea
          id="carbon-project-description"
          labelText="Description"
          value={projectDescription}
          onChange={(event) => dispatch({ type: 'SET_PROJECT_DESCRIPTION', payload: event.target.value })}
        />
      </Modal>
    </>
  );
}

// Inline MetricTile (kept local to shell — not imported from components/ui to avoid circular deps)
function MetricTileInline({ label, value, helper, onClick }) {
  return (
    <Tile className={onClick ? 'metric-tile metric-tile--button' : 'metric-tile'} onClick={onClick}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-helper">{helper}</p>
    </Tile>
  );
}

export default function WorkbenchPage() {
  return (
    <AppProvider>
      <WorkbenchShell />
    </AppProvider>
  );
}
