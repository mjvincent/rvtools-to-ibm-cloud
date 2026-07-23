'use client';

import React from 'react';
import { Tag, Tile } from '@carbon/react';

type CarbonTagType = 'red' | 'green' | 'blue' | 'purple' | 'gray' | 'warm-gray' | 'cyan';

export type ProjectSaveGuidanceInput = {
  persistenceEnabled: boolean;
  selectedProjectId: string;
  isDirty: boolean;
  autoSaveStatus: string;
  autoSaveError: string;
  projectError: string;
  apiStatus: string;
};

export type ProjectSaveGuidanceContent = {
  tagType: CarbonTagType;
  label: string;
  headline: string;
  detail: string;
  bullets: string[];
};

const retainedOutsideProject = [
  'Keep the original RVTools workbook; project save stores planning state, not the workbook as the system of record.',
  'Download and retain Terraform ZIPs and readiness reports after they are generated.',
];

export function buildProjectSaveGuidance(input: ProjectSaveGuidanceInput): ProjectSaveGuidanceContent {
  if (!input.persistenceEnabled || input.apiStatus === 'API unavailable') {
    return {
      tagType: 'red',
      label: 'Persistence unavailable',
      headline: 'Treat this session as temporary.',
      detail: 'Save/load and autosave need the FastAPI/Postgres prototype stack.',
      bullets: [
        'Do not refresh or close the browser until persistence is restored or you have exported needed files.',
        ...retainedOutsideProject,
      ],
    };
  }

  if (input.autoSaveError || input.projectError) {
    return {
      tagType: 'red',
      label: 'Save attention needed',
      headline: 'Review the save error before continuing.',
      detail: input.autoSaveError || input.projectError,
      bullets: [
        'Retry save after checking the API and database service.',
        'Current browser-side planning state is still present until you refresh or close the page.',
        ...retainedOutsideProject,
      ],
    };
  }

  if (!input.selectedProjectId) {
    return {
      tagType: 'warm-gray',
      label: 'Not saved yet',
      headline: 'Create or load a project before relying on resume.',
      detail: 'Edits are currently browser-side until a project is saved.',
      bullets: [
        'Use Save project after loading a workbook or importing planning state.',
        'Refresh, browser close, or switching machines can lose unsaved browser work.',
        ...retainedOutsideProject,
      ],
    };
  }

  if (input.isDirty) {
    return {
      tagType: 'warm-gray',
      label: 'Unsaved changes',
      headline: 'Autosave is queued for this saved project.',
      detail: input.autoSaveStatus || 'Recent planning edits are waiting to persist.',
      bullets: [
        'Wait for the saved status or use Save project before closing the browser.',
        'Saved projects restore planning state from Postgres for this prototype.',
        ...retainedOutsideProject,
      ],
    };
  }

  if (input.autoSaveStatus) {
    return {
      tagType: 'green',
      label: 'Project current',
      headline: 'Planning state is saved to Postgres.',
      detail: input.autoSaveStatus,
      bullets: [
        'You can resume saved planning state from the Saved project selector.',
        ...retainedOutsideProject,
      ],
    };
  }

  return {
    tagType: 'gray',
    label: 'Ready to save',
    headline: 'No saved changes have been recorded yet.',
    detail: 'Start planning, then save the project before closing or refreshing.',
    bullets: [
      'Saved projects persist planning state after the first successful save.',
      ...retainedOutsideProject,
    ],
  };
}

type ProjectSaveGuidanceProps = ProjectSaveGuidanceInput;

export default function ProjectSaveGuidance(props: ProjectSaveGuidanceProps) {
  const guidance = buildProjectSaveGuidance(props);

  return (
    <Tile className="project-save-guidance" aria-label="Project save guidance">
      <div className="project-save-guidance__header">
        <Tag type={guidance.tagType}>{guidance.label}</Tag>
        <h2>{guidance.headline}</h2>
      </div>
      <p>{guidance.detail}</p>
      <ul>
        {guidance.bullets.map((bullet) => (
          <li key={bullet}>{bullet}</li>
        ))}
      </ul>
    </Tile>
  );
}
