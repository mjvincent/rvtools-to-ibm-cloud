'use client';

import React, { createContext, useContext, useReducer } from 'react';
import type {
  AssignmentMode,
  AssignmentVm,
  RemediationTracker,
  ResourceState,
  SavedProject,
  Workflow,
  WorkbookSummary,
} from '../types/network-planning';

// ─── Default data ─────────────────────────────────────────────────────────────

export const sampleRows: AssignmentVm[] = [
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

export const defaultResources: ResourceState = {
  vpcs: [
    {
      id: 'vpc-prod',
      name: 'prod-vpc',
      label: 'prod_vpc',
      region: 'us-south',
      addressPrefixMode: 'manual',
      addressPrefixes: [],
      tags: {},
      notes: 'Primary migration landing VPC',
      createdAt: '',
      updatedAt: '',
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
      publicGateway: false,
      tags: {},
      notes: '',
      createdAt: '',
      updatedAt: '',
    },
    {
      id: 'subnet-db',
      name: 'prod-db-us-south-1',
      label: 'prod_db_us_south_1',
      vpcId: 'vpc-prod',
      zone: 'us-south-1',
      cidr: '10.40.20.0/24',
      purpose: 'Database',
      publicGateway: false,
      tags: {},
      notes: '',
      createdAt: '',
      updatedAt: '',
    },
  ],
  securityGroups: [
    {
      id: 'sg-app',
      name: 'sg-app-private',
      label: 'sg_app_private',
      vpcId: 'vpc-prod',
      purpose: 'Private application traffic',
      rules: [],
      tags: {},
      notes: 'Review app-to-db and management ingress',
      createdAt: '',
      updatedAt: '',
    },
    {
      id: 'sg-db',
      name: 'sg-db-private',
      label: 'sg_db_private',
      vpcId: 'vpc-prod',
      purpose: 'Database traffic',
      rules: [],
      tags: {},
      notes: 'Restrict ingress to app and management subnets',
      createdAt: '',
      updatedAt: '',
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
      createdAt: '',
      updatedAt: '',
    },
    {
      id: 'storage-db',
      name: 'Database high IOPS',
      label: 'db_high_iops',
      tier: '10iops-tier',
      iopsIntent: 'Latency-sensitive database',
      notes: 'Use when owner validates higher IOPS need',
      createdAt: '',
      updatedAt: '',
    },
  ],
  waves: [
    {
      id: 'wave-1',
      name: 'Wave 1',
      owner: 'Migration factory',
      targetWindow: 'TBD',
      priority: 'medium',
      notes: 'Early low-risk application group',
      createdAt: '',
      updatedAt: '',
    },
    {
      id: 'wave-2',
      name: 'Wave 2',
      owner: 'Migration factory',
      targetWindow: 'TBD',
      priority: 'medium',
      notes: 'Dependent production workloads',
      createdAt: '',
      updatedAt: '',
    },
  ],
  networkComponents: [
    {
      id: 'component-public-gateway',
      name: 'prod-public-gateway',
      label: 'prod_public_gateway',
      type: 'public_gateway',
      vpcId: 'vpc-prod',
      attachment: 'prod-app-us-south-1',
      config: {},
      tags: {},
      notes: 'Outbound NAT for workloads that need patching or internet egress',
      createdAt: '',
      updatedAt: '',
    },
    {
      id: 'component-transit-gateway',
      name: 'enterprise-transit-gateway',
      label: 'enterprise_transit_gateway',
      type: 'vpn_gateway',
      vpcId: 'vpc-prod',
      attachment: 'prod-vpc',
      config: {},
      tags: {},
      notes: 'Private backbone connectivity placeholder',
      createdAt: '',
      updatedAt: '',
    },
  ],
};

// ─── State & Actions ──────────────────────────────────────────────────────────

export type AppState = {
  // upload state
  summary: WorkbookSummary | null;
  uploadStatus: string;
  uploadError: string;

  // project state
  projects: SavedProject[];
  selectedProjectId: string;
  projectName: string;
  projectDescription: string;
  projectStatus: string;
  projectError: string;

  // resource state
  resources: ResourceState;

  // assignment state
  assignmentRows: AssignmentVm[];
  remediationTracker: RemediationTracker;
  selectedVmIds: string[];
  searchValue: string;
  readinessFilter: string;
  sortKey: string;
  sortDirection: 'asc' | 'desc';

  // UI state
  apiStatus: string;
  persistenceEnabled: boolean;
  isDirty: boolean;
  autoSaveStatus: string;
  autoSaveError: string;
  panelOpen: boolean;
  saveModalOpen: boolean;
  bucketModal: AssignmentMode | 'vpc' | 'component' | '';
  activeWorkflow: Workflow;
  assignmentMode: AssignmentMode;
  bucketDraft: Record<string, string>;

  // terraform state
  terraformStatus: string;
  terraformError: string;
  generatingTerraform: boolean;
};

const initialState: AppState = {
  summary: null,
  uploadStatus: '',
  uploadError: '',
  projects: [],
  selectedProjectId: '',
  projectName: 'Migration assessment',
  projectDescription: '',
  projectStatus: '',
  projectError: '',
  resources: defaultResources,
  assignmentRows: sampleRows,
  remediationTracker: {},
  selectedVmIds: [],
  searchValue: '',
  readinessFilter: 'all',
  sortKey: 'name',
  sortDirection: 'asc',
  apiStatus: 'Checking API',
  persistenceEnabled: false,
  isDirty: false,
  autoSaveStatus: '',
  autoSaveError: '',
  panelOpen: false,
  saveModalOpen: false,
  bucketModal: '',
  activeWorkflow: 'assignment',
  assignmentMode: 'network',
  bucketDraft: {},
  terraformStatus: '',
  terraformError: '',
  generatingTerraform: false,
};

// ─── Action union ─────────────────────────────────────────────────────────────

export type AppAction =
  | { type: 'SET_SUMMARY'; payload: WorkbookSummary }
  | { type: 'SET_UPLOAD_STATUS'; payload: string }
  | { type: 'SET_UPLOAD_ERROR'; payload: string }
  | { type: 'SET_PROJECTS'; payload: SavedProject[] }
  | { type: 'SET_SELECTED_PROJECT_ID'; payload: string }
  | { type: 'SET_PROJECT_NAME'; payload: string }
  | { type: 'SET_PROJECT_DESCRIPTION'; payload: string }
  | { type: 'SET_PROJECT_STATUS'; payload: string }
  | { type: 'SET_PROJECT_ERROR'; payload: string }
  | { type: 'SET_RESOURCES'; payload: ResourceState }
  | { type: 'SET_ASSIGNMENT_ROWS'; payload: AssignmentVm[] }
  | { type: 'SET_REMEDIATION_TRACKER'; payload: RemediationTracker }
  | { type: 'SET_SELECTED_VM_IDS'; payload: string[] }
  | { type: 'SET_SEARCH_VALUE'; payload: string }
  | { type: 'SET_READINESS_FILTER'; payload: string }
  | { type: 'SET_SORT_KEY'; payload: string }
  | { type: 'SET_SORT_DIRECTION'; payload: 'asc' | 'desc' }
  | { type: 'SET_API_STATUS'; payload: string }
  | { type: 'SET_PERSISTENCE_ENABLED'; payload: boolean }
  | { type: 'SET_IS_DIRTY'; payload: boolean }
  | { type: 'SET_AUTO_SAVE_STATUS'; payload: string }
  | { type: 'SET_AUTO_SAVE_ERROR'; payload: string }
  | { type: 'SET_PANEL_OPEN'; payload: boolean }
  | { type: 'SET_SAVE_MODAL_OPEN'; payload: boolean }
  | { type: 'SET_BUCKET_MODAL'; payload: AssignmentMode | 'vpc' | 'component' | '' }
  | { type: 'SET_ACTIVE_WORKFLOW'; payload: Workflow }
  | { type: 'SET_ASSIGNMENT_MODE'; payload: AssignmentMode }
  | { type: 'SET_BUCKET_DRAFT'; payload: Record<string, string> }
  | { type: 'SET_TERRAFORM_STATUS'; payload: string }
  | { type: 'SET_TERRAFORM_ERROR'; payload: string }
  | { type: 'SET_GENERATING_TERRAFORM'; payload: boolean };

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_SUMMARY': return { ...state, summary: action.payload, isDirty: true };
    case 'SET_UPLOAD_STATUS': return { ...state, uploadStatus: action.payload };
    case 'SET_UPLOAD_ERROR': return { ...state, uploadError: action.payload };
    case 'SET_PROJECTS': return { ...state, projects: action.payload };
    case 'SET_SELECTED_PROJECT_ID': return { ...state, selectedProjectId: action.payload };
    case 'SET_PROJECT_NAME': return { ...state, projectName: action.payload };
    case 'SET_PROJECT_DESCRIPTION': return { ...state, projectDescription: action.payload };
    case 'SET_PROJECT_STATUS': return { ...state, projectStatus: action.payload };
    case 'SET_PROJECT_ERROR': return { ...state, projectError: action.payload };
    case 'SET_RESOURCES': return { ...state, resources: action.payload, isDirty: true };
    case 'SET_ASSIGNMENT_ROWS': return { ...state, assignmentRows: action.payload, isDirty: true };
    case 'SET_REMEDIATION_TRACKER': return { ...state, remediationTracker: action.payload, isDirty: true };
    case 'SET_SELECTED_VM_IDS': return { ...state, selectedVmIds: action.payload };
    case 'SET_SEARCH_VALUE': return { ...state, searchValue: action.payload };
    case 'SET_READINESS_FILTER': return { ...state, readinessFilter: action.payload };
    case 'SET_SORT_KEY': return { ...state, sortKey: action.payload };
    case 'SET_SORT_DIRECTION': return { ...state, sortDirection: action.payload };
    case 'SET_API_STATUS': return { ...state, apiStatus: action.payload };
    case 'SET_PERSISTENCE_ENABLED': return { ...state, persistenceEnabled: action.payload };
    case 'SET_IS_DIRTY': return { ...state, isDirty: action.payload };
    case 'SET_AUTO_SAVE_STATUS': return { ...state, autoSaveStatus: action.payload };
    case 'SET_AUTO_SAVE_ERROR': return { ...state, autoSaveError: action.payload };
    case 'SET_PANEL_OPEN': return { ...state, panelOpen: action.payload };
    case 'SET_SAVE_MODAL_OPEN': return { ...state, saveModalOpen: action.payload };
    case 'SET_BUCKET_MODAL': return { ...state, bucketModal: action.payload };
    case 'SET_ACTIVE_WORKFLOW': return { ...state, activeWorkflow: action.payload };
    case 'SET_ASSIGNMENT_MODE': return { ...state, assignmentMode: action.payload };
    case 'SET_BUCKET_DRAFT': return { ...state, bucketDraft: action.payload };
    case 'SET_TERRAFORM_STATUS': return { ...state, terraformStatus: action.payload };
    case 'SET_TERRAFORM_ERROR': return { ...state, terraformError: action.payload };
    case 'SET_GENERATING_TERRAFORM': return { ...state, generatingTerraform: action.payload };
    default: return state;
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────

type AppContextValue = {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppState(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useAppState must be used inside <AppProvider>');
  }
  return ctx;
}

// Made with Bob
