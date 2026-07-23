'use client';

import React from 'react';
import { Tag, Tile } from '@carbon/react';

export type ExportModeGuide = {
  label: string;
  purpose: string;
  owner: string;
};

export type HandoffFileGuide = {
  path: string;
  purpose: string;
  owner: string;
};

export function buildExportModeGuide(): ExportModeGuide[] {
  return [
    {
      label: 'Preflight review',
      purpose: 'Checks whether the saved Carbon network plan is safe enough to package.',
      owner: 'Migration planner',
    },
    {
      label: 'Generated package preview',
      purpose: 'Lets reviewers inspect generated Terraform, handoff CSVs, and Carbon state before downloading a ZIP.',
      owner: 'Migration planner and Terraform operator',
    },
    {
      label: 'Readiness report',
      purpose: 'Captures checklist status, planning gaps, preflight findings, and suggestion audit evidence for review meetings.',
      owner: 'Migration lead',
    },
    {
      label: 'Terraform ZIP handoff',
      purpose: 'Packages the Terraform project and migration handoff files for operator review and execution outside the app.',
      owner: 'Terraform operator',
    },
  ];
}

export function buildHandoffFileGuide(): HandoffFileGuide[] {
  return [
    {
      path: 'README.md',
      purpose: 'Operator instructions for reviewing, validating, and planning the Terraform package.',
      owner: 'Terraform operator',
    },
    {
      path: 'network-plan.json',
      purpose: 'Saved Carbon network planning state used to render and audit the package.',
      owner: 'Migration planner',
    },
    {
      path: 'decision-audit.csv',
      purpose: 'Records assignment, sizing, override, and suggestion decisions for governance review.',
      owner: 'Migration lead',
    },
    {
      path: 'vm-mapping.csv',
      purpose: 'Maps source VMs to target profiles, networks, storage, scope, and planning metadata.',
      owner: 'Migration planner',
    },
    {
      path: 'cutover-readiness.csv',
      purpose: 'Summarizes per-VM blockers and readiness for wave and cutover review.',
      owner: 'Cutover lead',
    },
    {
      path: 'terraform.tfvars.example',
      purpose: 'Shows operator-owned Terraform variable inputs that must be reviewed before plan/apply.',
      owner: 'Terraform operator',
    },
  ];
}

export default function ExportHandoffGuide() {
  const modeGuide = buildExportModeGuide();
  const fileGuide = buildHandoffFileGuide();

  return (
    <Tile className="export-handoff-guide" aria-label="Export handoff guidance">
      <div className="section-header compact">
        <div>
          <h2>Handoff guidance</h2>
          <p>Understand what the Export controls create before handing Terraform to an operator.</p>
        </div>
        <Tag type="cyan">Operator handoff</Tag>
      </div>

      <div className="export-handoff-grid">
        {modeGuide.map((item) => (
          <div className="export-handoff-card" key={item.label}>
            <h3>{item.label}</h3>
            <p>{item.purpose}</p>
            <Tag type="gray">{item.owner}</Tag>
          </div>
        ))}
      </div>

      <div className="export-file-guide">
        <h3>Key generated files</h3>
        <div className="export-file-guide__table">
          {fileGuide.map((file) => (
            <React.Fragment key={file.path}>
              <strong>{`File: ${file.path}`}</strong>
              <span>{file.purpose}</span>
              <Tag type="warm-gray">{file.owner}</Tag>
            </React.Fragment>
          ))}
        </div>
      </div>

      <p className="export-handoff-boundary">
        The app generates and explains Terraform handoff files. Terraform execution,
        IBM Cloud credentials, image imports, and cutover remain operator-owned work
        outside the Carbon UI.
      </p>
    </Tile>
  );
}
