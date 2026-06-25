'use client';

import React from 'react';
import { Tag } from '@carbon/react';

type ReadinessTagProps = {
  status: 'Blocked' | 'Review' | 'Ready' | string;
};

function tagType(status: string): string {
  if (status === 'Blocked') return 'red';
  if (status === 'Review') return 'yellow';
  if (status === 'Ready') return 'green';
  return 'gray';
}

export default function ReadinessTag({ status }: ReadinessTagProps) {
  // Cast to any because Carbon's Tag `type` prop union doesn't include all string returns
  return <Tag type={tagType(status) as any}>{status || 'Unknown'}</Tag>;
}

// Made with Bob
