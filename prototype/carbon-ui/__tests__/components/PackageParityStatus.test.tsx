import React from 'react';
import { render, screen } from '@testing-library/react';
import PackageParityStatus from '../../components/workflows/export/PackageParityStatus';
import {
  packageGroups,
  packageParitySummary,
} from '../../utils/export-workflow';
import { packageFileCount } from '../../utils/package-inventory';

describe('PackageParityStatus', () => {
  it('renders package inventory and parity groups', () => {
    render(
      <PackageParityStatus
        packageFileCount={packageFileCount}
        packageParitySummary={packageParitySummary}
        packageGroups={packageGroups}
      />,
    );

    expect(screen.getByText('Package parity status')).toBeTruthy();
    expect(screen.getByText(`${packageFileCount} files are included in the generated ZIP.`)).toBeTruthy();
    expect(screen.getByText('Streamlit handoff set covered')).toBeTruthy();
    expect(screen.getByText('Handoff parity')).toBeTruthy();
    expect(screen.getByText('Terraform layout')).toBeTruthy();
    expect(screen.getByText('Carbon additions')).toBeTruthy();
    expect(screen.getByText('Terraform project')).toBeTruthy();
    expect(screen.getByText('Migration handoff')).toBeTruthy();
    expect(screen.getByText('Carbon state')).toBeTruthy();
  });
});
