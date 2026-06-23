// This prototype intentionally keeps Carbon render-prop typing loose while the
// UX direction is evaluated against the supported Streamlit app.
// @ts-nocheck
'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Checkbox,
  Column,
  Content,
  FileUploaderDropContainer,
  Grid,
  Header,
  HeaderGlobalAction,
  HeaderGlobalBar,
  HeaderName,
  HeaderPanel,
  InlineNotification,
  Layer,
  Modal,
  Search,
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
  assignment_rows?: Array<Record<string, string | number>>;
};

type AssignmentVm = {
  id: string;
  name: string;
  image: string;
  imageReasons: string;
  migration: string;
  migrationReasons: string;
  memory: string;
  memoryReasons: string;
  networkReadiness: string;
  networkReasons: string;
  profile: string;
  overrideProfile: string;
  storageTier: string;
  overrideStorageTier: string;
  network: string;
  subnet: string;
  securityGroup: string;
  power: string;
  owner: string;
  application: string;
  wave: string;
  cutoverGroup: string;
  priority: string;
  dependencyGroup: string;
  storageLabel?: string;
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
    carbon_assignment_rows?: AssignmentVm[];
    carbon_resources?: ResourceState;
    metadata?: Record<string, string>;
  };
};

type VpcBucket = {
  id: string;
  name: string;
  label: string;
  region: string;
  notes: string;
};

type SubnetBucket = {
  id: string;
  name: string;
  label: string;
  vpcId: string;
  zone: string;
  cidr: string;
  purpose: string;
};

type SecurityBucket = {
  id: string;
  name: string;
  label: string;
  purpose: string;
  notes: string;
};

type StorageBucket = {
  id: string;
  name: string;
  label: string;
  tier: string;
  iopsIntent: string;
  notes: string;
};

type WaveBucket = {
  id: string;
  name: string;
  owner: string;
  targetWindow: string;
  notes: string;
};

type NetworkComponent = {
  id: string;
  name: string;
  label: string;
  type: string;
  vpcId: string;
  attachment: string;
  notes: string;
};

type ResourceState = {
  vpcs: VpcBucket[];
  subnets: SubnetBucket[];
  securityGroups: SecurityBucket[];
  storageProfiles: StorageBucket[];
  waves: WaveBucket[];
  networkComponents: NetworkComponent[];
};

type AssignmentMode = 'network' | 'security' | 'storage' | 'wave';
type Workflow =
  | 'overview'
  | 'intake'
  | 'assignment'
  | 'network'
  | 'security'
  | 'storage'
  | 'waves'
  | 'export';

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

const sampleRows: AssignmentVm[] = [
  {
    id: 'sample-app-01',
    name: 'app-01',
    image: 'Ready',
    imageReasons: '',
    migration: 'Review',
    migrationReasons: 'Validate owner and cutover group',
    memory: 'Ready',
    memoryReasons: '',
    networkReadiness: 'Ready',
    networkReasons: '',
    profile: 'bx2-2x8',
    overrideProfile: '',
    storageTier: '5iops-tier',
    overrideStorageTier: '',
    network: 'app-net',
    subnet: '',
    securityGroup: '',
    power: 'poweredOn',
    owner: '',
    application: 'App tier',
    wave: '',
    cutoverGroup: '',
    priority: '',
    dependencyGroup: '',
  },
  {
    id: 'sample-db-01',
    name: 'db-01',
    image: 'Review',
    imageReasons: 'Confirm image import path',
    migration: 'Blocked',
    migrationReasons: 'Resolve source migration finding',
    memory: 'Review',
    memoryReasons: 'Validate memory pressure before resizing',
    networkReadiness: 'Ready',
    networkReasons: '',
    profile: 'bx2-4x16',
    overrideProfile: '',
    storageTier: '10iops-tier',
    overrideStorageTier: '',
    network: 'db-net',
    subnet: '',
    securityGroup: '',
    power: 'poweredOn',
    owner: '',
    application: 'Database',
    wave: '',
    cutoverGroup: '',
    priority: '',
    dependencyGroup: '',
  },
  {
    id: 'sample-web-01',
    name: 'web-01',
    image: 'Ready',
    imageReasons: '',
    migration: 'Ready',
    migrationReasons: '',
    memory: 'Ready',
    memoryReasons: '',
    networkReadiness: 'Review',
    networkReasons: 'Validate public ingress rules',
    profile: 'bx2-2x8',
    overrideProfile: '',
    storageTier: '3iops-tier',
    overrideStorageTier: '',
    network: 'web-net',
    subnet: '',
    securityGroup: '',
    power: 'poweredOff',
    owner: '',
    application: 'Web tier',
    wave: '',
    cutoverGroup: '',
    priority: '',
    dependencyGroup: '',
  },
];

const defaultResources: ResourceState = {
  vpcs: [
    {
      id: 'vpc-prod',
      name: 'prod-vpc',
      label: 'prod_vpc',
      region: 'us-south',
      notes: 'Primary migration landing VPC',
    },
  ],
  subnets: [
    {
      id: 'subnet-app',
      name: 'prod-app-us-south-1',
      label: 'prod_app_us_south_1',
      vpcId: 'vpc-prod',
      zone: 'us-south-1',
      cidr: '10.40.10.0/24',
      purpose: 'Application',
    },
    {
      id: 'subnet-db',
      name: 'prod-db-us-south-1',
      label: 'prod_db_us_south_1',
      vpcId: 'vpc-prod',
      zone: 'us-south-1',
      cidr: '10.40.20.0/24',
      purpose: 'Database',
    },
  ],
  securityGroups: [
    {
      id: 'sg-app',
      name: 'sg-app-private',
      label: 'sg_app_private',
      purpose: 'Private application traffic',
      notes: 'Review app-to-db and management ingress',
    },
    {
      id: 'sg-db',
      name: 'sg-db-private',
      label: 'sg_db_private',
      purpose: 'Database traffic',
      notes: 'Restrict ingress to app and management subnets',
    },
  ],
  storageProfiles: [
    {
      id: 'storage-general',
      name: 'General purpose',
      label: 'general_purpose',
      tier: '3iops-tier',
      iopsIntent: 'Standard workload',
      notes: '',
    },
    {
      id: 'storage-db',
      name: 'Database high IOPS',
      label: 'db_high_iops',
      tier: '10iops-tier',
      iopsIntent: 'Latency-sensitive database',
      notes: 'Use when owner validates higher IOPS need',
    },
  ],
  waves: [
    {
      id: 'wave-1',
      name: 'Wave 1',
      owner: 'Migration factory',
      targetWindow: 'TBD',
      notes: 'Early low-risk application group',
    },
    {
      id: 'wave-2',
      name: 'Wave 2',
      owner: 'Migration factory',
      targetWindow: 'TBD',
      notes: 'Dependent production workloads',
    },
  ],
  networkComponents: [
    {
      id: 'component-public-gateway',
      name: 'prod-public-gateway',
      label: 'prod_public_gateway',
      type: 'Public Gateway',
      vpcId: 'vpc-prod',
      attachment: 'prod-app-us-south-1',
      notes: 'Outbound NAT for workloads that need patching or internet egress',
    },
    {
      id: 'component-transit-gateway',
      name: 'enterprise-transit-gateway',
      label: 'enterprise_transit_gateway',
      type: 'Transit Gateway',
      vpcId: 'vpc-prod',
      attachment: 'prod-vpc',
      notes: 'Private backbone connectivity placeholder',
    },
  ],
};

function textValue(value: unknown) {
  return value === null || value === undefined ? '' : String(value);
}

function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

function statusTagType(status: string) {
  if (status === 'Blocked') {
    return 'red';
  }
  if (status === 'Review') {
    return 'yellow';
  }
  if (status === 'Ready') {
    return 'green';
  }
  return 'gray';
}

function MetricTile({
  label,
  value,
  helper,
  onClick,
}: {
  label: string;
  value: string | number;
  helper: string;
  onClick?: () => void;
}) {
  return (
    <Tile className={onClick ? 'metric-tile metric-tile--button' : 'metric-tile'} onClick={onClick}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-helper">{helper}</p>
    </Tile>
  );
}

function ReadinessTag({ value }: { value: string }) {
  return <Tag type={statusTagType(value)}>{value || 'Unknown'}</Tag>;
}

function rowsFromSummary(summary: WorkbookSummary | null) {
  const sourceRows = summary?.assignment_rows || summary?.readiness_rows;
  if (!sourceRows || sourceRows.length === 0) {
    return sampleRows;
  }
  return sourceRows.map((row, index) => ({
    id: textValue(row['VM Key']) || textValue(row['VM Name']) || `vm-${index + 1}`,
    name: textValue(row['VM Name']),
    image: textValue(row['Image Readiness']),
    imageReasons: textValue(row['Readiness Reasons']),
    migration: textValue(row['Migration Readiness']),
    migrationReasons: textValue(row['Migration Readiness Reasons']),
    memory: textValue(row['Memory Readiness']),
    memoryReasons: textValue(row['Memory Readiness Reasons']),
    networkReadiness: textValue(row['Network Readiness']),
    networkReasons: textValue(row['Network Readiness Reasons']),
    profile: textValue(row['IBM Profile']),
    overrideProfile: textValue(row['Override Profile']),
    storageTier: textValue(row['Storage Tier']),
    overrideStorageTier: textValue(row['Override Storage Tier']),
    network: textValue(row['Network']),
    subnet: textValue(row['Subnet']),
    securityGroup: textValue(row['Security Group']),
    power: textValue(row['Power State']),
    owner: textValue(row['Owner']),
    application: textValue(row['Application']),
    wave: textValue(row['Wave']),
    cutoverGroup: textValue(row['Cutover Group']),
    priority: textValue(row['Priority']),
    dependencyGroup: textValue(row['Dependency Group']),
  }));
}

function vmDecision(row: AssignmentVm) {
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

function waveDecision(row: AssignmentVm) {
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

function newBucketId(prefix: string, name: string) {
  return `${prefix}-${terraformLabel(name)}-${Date.now()}`;
}

export default function WorkbenchPage() {
  const [summary, setSummary] = useState<WorkbookSummary | null>(null);
  const [assignmentRows, setAssignmentRows] = useState<AssignmentVm[]>(sampleRows);
  const [resources, setResources] = useState<ResourceState>(defaultResources);
  const [apiStatus, setApiStatus] = useState('Checking API');
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [panelOpen, setPanelOpen] = useState(false);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [bucketModal, setBucketModal] = useState<AssignmentMode | 'vpc' | 'component' | ''>('');
  const [activeWorkflow, setActiveWorkflow] = useState<Workflow>('assignment');
  const [assignmentMode, setAssignmentMode] = useState<AssignmentMode>('network');
  const [projects, setProjects] = useState<SavedProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [projectName, setProjectName] = useState('Migration assessment');
  const [projectDescription, setProjectDescription] = useState('');
  const [projectStatus, setProjectStatus] = useState('');
  const [projectError, setProjectError] = useState('');
  const [selectedVmIds, setSelectedVmIds] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [readinessFilter, setReadinessFilter] = useState('all');
  const [sortKey, setSortKey] = useState('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [bucketDraft, setBucketDraft] = useState<Record<string, string>>({});

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
    in_scope: assignmentRows.length,
    excluded: 0,
    monthly: 0,
    savings: 0,
    blocked: assignmentRows.filter((row) => (
      [row.image, row.migration, row.memory, row.networkReadiness].includes('Blocked')
    )).length,
    review: assignmentRows.filter((row) => (
      [row.image, row.migration, row.memory, row.networkReadiness].includes('Review')
    )).length,
  };

  const selectedRows = useMemo(
    () => assignmentRows.filter((row) => selectedVmIds.includes(row.id)),
    [assignmentRows, selectedVmIds],
  );

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
    return {
      total,
      missingSubnet,
      missingSg,
      missingStorage,
      missingWave,
      missingCidr,
      invalidLabels,
      ready: total - Math.max(missingSubnet, missingSg, missingStorage, missingWave),
    };
  }, [assignmentRows, resources]);

  const filteredRows = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    const rows = assignmentRows.filter((row) => {
      const matchesSearch = !query || [
        row.name,
        row.network,
        row.subnet,
        row.securityGroup,
        row.wave,
        row.application,
        row.owner,
      ].some((value) => value.toLowerCase().includes(query));
      const statuses = [row.image, row.migration, row.memory, row.networkReadiness];
      const matchesReadiness = readinessFilter === 'all' || statuses.includes(readinessFilter);
      return matchesSearch && matchesReadiness;
    });
    return [...rows].sort((left, right) => {
      const a = textValue(left[sortKey]).toLowerCase();
      const b = textValue(right[sortKey]).toLowerCase();
      if (a === b) {
        return left.name.localeCompare(right.name);
      }
      const result = a > b ? 1 : -1;
      return sortDirection === 'asc' ? result : -result;
    });
  }, [assignmentRows, readinessFilter, searchValue, sortDirection, sortKey]);

  function toggleSort(nextSortKey: string) {
    if (sortKey === nextSortKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(nextSortKey);
      setSortDirection('asc');
    }
  }

  function toggleSelected(rowId: string, checked: boolean) {
    setSelectedVmIds((current) => (
      checked ? [...new Set([...current, rowId])] : current.filter((id) => id !== rowId)
    ));
  }

  function toggleAllFiltered(checked: boolean) {
    if (checked) {
      setSelectedVmIds([...new Set([...selectedVmIds, ...filteredRows.map((row) => row.id)])]);
    } else {
      const filteredIds = new Set(filteredRows.map((row) => row.id));
      setSelectedVmIds(selectedVmIds.filter((id) => !filteredIds.has(id)));
    }
  }

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
      const nextRows = rowsFromSummary(payload);
      setSummary(payload);
      setAssignmentRows(nextRows);
      setSelectedVmIds([]);
      setProjectName(payload.filename.replace(/\.xlsx$/i, '') || projectName);
      setUploadStatus(`Loaded ${payload.filename}`);
      setActiveWorkflow('assignment');
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
            schema_version: 'carbon-prototype-0.2',
            metadata: {
              project_name: projectName.trim(),
              source: 'carbon-ui-prototype',
            },
            vm_decisions: assignmentRows.map(vmDecision),
            wave_planning: assignmentRows.map(waveDecision),
            carbon_summary: summary,
            carbon_assignment_rows: assignmentRows,
            carbon_resources: resources,
            carbon_validation: planningCompleteness,
          },
          project_name: projectName.trim(),
        }),
      });
      const statePayload = await stateResponse.json();
      if (!stateResponse.ok) {
        throw new Error(statePayload.detail || 'Could not save project state.');
      }
      setProjectStatus('Project saved to Postgres.');
      setSaveModalOpen(false);
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
      if (state?.planning_state_json?.carbon_assignment_rows) {
        setAssignmentRows(state.planning_state_json.carbon_assignment_rows);
      } else if (state?.planning_state_json?.carbon_summary) {
        setAssignmentRows(rowsFromSummary(state.planning_state_json.carbon_summary));
      }
      if (state?.planning_state_json?.carbon_resources) {
        setResources(state.planning_state_json.carbon_resources);
      }
      setSelectedVmIds([]);
      setActiveWorkflow('assignment');
      setProjectStatus(`Loaded ${project.name}. Assignment buckets and VM planning state restored.`);
    } catch (error) {
      setProjectError(error instanceof Error ? error.message : 'Project load failed.');
    }
  }

  function assignSelected(type: AssignmentMode, bucket) {
    if (selectedVmIds.length === 0) {
      setProjectError('Select one or more VMs before assigning a bucket.');
      return;
    }
    setProjectError('');
    setAssignmentRows((current) => current.map((row) => {
      if (!selectedVmIds.includes(row.id)) {
        return row;
      }
      if (type === 'network') {
        return {
          ...row,
          subnet: bucket.name,
          network: bucket.purpose || row.network,
        };
      }
      if (type === 'security') {
        return {
          ...row,
          securityGroup: bucket.name,
        };
      }
      if (type === 'storage') {
        return {
          ...row,
          overrideStorageTier: bucket.tier,
          storageLabel: bucket.label,
        };
      }
      return {
        ...row,
        wave: bucket.name,
        owner: row.owner || bucket.owner,
        cutoverGroup: row.cutoverGroup || bucket.name,
      };
    }));
    setProjectStatus(`${selectedVmIds.length} VM(s) assigned to ${bucket.name}.`);
  }

  function clearSelectedAssignment() {
    if (selectedVmIds.length === 0) {
      setProjectError('Select one or more VMs before clearing assignments.');
      return;
    }
    setProjectError('');
    setAssignmentRows((current) => current.map((row) => {
      if (!selectedVmIds.includes(row.id)) {
        return row;
      }
      if (assignmentMode === 'network') {
        return { ...row, subnet: '' };
      }
      if (assignmentMode === 'security') {
        return { ...row, securityGroup: '' };
      }
      if (assignmentMode === 'storage') {
        return { ...row, overrideStorageTier: '', storageLabel: '' };
      }
      return { ...row, wave: '', cutoverGroup: '' };
    }));
    setProjectStatus(`${selectedVmIds.length} VM assignment(s) cleared.`);
  }

  function openBucketModal(type: AssignmentMode | 'vpc' | 'component') {
    setBucketModal(type);
    if (type === 'vpc') {
      setBucketDraft({ name: '', label: '', region: 'us-south', notes: '' });
    } else if (type === 'component') {
      setBucketDraft({
        name: '',
        label: '',
        type: 'Public Gateway',
        vpcId: resources.vpcs[0]?.id || '',
        attachment: '',
        notes: '',
      });
    } else if (type === 'network') {
      setBucketDraft({
        name: '',
        label: '',
        vpcId: resources.vpcs[0]?.id || '',
        zone: 'us-south-1',
        cidr: '',
        purpose: '',
      });
    } else if (type === 'security') {
      setBucketDraft({ name: '', label: '', purpose: '', notes: '' });
    } else if (type === 'storage') {
      setBucketDraft({ name: '', label: '', tier: '3iops-tier', iopsIntent: '', notes: '' });
    } else {
      setBucketDraft({ name: '', owner: '', targetWindow: '', notes: '' });
    }
  }

  function createBucket() {
    const name = bucketDraft.name?.trim();
    if (!name) {
      setProjectError('Enter a bucket name before creating it.');
      return;
    }
    const label = terraformLabel(bucketDraft.label || name);
    if (bucketModal === 'vpc') {
      setResources((current) => ({
        ...current,
        vpcs: [...current.vpcs, {
          id: newBucketId('vpc', name),
          name,
          label,
          region: bucketDraft.region || 'us-south',
          notes: bucketDraft.notes || '',
        }],
      }));
    } else if (bucketModal === 'component') {
      setResources((current) => ({
        ...current,
        networkComponents: [...(current.networkComponents || []), {
          id: newBucketId('component', name),
          name,
          label,
          type: bucketDraft.type || 'Public Gateway',
          vpcId: bucketDraft.vpcId || current.vpcs[0]?.id || '',
          attachment: bucketDraft.attachment || '',
          notes: bucketDraft.notes || '',
        }],
      }));
    } else if (bucketModal === 'network') {
      setResources((current) => ({
        ...current,
        subnets: [...current.subnets, {
          id: newBucketId('subnet', name),
          name,
          label,
          vpcId: bucketDraft.vpcId || current.vpcs[0]?.id || '',
          zone: bucketDraft.zone || 'us-south-1',
          cidr: bucketDraft.cidr || '',
          purpose: bucketDraft.purpose || '',
        }],
      }));
    } else if (bucketModal === 'security') {
      setResources((current) => ({
        ...current,
        securityGroups: [...current.securityGroups, {
          id: newBucketId('sg', name),
          name,
          label,
          purpose: bucketDraft.purpose || '',
          notes: bucketDraft.notes || '',
        }],
      }));
    } else if (bucketModal === 'storage') {
      setResources((current) => ({
        ...current,
        storageProfiles: [...current.storageProfiles, {
          id: newBucketId('storage', name),
          name,
          label,
          tier: bucketDraft.tier || '3iops-tier',
          iopsIntent: bucketDraft.iopsIntent || '',
          notes: bucketDraft.notes || '',
        }],
      }));
    } else if (bucketModal === 'wave') {
      setResources((current) => ({
        ...current,
        waves: [...current.waves, {
          id: newBucketId('wave', name),
          name,
          owner: bucketDraft.owner || '',
          targetWindow: bucketDraft.targetWindow || '',
          notes: bucketDraft.notes || '',
        }],
      }));
    }
    setBucketModal('');
    setBucketDraft({});
    setProjectStatus(`${name} bucket created.`);
  }

  function assignmentBuckets() {
    if (assignmentMode === 'network') {
      return resources.subnets.map((bucket) => ({
        ...bucket,
        details: `${bucket.zone} | ${bucket.cidr || 'CIDR needed'} | ${bucket.purpose || 'No purpose label'}`,
      }));
    }
    if (assignmentMode === 'security') {
      return resources.securityGroups.map((bucket) => ({
        ...bucket,
        details: `${bucket.label} | ${bucket.purpose || 'No purpose label'}`,
      }));
    }
    if (assignmentMode === 'storage') {
      return resources.storageProfiles.map((bucket) => ({
        ...bucket,
        details: `${bucket.tier} | ${bucket.iopsIntent || 'No IOPS note'}`,
      }));
    }
    return resources.waves.map((bucket) => ({
      ...bucket,
      details: `${bucket.owner || 'No owner'} | ${bucket.targetWindow || 'No window'}`,
    }));
  }

  function renderWorkflowBody() {
    if (activeWorkflow === 'intake') {
      return renderIntake();
    }
    if (activeWorkflow === 'assignment') {
      return renderAssignmentWorkbench();
    }
    if (activeWorkflow === 'network') {
      return renderNetworkPlan();
    }
    if (activeWorkflow === 'security') {
      return renderResourcePlan('Security Plan', 'Create security group intent buckets for Terraform review and VM assignment.', resources.securityGroups.map((bucket) => ({
        name: bucket.name,
        detail: `${bucket.label} | ${bucket.purpose || 'No purpose label'}`,
      })));
    }
    if (activeWorkflow === 'storage') {
      return renderResourcePlan('Storage / IOPS Plan', 'Create storage intent buckets with labels that can later flow into Terraform naming and handoff files.', resources.storageProfiles.map((bucket) => ({
        name: bucket.name,
        detail: `${bucket.tier} | ${bucket.label} | ${bucket.iopsIntent || 'No IOPS note'}`,
      })));
    }
    if (activeWorkflow === 'waves') {
      return renderResourcePlan('Wave Plan', 'Group workloads into migration waves with owners and target windows.', resources.waves.map((bucket) => ({
        name: bucket.name,
        detail: `${bucket.owner || 'No owner'} | ${bucket.targetWindow || 'No target window'}`,
      })));
    }
    if (activeWorkflow === 'export') {
      return renderExportReadiness();
    }
    return renderOverview();
  }

  function renderIntake() {
    return (
      <Layer className="workbench-section">
        <div className="section-header">
          <div>
            <h2>Workbook intake</h2>
            <p>Drag and drop a standard RVTools workbook to populate the live VM assignment workbench.</p>
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
            subtitle="Estate summary, readiness rows, and assignment rows came from the FastAPI prototype."
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
    );
  }

  function renderAssignmentWorkbench() {
    const allFilteredSelected = filteredRows.length > 0 && filteredRows.every((row) => selectedVmIds.includes(row.id));
    return (
      <div className="assignment-layout">
        <Layer className="workbench-section assignment-main">
          <div className="section-header">
            <div>
              <h2>VM Assignment Workbench</h2>
              <p>Select VMs, then assign target subnet, security group, storage/IOPS, and wave buckets.</p>
            </div>
            <Tag type={selectedVmIds.length ? 'blue' : 'gray'}>{selectedVmIds.length} selected</Tag>
          </div>

          <div className="assignment-toolbar">
            <Search
              id="vm-assignment-search"
              labelText="Search VMs"
              placeholder="Search VM, network, subnet, security group, wave, owner"
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
            />
            <Select
              id="readiness-filter"
              labelText="Readiness filter"
              value={readinessFilter}
              onChange={(event) => setReadinessFilter(event.target.value)}
            >
              <SelectItem value="all" text="All readiness states" />
              <SelectItem value="Blocked" text="Blocked" />
              <SelectItem value="Review" text="Review" />
              <SelectItem value="Ready" text="Ready" />
            </Select>
          </div>

          <div className="vm-table-wrap">
            <table className="vm-table" aria-label="VM assignment rows">
              <thead>
                <tr>
                  <th>
                    <Checkbox
                      id="select-all-filtered"
                      labelText=""
                      checked={allFilteredSelected}
                      onChange={(_, data) => toggleAllFiltered(Boolean(data.checked))}
                    />
                  </th>
                  {[
                    ['name', 'VM'],
                    ['migration', 'Readiness'],
                    ['subnet', 'Subnet'],
                    ['securityGroup', 'Security group'],
                    ['overrideStorageTier', 'Storage / IOPS'],
                    ['wave', 'Wave'],
                    ['power', 'Power'],
                  ].map(([key, label]) => (
                    <th key={key}>
                      <button type="button" onClick={() => toggleSort(key)}>
                        {label}{sortKey === key ? ` ${sortDirection === 'asc' ? 'up' : 'down'}` : ''}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Checkbox
                        id={`select-${row.id}`}
                        labelText=""
                        checked={selectedVmIds.includes(row.id)}
                        onChange={(_, data) => toggleSelected(row.id, Boolean(data.checked))}
                      />
                    </td>
                    <td>
                      <strong>{row.name}</strong>
                      <span>{row.profile || 'No profile'} | {row.network || 'No source network'}</span>
                    </td>
                    <td>
                      <ReadinessTag value={row.image} />
                      <ReadinessTag value={row.migration} />
                      <ReadinessTag value={row.memory} />
                      <ReadinessTag value={row.networkReadiness} />
                    </td>
                    <td>{row.subnet || <span className="empty-value">Unassigned</span>}</td>
                    <td>{row.securityGroup || <span className="empty-value">Unassigned</span>}</td>
                    <td>{row.overrideStorageTier || row.storageTier || <span className="empty-value">Unassigned</span>}</td>
                    <td>{row.wave || <span className="empty-value">Unassigned</span>}</td>
                    <td>{row.power}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Layer>
        {renderAssignmentPanel()}
      </div>
    );
  }

  function renderAssignmentPanel() {
    return (
      <Layer className="workbench-section assignment-panel">
        <div className="section-header compact">
          <div>
            <h2>Assignment buckets</h2>
            <p>{selectedRows.length} VM(s) ready for assignment</p>
          </div>
        </div>
        <div className="mode-switcher" role="group" aria-label="Assignment bucket mode">
          {[
            ['network', 'Network'],
            ['security', 'Security'],
            ['storage', 'Storage / IOPS'],
            ['wave', 'Wave'],
          ].map(([mode, label]) => (
            <Button
              key={mode}
              kind={assignmentMode === mode ? 'primary' : 'tertiary'}
              size="sm"
              onClick={() => setAssignmentMode(mode as AssignmentMode)}
            >
              {label}
            </Button>
          ))}
        </div>
        <div className="bucket-actions">
          {assignmentMode === 'network' && (
            <Button kind="tertiary" size="sm" onClick={() => openBucketModal('vpc')}>
              Create VPC
            </Button>
          )}
          <Button kind="secondary" size="sm" onClick={() => openBucketModal(assignmentMode)}>
            {assignmentMode === 'network' ? 'Create subnet' : 'Create bucket'}
          </Button>
          <Button kind="ghost" size="sm" onClick={clearSelectedAssignment}>
            Clear selected
          </Button>
        </div>
        {assignmentMode === 'network' && (
          <div className="vpc-bucket-strip" aria-label="Planned VPC buckets">
            <p className="bucket-group-label">VPCs</p>
            {resources.vpcs.map((vpc) => (
              <Tile key={vpc.id} className="vpc-pill-tile">
                <strong>{vpc.name}</strong>
                <span>{vpc.region} | {vpc.label}</span>
              </Tile>
            ))}
          </div>
        )}
        <div className="bucket-list">
          {assignmentMode === 'network' && <p className="bucket-group-label">Subnets assignable to selected VMs</p>}
          {assignmentBuckets().map((bucket) => (
            <Tile key={bucket.id} className="bucket-tile">
              <div>
                <h3>{bucket.name}</h3>
                <p>{bucket.details}</p>
              </div>
              <Button size="sm" onClick={() => assignSelected(assignmentMode, bucket)}>
                Assign
              </Button>
            </Tile>
          ))}
        </div>
      </Layer>
    );
  }

  function renderOverview() {
    return (
      <Layer className="workbench-section">
        <div className="section-header">
          <div>
            <h2>Planning overview</h2>
            <p>Carbon is tracking target architecture intent while Streamlit remains the supported Terraform ZIP path.</p>
          </div>
          <Tag type="purple">Prototype planner</Tag>
        </div>
        <div className="summary-grid">
          <Tile>
            <h3>Assessment quality</h3>
            <p>{summary ? String(summary.assessment_quality.overall_confidence || 'Unknown') : 'Sample preview'}</p>
          </Tile>
          <Tile>
            <h3>Assignment completeness</h3>
            <p>{planningCompleteness.ready} of {planningCompleteness.total} VMs have the core planning assignments underway.</p>
          </Tile>
          <Tile>
            <h3>Open subnet assignments</h3>
            <p>{planningCompleteness.missingSubnet} VMs need target subnet placement.</p>
          </Tile>
          <Tile>
            <h3>Open security assignments</h3>
            <p>{planningCompleteness.missingSg} VMs need security group placement.</p>
          </Tile>
        </div>
      </Layer>
    );
  }

  function renderNetworkPlan() {
    const components = resources.networkComponents || [];
    return (
      <Layer className="workbench-section">
        <div className="section-header">
          <div>
            <h2>Network Plan</h2>
            <p>Build the target IBM Cloud VPC network intent and watch the topology preview update as resources are added.</p>
          </div>
          <div className="network-actions">
            <Button kind="tertiary" size="sm" onClick={() => openBucketModal('vpc')}>
              Create VPC
            </Button>
            <Button kind="tertiary" size="sm" onClick={() => openBucketModal('network')}>
              Create subnet
            </Button>
            <Button kind="secondary" size="sm" onClick={() => openBucketModal('component')}>
              Create network component
            </Button>
          </div>
        </div>

        <div className="network-diagram" aria-label="Generated network diagram">
          {resources.vpcs.map((vpc) => {
            const vpcSubnets = resources.subnets.filter((subnet) => subnet.vpcId === vpc.id);
            const vpcComponents = components.filter((component) => component.vpcId === vpc.id);
            return (
              <div className="diagram-vpc" key={vpc.id}>
                <div className="diagram-vpc-header">
                  <div>
                    <p className="diagram-kicker">VPC</p>
                    <h3>{vpc.name}</h3>
                  </div>
                  <Tag type="blue">{vpc.region}</Tag>
                </div>
                <div className="diagram-lane">
                  <p className="diagram-label">Subnets</p>
                  <div className="diagram-node-grid">
                    {vpcSubnets.map((subnet) => (
                      <div className="diagram-node" key={subnet.id}>
                        <strong>{subnet.name}</strong>
                        <span>{subnet.zone}</span>
                        <span>{subnet.cidr || 'CIDR needed'}</span>
                        <Tag type={subnet.cidr ? 'green' : 'red'}>{subnet.purpose || 'Unlabeled'}</Tag>
                      </div>
                    ))}
                    {vpcSubnets.length === 0 && (
                      <div className="diagram-node diagram-node--empty">No subnets created yet</div>
                    )}
                  </div>
                </div>
                <div className="diagram-lane">
                  <p className="diagram-label">Gateways, routing, and edge services</p>
                  <div className="diagram-component-grid">
                    {vpcComponents.map((component) => (
                      <div className="diagram-component" key={component.id}>
                        <Tag type="purple">{component.type}</Tag>
                        <strong>{component.name}</strong>
                        <span>{component.attachment || 'No attachment selected'}</span>
                      </div>
                    ))}
                    {vpcComponents.length === 0 && (
                      <div className="diagram-component diagram-node--empty">No network components created yet</div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="network-component-catalog">
          {[
            'Address Prefix',
            'Public Gateway',
            'VPN Gateway',
            'VPE Gateway',
            'Transit Gateway',
            'Application Load Balancer',
            'Network Load Balancer',
            'Route Table',
            'Security Group',
            'Network ACL',
            'Floating IP',
            'BYOIP Range',
            'Direct Link',
            'Direct Link on Classic',
          ].map((component) => (
            <Tag key={component} type="gray">{component}</Tag>
          ))}
        </div>
      </Layer>
    );
  }

  function renderResourcePlan(title: string, description: string, rows: Array<{ name: string; detail: string }>) {
    return (
      <Layer className="workbench-section">
        <div className="section-header">
          <div>
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
        </div>
        <div className="resource-list">
          {rows.map((row) => (
            <Tile key={`${title}-${row.name}`} className="resource-tile">
              <h3>{row.name}</h3>
              <p>{row.detail}</p>
            </Tile>
          ))}
        </div>
      </Layer>
    );
  }

  function renderExportReadiness() {
    const findings = [
      ['Missing subnet assignments', planningCompleteness.missingSubnet],
      ['Missing security group assignments', planningCompleteness.missingSg],
      ['Missing storage/IOPS assignments', planningCompleteness.missingStorage],
      ['Missing wave assignments', planningCompleteness.missingWave],
      ['Subnets missing CIDR', planningCompleteness.missingCidr],
      ['Labels needing Terraform cleanup', planningCompleteness.invalidLabels],
    ];
    return (
      <Layer className="workbench-section">
        <div className="section-header">
          <div>
            <h2>Export readiness</h2>
            <p>Carbon saves planning state now. Streamlit remains the production Terraform ZIP generator.</p>
          </div>
          <Tag type="gray">Save state only</Tag>
        </div>
        <div className="resource-list">
          {findings.map(([label, count]) => (
            <Tile key={label} className="resource-tile">
              <h3>{label}</h3>
              <p>{count === 0 ? 'Ready' : `${count} item(s) need attention`}</p>
            </Tile>
          ))}
        </div>
      </Layer>
    );
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
                setActiveWorkflow(workflow.id);
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
                <Button kind="secondary" renderIcon={Save} onClick={() => setSaveModalOpen(true)}>
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
            <MetricTile label="In scope" value={estate.in_scope} helper="Active VM candidates" onClick={() => setActiveWorkflow('assignment')} />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTile label="Readiness blockers" value={estate.blocked} helper="Signals to resolve" onClick={() => {
              setReadinessFilter('Blocked');
              setActiveWorkflow('assignment');
            }} />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTile label="Missing subnet" value={planningCompleteness.missingSubnet} helper="Target placement gaps" onClick={() => {
              setAssignmentMode('network');
              setActiveWorkflow('assignment');
            }} />
          </Column>
          <Column lg={4} md={4} sm={4}>
            <MetricTile label="Missing SG" value={planningCompleteness.missingSg} helper="Security group gaps" onClick={() => {
              setAssignmentMode('security');
              setActiveWorkflow('assignment');
            }} />
          </Column>

          <Column lg={16} md={8} sm={4}>
            {renderWorkflowBody()}
          </Column>
        </Grid>
      </Content>

      <Modal
        open={saveModalOpen}
        modalHeading="Save project"
        primaryButtonText={selectedProjectId ? 'Update project' : 'Create project'}
        secondaryButtonText="Cancel"
        onRequestClose={() => setSaveModalOpen(false)}
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
          onChange={(event) => setProjectName(event.target.value)}
        />
        <TextArea
          id="carbon-project-description"
          labelText="Description"
          value={projectDescription}
          onChange={(event) => setProjectDescription(event.target.value)}
        />
      </Modal>

      <Modal
        open={Boolean(bucketModal)}
        modalHeading={
          bucketModal === 'vpc'
            ? 'Create VPC bucket'
            : bucketModal === 'component'
              ? 'Create network component'
              : `Create ${assignmentMode === 'network' ? 'subnet' : assignmentMode} bucket`
        }
        primaryButtonText={bucketModal === 'component' ? 'Create component' : 'Create bucket'}
        secondaryButtonText="Cancel"
        onRequestClose={() => setBucketModal('')}
        onRequestSubmit={createBucket}
      >
        <TextInput
          id="bucket-name"
          labelText="Name"
          value={bucketDraft.name || ''}
          onChange={(event) => setBucketDraft({ ...bucketDraft, name: event.target.value, label: bucketDraft.label || terraformLabel(event.target.value) })}
        />
        {bucketModal !== 'wave' && (
          <TextInput
            id="bucket-label"
            labelText="Terraform label"
            value={bucketDraft.label || ''}
            onChange={(event) => setBucketDraft({ ...bucketDraft, label: terraformLabel(event.target.value) })}
          />
        )}
        {bucketModal === 'vpc' && (
          <TextInput
            id="bucket-region"
            labelText="Region"
            value={bucketDraft.region || ''}
            onChange={(event) => setBucketDraft({ ...bucketDraft, region: event.target.value })}
          />
        )}
        {bucketModal === 'component' && (
          <>
            <Select
              id="component-type"
              labelText="Component type"
              value={bucketDraft.type || 'Public Gateway'}
              onChange={(event) => setBucketDraft({ ...bucketDraft, type: event.target.value })}
            >
              <SelectItem value="Address Prefix" text="Address Prefix" />
              <SelectItem value="Public Gateway" text="Public Gateway" />
              <SelectItem value="VPN Gateway" text="VPN Gateway" />
              <SelectItem value="VPE Gateway" text="VPE Gateway" />
              <SelectItem value="Transit Gateway" text="Transit Gateway" />
              <SelectItem value="Application Load Balancer" text="Application Load Balancer" />
              <SelectItem value="Network Load Balancer" text="Network Load Balancer" />
              <SelectItem value="Route Table" text="Route Table" />
              <SelectItem value="Security Group" text="Security Group" />
              <SelectItem value="Network ACL" text="Network ACL" />
              <SelectItem value="Floating IP" text="Floating IP" />
              <SelectItem value="BYOIP Range" text="BYOIP Range" />
              <SelectItem value="Direct Link" text="Direct Link" />
              <SelectItem value="Direct Link on Classic" text="Direct Link on Classic" />
            </Select>
            <Select
              id="component-vpc"
              labelText="VPC"
              value={bucketDraft.vpcId || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, vpcId: event.target.value })}
            >
              {resources.vpcs.map((vpc) => (
                <SelectItem key={vpc.id} value={vpc.id} text={vpc.name} />
              ))}
            </Select>
            <TextInput
              id="component-attachment"
              labelText="Attachment or target"
              value={bucketDraft.attachment || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, attachment: event.target.value })}
            />
          </>
        )}
        {bucketModal === 'network' && (
          <>
            <Select
              id="bucket-vpc"
              labelText="VPC"
              value={bucketDraft.vpcId || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, vpcId: event.target.value })}
            >
              {resources.vpcs.map((vpc) => (
                <SelectItem key={vpc.id} value={vpc.id} text={vpc.name} />
              ))}
            </Select>
            <TextInput
              id="bucket-zone"
              labelText="Zone"
              value={bucketDraft.zone || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, zone: event.target.value })}
            />
            <TextInput
              id="bucket-cidr"
              labelText="CIDR"
              value={bucketDraft.cidr || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, cidr: event.target.value })}
            />
            <TextInput
              id="bucket-purpose"
              labelText="Purpose label"
              value={bucketDraft.purpose || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, purpose: event.target.value })}
            />
          </>
        )}
        {bucketModal === 'security' && (
          <TextInput
            id="bucket-purpose"
            labelText="Purpose label"
            value={bucketDraft.purpose || ''}
            onChange={(event) => setBucketDraft({ ...bucketDraft, purpose: event.target.value })}
          />
        )}
        {bucketModal === 'storage' && (
          <>
            <Select
              id="bucket-tier"
              labelText="Storage tier"
              value={bucketDraft.tier || '3iops-tier'}
              onChange={(event) => setBucketDraft({ ...bucketDraft, tier: event.target.value })}
            >
              <SelectItem value="3iops-tier" text="3iops-tier" />
              <SelectItem value="5iops-tier" text="5iops-tier" />
              <SelectItem value="10iops-tier" text="10iops-tier" />
            </Select>
            <TextInput
              id="bucket-iops-intent"
              labelText="IOPS intent"
              value={bucketDraft.iopsIntent || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, iopsIntent: event.target.value })}
            />
          </>
        )}
        {bucketModal === 'wave' && (
          <>
            <TextInput
              id="bucket-owner"
              labelText="Owner"
              value={bucketDraft.owner || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, owner: event.target.value })}
            />
            <TextInput
              id="bucket-window"
              labelText="Target window"
              value={bucketDraft.targetWindow || ''}
              onChange={(event) => setBucketDraft({ ...bucketDraft, targetWindow: event.target.value })}
            />
          </>
        )}
        {bucketModal !== 'network' && (
          <TextArea
            id="bucket-notes"
            labelText="Notes"
            value={bucketDraft.notes || ''}
            onChange={(event) => setBucketDraft({ ...bucketDraft, notes: event.target.value })}
          />
        )}
      </Modal>
    </>
  );
}
