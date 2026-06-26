'use client';

import React, { useMemo } from 'react';
import { Button, InlineNotification, Layer, Tag, Tile } from '@carbon/react';
import { Download } from '@carbon/icons-react';
import { useAppState } from '../../store/AppContext';
import { generateTerraform, saveNetworkPlan } from '../../hooks/useApi';
import { buildNetworkPlanBody } from '../../utils/planning-state';

function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

export default function ExportWorkflow() {
  const { state, dispatch } = useAppState();
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

  async function handleDownloadTerraform() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    dispatch({ type: 'SET_GENERATING_TERRAFORM', payload: true });
    try {
      if (!selectedProjectId) throw new Error('Save or load a persisted project before exporting Terraform.');
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Saving latest network plan...' });
      await saveNetworkPlan(
        selectedProjectId,
        buildNetworkPlanBody({ resources, assignmentRows, projectName, summary }),
      );
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
    </Layer>
  );
}

// Made with Bob
