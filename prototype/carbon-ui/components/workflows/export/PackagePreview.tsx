'use client';

import React from 'react';
import { Button, Search, Select, SelectItem, Tag } from '@carbon/react';
import { Close, Download } from '@carbon/icons-react';
import type { TerraformPreviewFile } from '../../../hooks/useApi';

type PackagePreviewProps = {
  fileCount: number;
  selectedFile: TerraformPreviewFile;
  selectedFileSize: string;
  previewSearch: string;
  previewCategory: string;
  previewCategories: string[];
  filteredPreviewFiles: TerraformPreviewFile[];
  handoffCsvCount: number;
  onSearchChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onSelectFile: (path: string) => void;
  onShowHandoffCsvs: () => void;
  onDownloadSelected: (file: TerraformPreviewFile) => void;
  onClosePreview: () => void;
};

export default function PackagePreview({
  fileCount,
  selectedFile,
  selectedFileSize,
  previewSearch,
  previewCategory,
  previewCategories,
  filteredPreviewFiles,
  handoffCsvCount,
  onSearchChange,
  onCategoryChange,
  onSelectFile,
  onShowHandoffCsvs,
  onDownloadSelected,
  onClosePreview,
}: PackagePreviewProps) {
  return (
    <div className="export-package">
      <div className="section-header compact">
        <div>
          <h2>Package preview</h2>
          <p>{fileCount} generated file(s) from the saved Carbon network plan.</p>
        </div>
        <div className="network-actions">
          <Tag type="blue">{selectedFile.category}</Tag>
          <Tag type="gray">{selectedFileSize}</Tag>
          <Button
            kind="tertiary"
            size="sm"
            renderIcon={Download}
            onClick={onShowHandoffCsvs}
          >
            Show handoff CSVs
          </Button>
          <Button
            kind="secondary"
            size="sm"
            renderIcon={Download}
            onClick={() => onDownloadSelected(selectedFile)}
          >
            Download selected
          </Button>
          <Button
            kind="tertiary"
            size="sm"
            renderIcon={Close}
            onClick={onClosePreview}
          >
            Close preview
          </Button>
        </div>
      </div>
      <div className="preview-browser">
        <div className="preview-browser__sidebar">
          <Search
            id="terraform-preview-search"
            labelText="Search package files"
            placeholder="Search file path"
            value={previewSearch}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              onSearchChange(event.target.value)
            }
          />
          <Select
            id="terraform-preview-category"
            labelText="Package section"
            value={previewCategory}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              onCategoryChange(event.target.value)
            }
          >
            {previewCategories.map((category) => (
              <SelectItem key={category} value={category} text={category} />
            ))}
          </Select>
          <div className="preview-file-list" aria-label="Package preview files">
            {filteredPreviewFiles.map((file) => {
              const isSelected = file.path === selectedFile.path;
              return (
                <button
                  key={file.path}
                  className={`preview-file-row${isSelected ? ' preview-file-row--selected' : ''}`}
                  type="button"
                  aria-pressed={isSelected}
                  aria-label={`Preview ${file.path} (${file.category})${isSelected ? ', selected' : ''}`}
                  onClick={() => onSelectFile(file.path)}
                >
                  <span>{file.path}</span>
                  <small>{file.category}</small>
                </button>
              );
            })}
            {filteredPreviewFiles.length === 0 && (
              <p className="preview-empty">No package files match this filter.</p>
            )}
          </div>
        </div>
        <div className="preview-browser__content">
          <div className="preview-file-header">
            <div>
              <strong>{selectedFile.path}</strong>
              <span>{selectedFileSize}</span>
            </div>
            <Tag type="blue">{handoffCsvCount} handoff CSVs</Tag>
          </div>
          <pre className="terraform-preview" aria-label={`Terraform preview ${selectedFile.path}`}>
            <code>{selectedFile.content}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
