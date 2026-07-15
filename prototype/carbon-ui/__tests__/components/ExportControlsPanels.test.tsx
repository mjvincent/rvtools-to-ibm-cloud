import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExportChecklistPanel from '../../components/workflows/export/ExportChecklistPanel';
import ExportReadinessHeader from '../../components/workflows/export/ExportReadinessHeader';
import PlanningGapSummary from '../../components/workflows/export/PlanningGapSummary';
import type { ExportChecklistItem } from '../../utils/export-workflow';

describe('ExportReadinessHeader', () => {
  it('renders export controls and routes actions', async () => {
    const planningStateInputRef = React.createRef<HTMLInputElement>();
    const props: React.ComponentProps<typeof ExportReadinessHeader> = {
      blockingFindingCount: 2,
      planningStateInputRef,
      runningPreflight: false,
      loadingPreview: false,
      generatingTerraform: false,
      hasResolvableIssue: true,
      hasSelectedProject: true,
      onResolveNextIssue: jest.fn(),
      onImportPlanningState: jest.fn(),
      onExportPlanningState: jest.fn(),
      onDownloadReadinessReport: jest.fn(),
      onRunPreflight: jest.fn(),
      onPreviewTerraform: jest.fn(),
      onDownloadTerraform: jest.fn(),
    };

    render(<ExportReadinessHeader {...props} />);

    expect(screen.getByText('Export readiness')).toBeTruthy();
    expect(screen.getByText('Needs review')).toBeTruthy();

    await userEvent.click(screen.getByText('Resolve next issue'));
    expect(props.onResolveNextIssue).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Export planning JSON'));
    expect(props.onExportPlanningState).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Download readiness report'));
    expect(props.onDownloadReadinessReport).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Run preflight'));
    expect(props.onRunPreflight).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Preview Terraform'));
    expect(props.onPreviewTerraform).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Download Terraform ZIP'));
    expect(props.onDownloadTerraform).toHaveBeenCalledTimes(1);

    const importInput = screen.getByLabelText('Import planning state JSON');
    const file = new File(['{}'], 'planning-state.json', { type: 'application/json' });
    fireEvent.change(importInput, { target: { files: [file] } });
    expect(props.onImportPlanningState).toHaveBeenCalledTimes(1);
  });

  it('disables backend actions when there is no selected project', () => {
    render(
      <ExportReadinessHeader
        blockingFindingCount={0}
        planningStateInputRef={React.createRef<HTMLInputElement>()}
        runningPreflight={false}
        loadingPreview={false}
        generatingTerraform={false}
        hasResolvableIssue={false}
        hasSelectedProject={false}
        onResolveNextIssue={jest.fn()}
        onImportPlanningState={jest.fn()}
        onExportPlanningState={jest.fn()}
        onDownloadReadinessReport={jest.fn()}
        onRunPreflight={jest.fn()}
        onPreviewTerraform={jest.fn()}
        onDownloadTerraform={jest.fn()}
      />,
    );

    expect(screen.getByText('Ready')).toBeTruthy();
    expect(screen.getByText('Resolve next issue').closest('button')?.disabled).toBe(true);
    expect(screen.getByText('Run preflight').closest('button')?.disabled).toBe(true);
    expect(screen.getByText('Preview Terraform').closest('button')?.disabled).toBe(true);
    expect(screen.getByText('Download Terraform ZIP').closest('button')?.disabled).toBe(true);
  });
});

describe('ExportChecklistPanel', () => {
  it('renders checklist completion state', () => {
    const checklist: ExportChecklistItem[] = [
      { label: 'Saved project', complete: true },
      { label: 'Package preflight', complete: false },
    ];

    render(<ExportChecklistPanel checklist={checklist} completeCount={1} />);

    expect(screen.getByText('Export checklist')).toBeTruthy();
    expect(screen.getByText('1/2 readiness item(s) complete before Terraform handoff.')).toBeTruthy();
    expect(screen.getByText('In progress')).toBeTruthy();
    expect(screen.getByText('Saved project')).toBeTruthy();
    expect(screen.getByText('Package preflight')).toBeTruthy();
    expect(screen.getByText('Complete')).toBeTruthy();
    expect(screen.getByText('Needs review')).toBeTruthy();
  });
});

describe('PlanningGapSummary', () => {
  it('renders ready and attention-needed planning gap counts', () => {
    render(
      <PlanningGapSummary
        findings={[
          ['Network assignment gaps', 0],
          ['Wave planning gaps', 3],
        ]}
      />,
    );

    expect(screen.getByText('Network assignment gaps')).toBeTruthy();
    expect(screen.getByText('Ready')).toBeTruthy();
    expect(screen.getByText('Wave planning gaps')).toBeTruthy();
    expect(screen.getByText('3 item(s) need attention')).toBeTruthy();
  });
});
