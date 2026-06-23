// This prototype intentionally keeps Carbon render-prop typing loose while the
// UX direction is evaluated against the supported Streamlit app.
// @ts-nocheck
'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Column,
  Content,
  FileUploaderDropContainer,
  Grid,
  Header,
  HeaderGlobalBar,
  HeaderGlobalAction,
  HeaderName,
  HeaderPanel,
  InlineNotification,
  Layer,
  Modal,
  Select,
  SelectItem,
  SideNav,
  SideNavItems,
  SideNavLink,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
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

type EstateSummary = {
  in_scope: number;
  excluded: number;
  monthly: number;
  savings: number;
  blocked: number;
  review: number;
};

type WorkbookSummary = {
  filename: string;
  estate_summary: EstateSummary;
  overview_blockers: Record<string, number>;
  readiness_counts: Record<string, Record<string, number>>;
  assessment_quality: Record<string, string | number>;
  readiness_rows: Array<Record<string, string | number>>;
};

type SavedProject = {
  id: string;
  name: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
};

type SavedProjectState = {
  planning_state_json?: {
    carbon_summary?: WorkbookSummary;
    metadata?: Record<string, string>;
  };
};

const sampleRows = [
  {
    id: 'sample-1',
    name: 'app-01',
    image: 'Ready',
    migration: 'Review',
    memory: 'Ready',
    network: 'Ready',
    power: 'poweredOn',
  },
  {
    id: 'sample-2',
    name: 'db-01',
    image: 'Review',
    migration: 'Blocked',
    memory: 'Review',
    network: 'Ready',
    power: 'poweredOn',
  },
  {
    id: 'sample-3',
    name: 'web-01',
    image: 'Ready',
    migration: 'Ready',
    memory: 'Ready',
    network: 'Review',
    power: 'poweredOff',
  },
];

const headers = [
  { key: 'name', header: 'VM' },
  { key: 'image', header: 'Image' },
  { key: 'migration', header: 'Migration' },
  { key: 'memory', header: 'Memory' },
  { key: 'network', header: 'Network' },
  { key: 'power', header: 'Power' },
];

function MetricTile({
  label,
  value,
  helper,
}: {
  label: string;
  value: string | number;
  helper: string;
}) {
  return (
    <Tile className="metric-tile">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-helper">{helper}</p>
    </Tile>
  );
}

function toRows(summary: WorkbookSummary | null) {
  if (!summary) {
    return sampleRows;
  }
  return summary.readiness_rows.map((row, index) => ({
    id: `${row['VM Name'] || index}`,
    name: String(row['VM Name'] || ''),
    image: String(row['Image Readiness'] || ''),
    migration: String(row['Migration Readiness'] || ''),
    memory: String(row['Memory Readiness'] || ''),
    network: String(row['Network Readiness'] || ''),
    power: String(row['Power State'] || ''),
  }));
}

export default function WorkbenchPage() {
  const [summary, setSummary] = useState<WorkbookSummary | null>(null);
  const [apiStatus, setApiStatus] = useState('Checking API');
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [panelOpen, setPanelOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [projects, setProjects] = useState<SavedProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [projectName, setProjectName] = useState('Migration assessment');
  const [projectDescription, setProjectDescription] = useState('');
  const [projectStatus, setProjectStatus] = useState('');
  const [projectError, setProjectError] = useState('');

  useEffect(() => {
    fetch('/health')
      .then((response) => response.json())
      .then((payload) => {
        setApiStatus(payload.persistence_enabled ? 'API online with persistence' : 'API online');
        if (payload.persistence_enabled) {
          refreshProjects();
        }
      })
      .catch(() => setApiStatus('API unavailable'));
  }, []);

  const estate = summary?.estate_summary || {
    in_scope: 0,
    excluded: 0,
    monthly: 0,
    savings: 0,
    blocked: 0,
    review: 0,
  };
  const rows = useMemo(() => toRows(summary), [summary]);

  async function handleUpload(_event, content) {
    const file = content?.addedFiles?.[0];
    if (!file) {
      return;
    }
    setUploadStatus(`Uploading ${file.name}`);
    setUploadError('');
    const formData = new FormData();
    formData.append('workbook', file);
    try {
      const response = await fetch('/api/workbooks/summary', {
        method: 'POST',
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Workbook upload failed.');
      }
      setSummary(payload);
      setProjectName(payload.filename.replace(/\.xlsx$/i, '') || projectName);
      setUploadStatus(`Loaded ${payload.filename}`);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Workbook upload failed.');
      setUploadStatus('');
    }
  }

  async function refreshProjects() {
    try {
      const response = await fetch('/api/projects');
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Could not load saved projects.');
      }
      setProjects(payload.projects || []);
    } catch (error) {
      setProjectError(error instanceof Error ? error.message : 'Could not load saved projects.');
    }
  }

  async function saveProject() {
    setProjectStatus('');
    setProjectError('');
    try {
      if (!projectName.trim()) {
        throw new Error('Enter a project name before saving.');
      }
      let projectId = selectedProjectId;
      if (!projectId) {
        const createResponse = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: projectName.trim(),
            description: projectDescription.trim(),
          }),
        });
        const createPayload = await createResponse.json();
        if (!createResponse.ok) {
          throw new Error(createPayload.detail || 'Could not create project.');
        }
        projectId = createPayload.project.id;
        setSelectedProjectId(projectId);
      } else {
        const updateResponse = await fetch(`/api/projects/${projectId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: projectName.trim(),
            description: projectDescription.trim(),
          }),
        });
        const updatePayload = await updateResponse.json();
        if (!updateResponse.ok) {
          throw new Error(updatePayload.detail || 'Could not update project.');
        }
      }

      const stateResponse = await fetch(`/api/projects/${projectId}/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planning_state: {
            schema_version: 'carbon-prototype-0.1',
            metadata: {
              project_name: projectName.trim(),
              source: 'carbon-ui-prototype',
            },
            carbon_summary: summary,
          },
          project_name: projectName.trim(),
        }),
      });
      const statePayload = await stateResponse.json();
      if (!stateResponse.ok) {
        throw new Error(statePayload.detail || 'Could not save project state.');
      }
      setProjectStatus('Project saved to Postgres.');
      setModalOpen(false);
      await refreshProjects();
    } catch (error) {
      setProjectError(error instanceof Error ? error.message : 'Project save failed.');
    }
  }

  async function loadProject(projectId: string) {
    if (!projectId) {
      return;
    }
    setProjectStatus('');
    setProjectError('');
    try {
      const response = await fetch(`/api/projects/${projectId}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Could not load project.');
      }
      const project = payload.project as SavedProject;
      const state = payload.state as SavedProjectState | null;
      setSelectedProjectId(project.id);
      setProjectName(project.name || 'Migration assessment');
      setProjectDescription(project.description || '');
      if (state?.planning_state_json?.carbon_summary) {
        setSummary(state.planning_state_json.carbon_summary);
      }
      setProjectStatus(`Loaded ${project.name}. Upload the matching workbook before production restore.`);
    } catch (error) {
      setProjectError(error instanceof Error ? error.message : 'Project load failed.');
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
            onClick={() => setPanelOpen(!panelOpen)}
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
              future IBM Cloud-style experience.
            </p>
          </div>
        </HeaderPanel>
      </Header>

      <SideNav aria-label="Workbench navigation" expanded isPersistent>
        <SideNavItems>
          <SideNavLink renderIcon={CloudUpload} href="#upload">Upload</SideNavLink>
          <SideNavLink renderIcon={DataTableIcon} href="#readiness">Readiness</SideNavLink>
          <SideNavLink renderIcon={DeploymentPattern} href="#export">Export</SideNavLink>
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
                  onChange={(event) => setSelectedProjectId(event.target.value)}
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
                <Button kind="tertiary" renderIcon={Renew} onClick={() => loadProject(selectedProjectId)} disabled={!selectedProjectId}>
                  Load
                </Button>
                <Button kind="secondary" renderIcon={Save} onClick={() => setModalOpen(true)}>
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
          </Column>

          <Column lg={4} md={4} sm={4}>
            <MetricTile label="In scope" value={estate.in_scope} helper="Active VM candidates" />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTile label="Readiness blockers" value={estate.blocked} helper="Signals to resolve" />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTile label="Monthly estimate" value={`$${estate.monthly.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} helper="Static catalog basis" />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTile label="Potential savings" value={`$${estate.savings.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} helper="Right-sizing delta" />
          </Column>

          <Column lg={16} md={8} sm={4}>
            <Layer className="workbench-section" id="upload">
              <div className="section-header">
                <div>
                  <h2>Workbook intake</h2>
                  <p>Drag and drop a standard RVTools workbook to populate the live summary slice.</p>
                </div>
                <Tag type="blue">Real API integration</Tag>
              </div>
              <FileUploaderDropContainer
                accept={['.xlsx']}
                labelText="Drag and drop RVTools .xlsx here or click to upload"
                multiple={false}
                name="workbook"
                onAddFiles={handleUpload}
              />
              {uploadStatus && (
                <InlineNotification
                  kind="success"
                  lowContrast
                  title={uploadStatus}
                  subtitle="Estate summary and readiness rows came from the FastAPI prototype."
                />
              )}
              {uploadError && (
                <InlineNotification
                  kind="error"
                  lowContrast
                  title="Upload failed"
                  subtitle={uploadError}
                />
              )}
            </Layer>
          </Column>

          <Column lg={16} md={8} sm={4}>
            <Layer className="workbench-section" id="readiness">
              <Tabs>
                <TabList aria-label="Workbench views">
                  <Tab>Overview</Tab>
                  <Tab>Readiness</Tab>
                  <Tab>Planning</Tab>
                  <Tab>Export</Tab>
                </TabList>
                <TabPanels>
                  <TabPanel>
                    <div className="summary-grid">
                      <Tile>
                        <h3>Assessment quality</h3>
                        <p>{summary ? String(summary.assessment_quality.overall_confidence || 'Unknown') : 'Sample preview'}</p>
                      </Tile>
                      <Tile>
                        <h3>Next action</h3>
                        <p>Resolve blocked readiness signals, then review wave and image import planning.</p>
                      </Tile>
                    </div>
                  </TabPanel>
                  <TabPanel>
                    <Table>
                      <TableHead>
                        <TableRow>
                          {headers.map((header) => (
                            <TableHeader key={header.key}>
                              {header.header}
                            </TableHeader>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {rows.map((row) => (
                          <TableRow key={row.id}>
                            <TableCell>{row.name}</TableCell>
                            <TableCell>{row.image}</TableCell>
                            <TableCell>{row.migration}</TableCell>
                            <TableCell>{row.memory}</TableCell>
                            <TableCell>{row.network}</TableCell>
                            <TableCell>{row.power}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TabPanel>
                  <TabPanel>
                    <div className="summary-grid">
                      <Tile>
                        <h3>Wave planning</h3>
                        <p>Mocked panel for assigning migration waves, owners, applications, and dependency groups.</p>
                      </Tile>
                      <Tile>
                        <h3>Image import planning</h3>
                        <p>Mocked panel for pending/imported/blocked source image groups.</p>
                      </Tile>
                    </div>
                  </TabPanel>
                  <TabPanel>
                    <div className="export-actions" id="export">
                      <InlineNotification
                        kind="info"
                        lowContrast
                        title="Prototype export readiness"
                        subtitle="The supported Terraform ZIP build remains in Streamlit while this UI is evaluated."
                      />
                      <Button renderIcon={Renew}>Run preflight preview</Button>
                      <Button kind="secondary" renderIcon={DeploymentPattern}>Review bundle contents</Button>
                    </div>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </Layer>
          </Column>
        </Grid>
      </Content>

      <Modal
        open={modalOpen}
        modalHeading="Save project"
        primaryButtonText={selectedProjectId ? 'Update project' : 'Create project'}
        secondaryButtonText="Cancel"
        onRequestClose={() => setModalOpen(false)}
        onRequestSubmit={saveProject}
      >
        <p>
          Save the current Carbon prototype summary to the shared FastAPI/Postgres
          persistence layer. Streamlit remains the production restore workflow.
        </p>
        <TextInput
          id="carbon-project-name"
          labelText="Project name"
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
        />
        <TextArea
          id="carbon-project-description"
          labelText="Description"
          value={projectDescription}
          onChange={(event) => setProjectDescription(event.target.value)}
        />
      </Modal>
    </>
  );
}
