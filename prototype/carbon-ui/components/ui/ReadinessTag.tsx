'use client';

import React from 'react';
import { Tag } from '@carbon/react';

type ReadinessTagProps = {
  status: 'Blocked' | 'Review' | 'Ready' | string;
  area?: 'Image' | 'Migration' | 'Memory' | 'Network';
  reason?: string;
  vmName?: string;
  onAction?: () => void;
};

function tagType(status: string): string {
  if (status === 'Blocked') return 'red';
  if (status === 'Review') return 'yellow';
  if (status === 'Ready') return 'green';
  return 'gray';
}

function areaCode(area?: ReadinessTagProps['area']) {
  if (area === 'Image') return 'IMG';
  if (area === 'Migration') return 'MIG';
  if (area === 'Memory') return 'MEM';
  if (area === 'Network') return 'NET';
  return '';
}

export function readinessAriaLabel({
  area,
  status,
  reason,
  vmName,
}: Pick<ReadinessTagProps, 'area' | 'status' | 'reason' | 'vmName'>) {
  const normalizedStatus = status || 'Unknown';
  const subject = area ? `${area} readiness` : 'Readiness';
  const vmSuffix = vmName ? ` for ${vmName}` : '';
  const reasonSuffix = reason ? `. ${reason}` : '';
  return `${subject}${vmSuffix}: ${normalizedStatus}${reasonSuffix}`;
}

export default function ReadinessTag({
  status,
  area,
  reason,
  vmName,
  onAction,
}: ReadinessTagProps) {
  // Cast to any because Carbon's Tag `type` prop union doesn't include all string returns
  const label = [areaCode(area), status || 'Unknown'].filter(Boolean).join(' ');
  const ariaLabel = readinessAriaLabel({ area, status, reason, vmName });
  const tag = <Tag type={tagType(status) as any}>{label}</Tag>;

  if (!onAction || status === 'Ready') {
    return (
      <span className="readiness-chip" title={ariaLabel} aria-label={ariaLabel}>
        {tag}
      </span>
    );
  }

  return (
    <button
      type="button"
      className="readiness-chip readiness-chip--action"
      title={`${ariaLabel}. Open review workflow.`}
      aria-label={`${ariaLabel}. Open review workflow.`}
      onClick={onAction}
    >
      {tag}
    </button>
  );
}

// Made with Bob
