'use client';

import React, { useMemo } from 'react';
import { Layer, Tag, Tile } from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import WorkflowCompletionChecklist from '../ui/WorkflowCompletionChecklist';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';

function terraformLabel(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'new_resource';
}

export default function OverviewWorkflow() {
  const { state } = useAppState();
  const { summary, assignmentRows, resources } = state;

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

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Planning overview</h2>
          <p>Carbon is tracking target architecture intent while Streamlit remains the supported Terraform ZIP path.</p>
        </div>
        <div className="workflow-header-actions">
          <WorkflowHeaderHelp workflow="overview" />
          <Tag type="purple">Prototype planner</Tag>
        </div>
      </div>
      <WorkflowCompletionChecklist workflow="overview" />
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

// Made with Bob
