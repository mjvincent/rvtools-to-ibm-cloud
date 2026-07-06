'use client';

import React, { useMemo, useRef, useState } from 'react';
import { Button, InlineNotification, Layer, Search, Select, SelectItem, Tag, Tile } from '@carbon/react';
import { CloudUpload, Download, Renew } from '@carbon/icons-react';
import { useAppState } from '../../store/AppContext';
import type { Workflow } from '../../types/network-planning';
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
  const {
    assignmentRows,
    resources,
    selectedProjectId,
    projectName,
    summary,
    terraformStatus,
    terraformError,
    generatingTerraform,
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
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Saving latest network plan...' });
      await saveLatestNetworkPlan();
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
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Terraform ZIP downloaded.' });
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
            renderIcon={Renew}
            onClick={handleRunPreflight}
            disabled={!selectedProjectId || runningPreflight}
          >
            {runningPreflight ? 'Running...' : 'Run preflight'}
          </Button>
          <Button
            kind="secondary"
            size="sm"
            renderIcon={Download}
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
      <div className="resource-list">
        {findings.map(([label, count]) => (
          <Tile key={label} className="resource-tile">
            <h3>{label}</h3>
            <p>{count === 0 ? 'Ready' : `${count} item(s) need attention`}</p>
          </Tile>
        ))}
      </div>
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
                  <div className="package-tile__header">
                    <h3>{finding.Subject || 'Package'}</h3>
                    <Tag type={finding.Severity === 'blocker' ? 'red' : finding.Severity === 'warning' ? 'warm-gray' : 'gray'}>
                      {finding.Severity}
                    </Tag>
                  </div>
                  <p>{finding.Message}</p>
                  {finding['Fix Category'] && <p>{finding['Fix Category']}</p>}
                  <div className="network-actions">
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
                <strong>{selectedPreviewFile.path}</strong>
                <span>{selectedPreviewSize}</span>
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
