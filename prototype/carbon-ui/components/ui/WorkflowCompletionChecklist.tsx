'use client';

import React from 'react';
import { Checkmark } from '@carbon/icons-react';
import type { Workflow } from '../../types/network-planning';
import { helpForWorkflow } from '../../utils/guided-help';

type WorkflowCompletionChecklistProps = {
  workflow: Workflow;
};

export default function WorkflowCompletionChecklist({ workflow }: WorkflowCompletionChecklistProps) {
  const help = helpForWorkflow(workflow);

  return (
    <details className="workflow-completion-checklist" open>
      <summary id={`${workflow}-completion-title`}>
        <span>Complete when</span>
        <span className="workflow-completion-checklist__count">{help.completeWhen.length} items</span>
      </summary>
      <ul>
        {help.completeWhen.map((item) => (
          <li key={item}>
            <Checkmark size={16} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </details>
  );
}
