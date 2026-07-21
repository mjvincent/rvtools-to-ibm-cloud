'use client';

import React from 'react';
import { Button, Tag } from '@carbon/react';
import type { Workflow } from '../../types/network-planning';
import type { WorkflowProgressStep } from '../../utils/workflow-progress';
import { findNextWorkflowStep } from '../../utils/workflow-progress';

type WorkflowProgressGuideProps = {
  steps: WorkflowProgressStep[];
  activeWorkflow: Workflow;
  onSelectWorkflow: (workflow: Workflow) => void;
};

const tagTypeByStatus: Record<WorkflowProgressStep['status'], 'gray' | 'blue' | 'green' | 'red'> = {
  'Not started': 'gray',
  'Needs attention': 'red',
  Ready: 'blue',
  Complete: 'green',
};

export default function WorkflowProgressGuide({
  steps,
  activeWorkflow,
  onSelectWorkflow,
}: WorkflowProgressGuideProps) {
  const nextStep = findNextWorkflowStep(steps);

  return (
    <section className="workflow-progress-guide" aria-labelledby="workflow-progress-title">
      <div className="workflow-progress-guide__header">
        <div>
          <p className="eyebrow">Migration workflow</p>
          <h2 id="workflow-progress-title">Progress guide</h2>
          <p>
            Follow the readiness path from workbook intake through Terraform package handoff.
          </p>
        </div>
        <div className="workflow-progress-guide__next">
          <span>Next recommended action</span>
          <strong>{nextStep.nextAction}</strong>
          <Button
            kind="tertiary"
            size="sm"
            onClick={() => onSelectWorkflow(nextStep.workflow)}
          >
            Open {nextStep.label}
          </Button>
        </div>
      </div>

      <ol className="workflow-progress-guide__steps">
        {steps.map((step, index) => (
          <li
            key={step.workflow}
            className={step.workflow === activeWorkflow ? 'workflow-progress-step workflow-progress-step--active' : 'workflow-progress-step'}
          >
            <div className="workflow-progress-step__index" aria-hidden="true">
              {index + 1}
            </div>
            <div className="workflow-progress-step__body">
              <div className="workflow-progress-step__title">
                <button type="button" onClick={() => onSelectWorkflow(step.workflow)}>
                  {step.label}
                </button>
                <Tag type={tagTypeByStatus[step.status]}>{step.status}</Tag>
              </div>
              <p>{step.reason}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
