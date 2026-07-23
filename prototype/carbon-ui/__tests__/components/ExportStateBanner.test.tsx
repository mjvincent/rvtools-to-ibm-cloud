import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ExportStateBanner, { buildExportStateBanner } from '../../components/workflows/export/ExportStateBanner';
import type { ExportResolutionStep } from '../../components/workflows/export/ExportResolutionOrder';

function stepsWithNext(label: string, detail = 'Review this export readiness step.'): ExportResolutionStep[] {
  return [
    {
      label,
      detail,
      status: 'Next',
      tagType: 'blue',
    },
  ];
}

describe('buildExportStateBanner', () => {
  it.each([
    ['Save or load project', 'Needs save', 'Review saved project controls'],
    ['Resolve planning gaps', 'Planning gaps', 'Go to next issue'],
    ['Run package preflight', 'Ready for preflight', 'Start package preflight'],
    ['Resolve preflight blockers', 'Blockers remain', 'Go to next issue'],
    ['Preview package files', 'Ready to preview', 'Open package preview'],
    ['Download handoff artifacts', 'Ready to download', 'Download readiness report'],
  ])('maps %s to %s', (stepLabel, expectedState, expectedAction) => {
    const banner = buildExportStateBanner(stepsWithNext(stepLabel));

    expect(banner).toMatchObject({
      state: expectedState,
      nextAction: expectedAction,
      detail: 'Review this export readiness step.',
    });
  });

  it('falls back when no resolution steps exist', () => {
    expect(buildExportStateBanner([])).toMatchObject({
      state: 'Needs review',
      nextAction: 'Review export readiness',
    });
  });
});

describe('ExportStateBanner', () => {
  it('renders the current export state and action', () => {
    const onNextAction = jest.fn();

    render(
      <ExportStateBanner
        model={{
          state: 'Ready to preview',
          detail: 'Preview generated files before sharing the handoff.',
          nextAction: 'Open package preview',
          tagType: 'blue',
        }}
        onNextAction={onNextAction}
      />,
    );

    expect(screen.getByLabelText('Current export state')).toBeTruthy();
    expect(screen.getByText('Ready to preview')).toBeTruthy();
    expect(screen.getByText('Preview generated files before sharing the handoff.')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Open package preview' }));

    expect(onNextAction).toHaveBeenCalledTimes(1);
  });

  it('omits the action button when no action handler is provided', () => {
    render(
      <ExportStateBanner
        model={{
          state: 'Needs save',
          detail: 'Backend preflight, preview, and ZIP download need a persisted Carbon project.',
          nextAction: 'Review saved project controls',
          tagType: 'warm-gray',
        }}
      />,
    );

    expect(screen.getByText('Needs save')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Review saved project controls' })).toBeNull();
  });
});
