'use client';

import React from 'react';
import { Button, Tag } from '@carbon/react';
import { CloudUpload, Download, Renew, View } from '@carbon/icons-react';
import WorkflowHeaderHelp from '../../ui/WorkflowHeaderHelp';

type ExportReadinessHeaderProps = {
  blockingFindingCount: number;
  planningStateInputRef: React.RefObject<HTMLInputElement | null>;
  runningPreflight: boolean;
  loadingPreview: boolean;
  generatingTerraform: boolean;
  hasResolvableIssue: boolean;
  hasSelectedProject: boolean;
  onResolveNextIssue: () => void;
  onImportPlanningState: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onExportPlanningState: () => void;
  onDownloadReadinessReport: () => void;
  onRunPreflight: () => void;
  onPreviewTerraform: () => void;
  onDownloadTerraform: () => void;
};

export default function ExportReadinessHeader({
  blockingFindingCount,
  planningStateInputRef,
  runningPreflight,
  loadingPreview,
  generatingTerraform,
  hasResolvableIssue,
  hasSelectedProject,
  onResolveNextIssue,
  onImportPlanningState,
  onExportPlanningState,
  onDownloadReadinessReport,
  onRunPreflight,
  onPreviewTerraform,
  onDownloadTerraform,
}: ExportReadinessHeaderProps) {
  return (
    <div className="section-header">
      <div>
        <h2>Export readiness</h2>
        <p>Review planning gaps, then save the latest Carbon network plan and download a Terraform ZIP from FastAPI.</p>
      </div>
      <div className="network-actions">
        <WorkflowHeaderHelp workflow="export" />
        <Tag type={blockingFindingCount === 0 ? 'green' : 'warm-gray'}>
          {blockingFindingCount === 0 ? 'Ready' : 'Needs review'}
        </Tag>
        <Button
          kind="tertiary"
          size="sm"
          renderIcon={Renew}
          disabled={!hasResolvableIssue}
          onClick={onResolveNextIssue}
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
          onChange={onImportPlanningState}
        />
        <Button
          kind="secondary"
          size="sm"
          renderIcon={Download}
          onClick={onExportPlanningState}
        >
          Export planning JSON
        </Button>
        <Button
          kind="secondary"
          size="sm"
          renderIcon={Download}
          onClick={onDownloadReadinessReport}
        >
          Download readiness report
        </Button>
        <Button
          kind="secondary"
          size="sm"
          renderIcon={Renew}
          onClick={onRunPreflight}
          disabled={!hasSelectedProject || runningPreflight}
        >
          {runningPreflight ? 'Running...' : 'Run preflight'}
        </Button>
        <Button
          kind="secondary"
          size="sm"
          renderIcon={View}
          onClick={onPreviewTerraform}
          disabled={!hasSelectedProject || loadingPreview}
        >
          {loadingPreview ? 'Previewing...' : 'Preview Terraform'}
        </Button>
        <Button
          kind="primary"
          size="sm"
          renderIcon={Download}
          onClick={onDownloadTerraform}
          disabled={!hasSelectedProject || generatingTerraform}
        >
          {generatingTerraform ? 'Generating...' : 'Download Terraform ZIP'}
        </Button>
      </div>
    </div>
  );
}
