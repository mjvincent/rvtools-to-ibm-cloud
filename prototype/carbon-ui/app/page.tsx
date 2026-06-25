// @ts-nocheck
'use client';

import React, { useEffect } from 'react';
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
import type { Workflow } from '../types/network-planning';

import OverviewWorkflow from '../components/workflows/OverviewWorkflow';
import IntakeWorkflow from '../components/workflows/IntakeWorkflow';
import AssignmentWorkflow from '../components/workflows/AssignmentWorkflow';
import NetworkPlanWorkflow from '../components/workflows/NetworkPlanWorkflow';
import SecurityWorkflow from '../components/workflows/SecurityWorkflow';
import StorageWorkflow from '../components/workflows/StorageWorkflow';
import WavesWorkflow from '../components/workflows/WavesWorkflow';
import ExportWorkflow from '../components/workflows/ExportWorkflow';

const workflows: Array<{ id: Workflow; label: string; icon?: React.ComponentType }> = [
  { id: 'overview', label: 'Overview', icon: DataTableIcon },
  { id: 'intake', label: 'Workbook Intake', icon: CloudUpload },
  { id: 'assignment', label: 'VM Assignment', icon: DeploymentPattern },
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
    'Exclude?': false,
    'Override Profile': row.overrideProfile,
    'Override Storage Tier': row.overrideStorageTier,
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

function WorkbenchShell() {
  const { state, dispatch } = useAppState();
  const {
    apiStatus, panelOpen, saveModalOpen, projects, selectedProjectId,
    projectName, projectDescription, projectStatus, projectError, uploadStatus,
    activeWorkflow, assignmentRows, resources, summary,
  } = state;

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

  useEffect(() => {
    api.checkApiHealth()
      .then((payload) => {
        dispatch({ type: 'SET_API_STATUS', payload: payload.persistence_enabled ? 'API online with persistence' : 'API online' });
        if (payload.persistence_enabled) {
          api.listProjects().then((projects) => dispatch({ type: 'SET_PROJECTS', payload: projects })).catch(() => {});
        }
      })
      .catch(() => dispatch({ type: 'SET_API_STATUS', payload: 'API unavailable' }));
  }, []);

  // Refresh derived rows when workflow changes
  useEffect(() => {
    if (summary) {
      const refreshedRows = rowsFromSummary(summary);
      if (JSON.stringify(refreshedRows) !== JSON.stringify(assignmentRows)) {
        dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: refreshedRows });
      }
    }
  }, [activeWorkflow, summary]);

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
        schema_version: 'carbon-prototype-0.2',
        metadata: { project_name: projectName.trim(), source: 'carbon-ui-prototype' },
        vm_decisions: assignmentRows.map(vmDecision),
        wave_planning: assignmentRows.map(waveDecision),
        carbon_summary: summary,
        carbon_assignment_rows: assignmentRows,
        carbon_resources: resources,
      }, projectName.trim());
      dispatch({ type: 'SET_PROJECT_STATUS', payload: 'Project saved to Postgres.' });
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
      dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [] });
      dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
      dispatch({ type: 'SET_PROJECT_STATUS', payload: `Loaded ${project.name}. Assignment buckets and VM planning state restored.` });
    } catch (error) {
      dispatch({ type: 'SET_PROJECT_ERROR', payload: error instanceof Error ? error.message : 'Project load failed.' });
    }
  }

  function renderWorkflow() {
    switch (activeWorkflow) {
      case 'intake': return <IntakeWorkflow />;
      case 'assignment': return <AssignmentWorkflow />;
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
            <MetricTileInline label="Readiness blockers" value={computedEstate.blocked} helper="Signals to resolve" onClick={() => {
              dispatch({ type: 'SET_READINESS_FILTER', payload: 'Blocked' });
              dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
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
