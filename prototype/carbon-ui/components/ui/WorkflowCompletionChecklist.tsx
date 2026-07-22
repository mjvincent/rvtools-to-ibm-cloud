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
    <aside className="workflow-completion-checklist" aria-labelledby={`${workflow}-completion-title`}>
      <h3 id={`${workflow}-completion-title`}>Complete when</h3>
      <ul>
        {help.completeWhen.map((item) => (
          <li key={item}>
            <Checkmark size={16} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
