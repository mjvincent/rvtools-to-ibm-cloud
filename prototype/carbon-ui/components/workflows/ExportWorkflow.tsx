'use client';

import React, { useMemo, useRef, useState } from 'react';
import { Button, Checkbox, InlineNotification, Layer, Search, Select, SelectItem, Tag, Tile } from '@carbon/react';
import { Close, CloudUpload, Download, Renew, View } from '@carbon/icons-react';
import { useAppState } from '../../store/AppContext';
import type { AssignmentVm, Workflow } from '../../types/network-planning';
import {
  generateTerraform,
  previewTerraform,
  runProjectPreflight,
  saveNetworkPlan,
  type PreflightResponse,
  type TerraformPreviewResponse,
} from '../../hooks/useApi';
import {
  packageFileCount,
} from '../../utils/package-inventory';
import {
  buildNetworkPlanBody,
  exportNetworkPlanJson,
  parseNetworkPlanJson,
  resourcesFromNetworkPlan,
  rowsFromNetworkPlan,
} from '../../utils/planning-state';
import PackageParityStatus from './export/PackageParityStatus';
import {
  applySuggestionsToRows,
  buildAssignmentSuggestions,
  buildExportChecklist,
  buildRemediationQueue,
  calculatePlanningCompleteness,
  confidenceTagType,
  downloadBrowserFile,
  filterPreviewFiles,
  handoffCsvFileCount,
  markSuggestionAuditReverted,
  packageGroups,
  packageParitySummary,
  planningFindings,
  planningGapLabel,
  previewCategories as buildPreviewCategories,
  previewFileSizeLabel,
  readFileText,
  readinessReportPayload,
  revertSuggestionInRows,
  routesForFinding,
  suggestionAuditEntries,
  suggestionForFinding,
  suggestionForQueueItem,
  suggestionKey,
  suggestionLabels,
  type AssignmentSuggestion,
  type PreflightRoute,
  type RemediationQueueItem,
} from '../../utils/export-workflow';

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

  const planningCompleteness = useMemo(() =>
    calculatePlanningCompleteness({ assignmentRows, resources }),
  [assignmentRows, resources]);

  const findings = useMemo(() => planningFindings(planningCompleteness), [planningCompleteness]);
  const blockingFindingCount = findings.reduce((total, [, count]) => total + count, 0);
  const preflightSummary = preflight?.summary;
  const visiblePreflightFindings = preflight?.findings.slice(0, 5) || [];
  const exportChecklist = buildExportChecklist({
    selectedProjectId,
    isDirty: state.isDirty,
    planningCompleteness,
    hasPreflight: !!preflight,
  });
  const exportChecklistComplete = exportChecklist.filter((item) => item.complete).length;
  const selectedPreviewFile = terraformPreview?.files.find((file) =>
    file.path === selectedPreviewPath,
  ) || terraformPreview?.files[0];
  const previewCategories = useMemo(() => {
    return buildPreviewCategories(terraformPreview?.files || []);
  }, [terraformPreview]);
  const filteredPreviewFiles = useMemo(() => {
    return filterPreviewFiles({
      files: terraformPreview?.files || [],
      category: previewCategory,
      search: previewSearch,
    });
  }, [previewCategory, previewSearch, terraformPreview]);
  const selectedPreviewSize = previewFileSizeLabel(selectedPreviewFile);
  const handoffCsvCount = handoffCsvFileCount(terraformPreview?.files || []);

  const assignmentSuggestions = useMemo(() => {
    return buildAssignmentSuggestions({ assignmentRows, resources });
  }, [assignmentRows, resources]);
  const highConfidenceSuggestions = assignmentSuggestions.filter((suggestion) => suggestion.confidence === 'High');
  const recentSuggestionAudit = suggestionAudit.slice(0, 6);
  const activeAuditCount = suggestionAudit.filter((entry) => !entry.revertedAt).length;
  const activeAssignmentGapCount = findings.reduce((total, [, count]) => total + count, 0);

  function applyAssignmentSuggestions(suggestions: AssignmentSuggestion[]) {
    if (suggestions.length === 0) return;
    dispatch({
      type: 'SET_ASSIGNMENT_ROWS',
      payload: applySuggestionsToRows(assignmentRows, suggestions),
    });
    dispatch({
      type: 'APPEND_SUGGESTION_AUDIT',
      payload: suggestionAuditEntries(suggestions, new Date().toISOString()),
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
      payload: revertSuggestionInRows(assignmentRows, entry),
    });
    dispatch({
      type: 'SET_SUGGESTION_AUDIT',
      payload: markSuggestionAuditReverted(suggestionAudit, entryId, new Date().toISOString()),
    });
    dispatch({
      type: 'SET_TERRAFORM_STATUS',
      payload: `Reverted suggested ${suggestionLabels[entry.field]} change for ${entry.vmName}. Save the project to persist it.`,
    });
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

  const remediationQueue: RemediationQueueItem[] = buildRemediationQueue({
    preflightFindings: preflight?.findings || [],
    assignmentRows,
    planningCompleteness,
  });
  const hasResolvableIssue = remediationQueue.length > 0;

  const queueSuggestionEntries = remediationQueue
    .map((item) => {
      const suggestion = suggestionForQueueItem({ item, assignmentRows, resources });
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
      downloadBrowserFile({
        blob,
        filename: `${projectName.replace(/\s+/g, '-')}-terraform-${new Date().toISOString().split('T')[0]}.zip`,
      });
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
    downloadBrowserFile({
      blob,
      filename: file.path.replace(/\//g, '__'),
    });
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: `Downloaded ${file.path}.` });
  }

  function handleDownloadReadinessReport() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    const generatedAt = new Date().toISOString();
    const report = readinessReportPayload({
      generatedAt,
      selectedProjectId,
      projectName,
      workbookFilename: summary?.filename,
      activeAssignmentGapCount,
      preflight,
      exportChecklist,
      findings,
      assignmentSuggestions,
      suggestionAudit,
    });
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    downloadBrowserFile({
      blob,
      filename: `${projectName.replace(/\s+/g, '-')}-carbon-export-readiness-${generatedAt.split('T')[0]}.json`,
    });
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
    downloadBrowserFile({
      blob,
      filename: `${projectName.replace(/\s+/g, '-')}-planning-state-${new Date().toISOString().split('T')[0]}.json`,
    });
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
              const suggestion = suggestionForQueueItem({ item, assignmentRows, resources });
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
                    const suggestion = suggestionForFinding({ finding, assignmentRows, resources });
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
                {filteredPreviewFiles.map((file) => {
                  const isSelected = file.path === selectedPreviewFile.path;
                  return (
                    <button
                      key={file.path}
                      className={`preview-file-row${isSelected ? ' preview-file-row--selected' : ''}`}
                      type="button"
                      aria-pressed={isSelected}
                      aria-label={`Preview ${file.path} (${file.category})${isSelected ? ', selected' : ''}`}
                      onClick={() => setSelectedPreviewPath(file.path)}
                    >
                      <span>{file.path}</span>
                      <small>{file.category}</small>
                    </button>
                  );
                })}
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
      <PackageParityStatus
        packageFileCount={packageFileCount}
        packageParitySummary={packageParitySummary}
        packageGroups={packageGroups}
      />
    </Layer>
  );
}

// Made with Bob
