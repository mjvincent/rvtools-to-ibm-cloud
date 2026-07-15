import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PackagePreview from '../../components/workflows/export/PackagePreview';
import type { TerraformPreviewFile } from '../../hooks/useApi';

const files: TerraformPreviewFile[] = [
  {
    path: 'README.md',
    category: 'Terraform',
    size_bytes: 35,
    content: '# Terraform Package',
  },
  {
    path: 'decision-audit.csv',
    category: 'Migration handoff',
    size_bytes: 48,
    content: 'VM Name,Chosen Profile\napp-01,bx2-2x8\n',
  },
];

function renderPreview(overrides: Partial<React.ComponentProps<typeof PackagePreview>> = {}) {
  const props: React.ComponentProps<typeof PackagePreview> = {
    fileCount: files.length,
    selectedFile: files[0],
    selectedFileSize: '1 KB',
    previewSearch: '',
    previewCategory: 'All',
    previewCategories: ['All', 'Terraform', 'Migration handoff'],
    filteredPreviewFiles: files,
    handoffCsvCount: 1,
    onSearchChange: jest.fn(),
    onCategoryChange: jest.fn(),
    onSelectFile: jest.fn(),
    onShowHandoffCsvs: jest.fn(),
    onDownloadSelected: jest.fn(),
    onClosePreview: jest.fn(),
    ...overrides,
  };
  render(<PackagePreview {...props} />);
  return props;
}

describe('PackagePreview', () => {
  it('renders preview metadata and selected file content', () => {
    renderPreview();

    expect(screen.getByText('Package preview')).toBeTruthy();
    expect(screen.getByText('2 generated file(s) from the saved Carbon network plan.')).toBeTruthy();
    expect(screen.getAllByText('README.md').length).toBeGreaterThan(0);
    expect(screen.getByText('decision-audit.csv')).toBeTruthy();
    expect(screen.getByLabelText('Terraform preview README.md').textContent).toContain('# Terraform Package');
    expect(screen.getByText('1 handoff CSVs')).toBeTruthy();
  });

  it('routes search, category, file selection, download, and close actions', async () => {
    const props = renderPreview();

    fireEvent.change(screen.getByLabelText('Search package files'), {
      target: { value: 'audit' },
    });
    expect(props.onSearchChange).toHaveBeenCalledWith('audit');

    await userEvent.selectOptions(screen.getByLabelText('Package section'), 'Migration handoff');
    expect(props.onCategoryChange).toHaveBeenCalledWith('Migration handoff');

    await userEvent.click(screen.getByRole('button', { name: 'Preview decision-audit.csv (Migration handoff)' }));
    expect(props.onSelectFile).toHaveBeenCalledWith('decision-audit.csv');

    await userEvent.click(screen.getByText('Show handoff CSVs'));
    expect(props.onShowHandoffCsvs).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByText('Download selected'));
    expect(props.onDownloadSelected).toHaveBeenCalledWith(files[0]);

    await userEvent.click(screen.getByText('Close preview'));
    expect(props.onClosePreview).toHaveBeenCalledTimes(1);
  });

  it('shows an empty state when filters hide all files', () => {
    renderPreview({ filteredPreviewFiles: [] });

    expect(screen.getByText('No package files match this filter.')).toBeTruthy();
  });
});
