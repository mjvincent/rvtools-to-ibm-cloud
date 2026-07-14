'use client';

import React from 'react';
import { Tag, Tile } from '@carbon/react';

type PackageParitySummaryItem = {
  label: string;
  value: string;
  detail: string;
  tag: string;
  tagType: 'green' | 'blue' | 'purple' | 'gray' | 'warm-gray' | 'red' | 'cyan';
};

type PackageGroup = {
  title: string;
  status: string;
  tagType: 'green' | 'blue' | 'purple' | 'gray' | 'warm-gray' | 'red' | 'cyan';
  files: string[];
};

type PackageParityStatusProps = {
  packageFileCount: number;
  packageParitySummary: PackageParitySummaryItem[];
  packageGroups: PackageGroup[];
};

export default function PackageParityStatus({
  packageFileCount,
  packageParitySummary,
  packageGroups,
}: PackageParityStatusProps) {
  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Package parity status</h2>
          <p>{packageFileCount} files are included in the generated ZIP.</p>
        </div>
        <Tag type="green">Streamlit handoff set covered</Tag>
      </div>
      <div className="package-parity-grid">
        {packageParitySummary.map((item) => (
          <Tile key={item.label} className="package-parity-tile">
            <div>
              <h3>{item.label}</h3>
              <p>{item.detail}</p>
            </div>
            <div className="package-parity-tile__status">
              <strong>{item.value}</strong>
              <Tag type={item.tagType}>{item.tag}</Tag>
            </div>
          </Tile>
        ))}
      </div>
      <div className="package-grid">
        {packageGroups.map((group) => (
          <Tile key={group.title} className="package-tile">
            <div className="package-tile__header">
              <h3>{group.title}</h3>
              <Tag type={group.tagType}>{group.status}</Tag>
            </div>
            <p>{group.files.length} file(s)</p>
            <ul>
              {group.files.map((file) => (
                <li key={file}>{file}</li>
              ))}
            </ul>
          </Tile>
        ))}
      </div>
    </div>
  );
}
