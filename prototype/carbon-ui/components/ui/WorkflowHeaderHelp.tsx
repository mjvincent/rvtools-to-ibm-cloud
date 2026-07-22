'use client';

import React from 'react';
import { Button, Modal } from '@carbon/react';
import { Help } from '@carbon/icons-react';
import type { Workflow } from '../../types/network-planning';
import { helpForWorkflow } from '../../utils/guided-help';

type WorkflowHeaderHelpProps = {
  workflow: Workflow;
};

function GuidanceList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export default function WorkflowHeaderHelp({ workflow }: WorkflowHeaderHelpProps) {
  const [open, setOpen] = React.useState(false);
  const help = helpForWorkflow(workflow);

  function openUserGuide() {
    window.open('/help/user-guide', '_blank', 'noopener,noreferrer');
  }

  return (
    <div className="workflow-header-help">
      <Button
        kind="ghost"
        size="sm"
        renderIcon={Help}
        aria-label={`Step help for ${help.title}`}
        onClick={() => setOpen(true)}
      >
        Step help
      </Button>
      <Modal
        open={open}
        modalHeading={`${help.title} step help`}
        primaryButtonText="Got it"
        secondaryButtonText="Close"
        onRequestClose={() => setOpen(false)}
        onRequestSubmit={() => setOpen(false)}
      >
        <div className="guided-help-modal">
          <p>{help.purpose}</p>
          <GuidanceList title="Before continuing" items={help.beforeContinuing} />
          <GuidanceList title="Complete when" items={help.completeWhen} />
          <GuidanceList title="Common mistakes" items={help.commonMistakes} />
          <section className="guided-help-modal__next">
            <h3>Recommended next step</h3>
            <p>{help.nextStep}</p>
          </section>
          <Button kind="ghost" size="sm" onClick={openUserGuide}>
            Open full user guide in a new window
          </Button>
        </div>
      </Modal>
    </div>
  );
}
