'use client';

import React from 'react';
import { Button, Modal, Tag } from '@carbon/react';
import { Help } from '@carbon/icons-react';
import type { Workflow } from '../../types/network-planning';
import { helpForWorkflow } from '../../utils/guided-help';

type GuidedHelpProps = {
  workflow: Workflow;
  label: string;
};

function HelpList({ title, items }: { title: string; items: string[] }) {
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

export default function GuidedHelp({ workflow, label }: GuidedHelpProps) {
  const [open, setOpen] = React.useState(false);
  const help = helpForWorkflow(workflow);

  function openUserGuide() {
    window.open('/help/user-guide', '_blank', 'noopener,noreferrer');
  }

  return (
    <div className="guided-help-actions" aria-label="Workflow help">
      <Button
        kind="ghost"
        size="sm"
        renderIcon={Help}
        aria-label={`Help for ${label}`}
        onClick={() => setOpen(true)}
      >
        Help
      </Button>
      <Button
        kind="tertiary"
        size="sm"
        onClick={openUserGuide}
      >
        Open user guide
      </Button>
      <Modal
        open={open}
        modalHeading={`${help.title} help`}
        primaryButtonText="Got it"
        secondaryButtonText="Close"
        onRequestClose={() => setOpen(false)}
        onRequestSubmit={() => setOpen(false)}
      >
        <div className="guided-help-modal">
          <Tag type="blue">Current step</Tag>
          <p>{help.purpose}</p>
          <HelpList title="Before continuing" items={help.beforeContinuing} />
          <HelpList title="Complete when" items={help.completeWhen} />
          <HelpList title="Common mistakes" items={help.commonMistakes} />
          <section>
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
