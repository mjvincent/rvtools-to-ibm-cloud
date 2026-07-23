import React from 'react';
import { render, screen } from '@testing-library/react';
import ExportHandoffGuide, {
  buildExportModeGuide,
  buildHandoffFileGuide,
} from '../../components/workflows/export/ExportHandoffGuide';

describe('buildExportModeGuide', () => {
  it('explains the export controls and owners', () => {
    const guide = buildExportModeGuide();

    expect(guide.map((item) => item.label)).toEqual([
      'Preflight review',
      'Generated package preview',
      'Readiness report',
      'Terraform ZIP handoff',
    ]);
    expect(guide.find((item) => item.label === 'Terraform ZIP handoff')).toMatchObject({
      owner: 'Terraform operator',
    });
  });
});

describe('buildHandoffFileGuide', () => {
  it('explains key generated files and handoff owners', () => {
    const guide = buildHandoffFileGuide();

    expect(guide.map((item) => item.path)).toEqual([
      'README.md',
      'network-plan.json',
      'decision-audit.csv',
      'vm-mapping.csv',
      'cutover-readiness.csv',
      'terraform.tfvars.example',
    ]);
    expect(guide.find((item) => item.path === 'terraform.tfvars.example')).toMatchObject({
      owner: 'Terraform operator',
    });
    expect(guide.find((item) => item.path === 'cutover-readiness.csv')?.purpose).toContain('cutover');
  });
});

describe('ExportHandoffGuide', () => {
  it('renders export handoff guidance and tool boundary', () => {
    render(<ExportHandoffGuide />);

    expect(screen.getByLabelText('Export handoff guidance')).toBeTruthy();
    expect(screen.getByText('Handoff guidance')).toBeTruthy();
    expect(screen.getByText('Preflight review')).toBeTruthy();
    expect(screen.getByText('File: terraform.tfvars.example')).toBeTruthy();
    expect(screen.getByText(/Terraform execution/)).toBeTruthy();
    expect(screen.getByText(/outside the Carbon UI/)).toBeTruthy();
  });
});
