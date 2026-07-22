'use client';

import React, { useMemo } from 'react';
import {
  FileUploaderDropContainer,
  InlineNotification,
  Layer,
  Select,
  SelectItem,
  Tag,
  TextArea,
  TextInput,
  Tile,
} from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';
import type {
  AssignmentVm,
  ImageImportRow,
  ImageImportStatus,
  ImageImportStatusValue,
} from '../../types/network-planning';

export const imageImportStatusOptions: ImageImportStatusValue[] = [
  '',
  'Pending',
  'Scheduled',
  'Imported',
  'Failed',
  'Review',
];

function sourceImageForRow(row: AssignmentVm) {
  return row.originalSpecs || row.imageReasons || row.profile || row.name;
}

export function buildImageImportRows(
  rows: AssignmentVm[],
  imageImportStatus: ImageImportStatus,
): ImageImportRow[] {
  const groups = new Map<string, { vms: AssignmentVm[]; owners: Set<string> }>();
  rows.forEach((row) => {
    const sourceImage = sourceImageForRow(row);
    const entry = groups.get(sourceImage) || { vms: [], owners: new Set<string>() };
    entry.vms.push(row);
    if (row.owner) entry.owners.add(row.owner);
    groups.set(sourceImage, entry);
  });

  return [...groups.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([sourceImage, group]) => {
    const state = imageImportStatus[sourceImage];
    return {
      sourceImage,
      vmCount: group.vms.length,
      owners: [...group.owners].sort().join('; '),
      targetCatalogId: state?.targetCatalogId || '',
      importStatus: state?.importStatus || '',
      estimatedImportTime: state?.estimatedImportTime || '',
      notes: state?.notes || '',
    };
  });
}

function csvEscape(value: string | number) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

function imageImportCsv(rows: ImageImportRow[]) {
  const headers = [
    'Source Image',
    'Count of VMs',
    'Owners',
    'Target Catalog ID',
    'Import Status',
    'Estimated Import Time',
    'Notes',
  ];
  const lines = rows.map((row) => [
    row.sourceImage,
    row.vmCount,
    row.owners,
    row.targetCatalogId,
    row.importStatus,
    row.estimatedImportTime,
    row.notes,
  ].map(csvEscape).join(','));
  return [headers.join(','), ...lines].join('\n');
}

function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let field = '';
  let row: string[] = [];
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      row.push(field);
      field = '';
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') index += 1;
      row.push(field);
      if (row.some((value) => value.trim())) rows.push(row);
      field = '';
      row = [];
    } else {
      field += char;
    }
  }

  row.push(field);
  if (row.some((value) => value.trim())) rows.push(row);
  if (rows.length < 2) return [];

  const headers = rows[0].map((header) => header.trim());
  return rows.slice(1).map((values) => Object.fromEntries(
    headers.map((header, index) => [header, values[index]?.trim() || '']),
  ));
}

function normalizeImportStatus(value: string): ImageImportStatusValue {
  return imageImportStatusOptions.includes(value as ImageImportStatusValue)
    ? value as ImageImportStatusValue
    : '';
}

export function importImageImportCsv(
  csvText: string,
  currentStatus: ImageImportStatus,
  knownSourceImages?: string[],
): { status: ImageImportStatus; applied: number; skipped: number } {
  const nextStatus = { ...currentStatus };
  const knownSources = knownSourceImages ? new Set(knownSourceImages) : null;
  let applied = 0;
  let skipped = 0;

  parseCsv(csvText).forEach((row) => {
    const sourceImage = row['Source Image'];
    if (!sourceImage || sourceImage === 'TOTAL' || (knownSources && !knownSources.has(sourceImage))) {
      skipped += 1;
      return;
    }
    nextStatus[sourceImage] = {
      targetCatalogId: row['Target Catalog ID'] || row.target_catalog_id || '',
      importStatus: normalizeImportStatus(row['Import Status'] || row.import_status || ''),
      estimatedImportTime: row['Estimated Import Time'] || row.estimated_import_time || '',
      notes: row.Notes || '',
    };
    applied += 1;
  });

  return { status: nextStatus, applied, skipped };
}

export default function ImageImportWorkflow() {
  const { state, dispatch } = useAppState();
  const { assignmentRows, imageImportStatus } = state;
  const [importStatus, setImportStatus] = React.useState('');
  const [importError, setImportError] = React.useState('');

  const imageRows = useMemo(
    () => buildImageImportRows(assignmentRows, imageImportStatus),
    [assignmentRows, imageImportStatus],
  );

  const summary = useMemo(() => ({
    totalImages: imageRows.length,
    totalVms: imageRows.reduce((total, row) => total + row.vmCount, 0),
    imported: imageRows.filter((row) => row.importStatus === 'Imported').length,
    active: imageRows.filter((row) => row.importStatus && row.importStatus !== 'Imported').length,
  }), [imageRows]);

  const csvHref = `data:text/csv;charset=utf-8,${encodeURIComponent(imageImportCsv(imageRows))}`;

  function updateImageStatus(sourceImage: string, patch: Partial<ImageImportRow>) {
    const currentRow = imageRows.find((row) => row.sourceImage === sourceImage);
    const current = imageImportStatus[sourceImage] || {
      targetCatalogId: currentRow?.targetCatalogId || '',
      importStatus: currentRow?.importStatus || '',
      estimatedImportTime: currentRow?.estimatedImportTime || '',
      notes: currentRow?.notes || '',
    };
    dispatch({
      type: 'SET_IMAGE_IMPORT_STATUS',
      payload: {
        ...imageImportStatus,
        [sourceImage]: {
          targetCatalogId: patch.targetCatalogId ?? current.targetCatalogId,
          importStatus: patch.importStatus ?? current.importStatus,
          estimatedImportTime: patch.estimatedImportTime ?? current.estimatedImportTime,
          notes: patch.notes ?? current.notes,
        },
      },
    });
  }

  async function importCsvFile(_event: unknown, content: { addedFiles?: File[] }) {
    const file = content.addedFiles?.[0];
    if (!file) return;
    setImportStatus('');
    setImportError('');
    try {
      const result = importImageImportCsv(
        await file.text(),
        imageImportStatus,
        imageRows.map((row) => row.sourceImage),
      );
      dispatch({ type: 'SET_IMAGE_IMPORT_STATUS', payload: result.status });
      setImportStatus(`Imported ${result.applied} image row(s)${result.skipped ? `; skipped ${result.skipped} row(s).` : '.'}`);
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Could not import image import CSV.');
    }
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Image Import Planning</h2>
          <p>Group active VMs by inferred source image and track IBM Cloud catalog import status.</p>
        </div>
        <div className="workflow-header-actions">
          <WorkflowHeaderHelp workflow="imageImport" />
          <Tag type={summary.active ? 'purple' : 'green'}>
            {summary.imported} of {summary.totalImages} imported
          </Tag>
        </div>
      </div>

      <div className="summary-grid image-import-summary">
        <Tile>
          <h3>Source images</h3>
          <p>{summary.totalImages}</p>
        </Tile>
        <Tile>
          <h3>VMs covered</h3>
          <p>{summary.totalVms}</p>
        </Tile>
        <Tile>
          <h3>Imported</h3>
          <p>{summary.imported}</p>
        </Tile>
        <Tile>
          <h3>Needs action</h3>
          <p>{summary.totalImages - summary.imported}</p>
        </Tile>
      </div>

      <div className="export-actions">
        <div className="remediation-import">
          <FileUploaderDropContainer
            accept={['.csv', 'text/csv']}
            labelText="Import image import CSV"
            onAddFiles={importCsvFile}
          />
        </div>
        <a
          className={`cds--btn cds--btn--secondary${imageRows.length === 0 ? ' cds--btn--disabled' : ''}`}
          href={csvHref}
          download="image-import-plan.csv"
          aria-disabled={imageRows.length === 0}
          onClick={(event) => {
            if (imageRows.length === 0) event.preventDefault();
          }}
        >
          Export image import CSV
        </a>
      </div>

      {importStatus && (
        <InlineNotification
          kind="success"
          lowContrast
          title="Image import CSV imported"
          subtitle={importStatus}
        />
      )}
      {importError && (
        <InlineNotification
          kind="error"
          lowContrast
          title="Image import CSV import failed"
          subtitle={importError}
        />
      )}

      {imageRows.length === 0 ? (
        <Tile className="empty-state">
          <h3>No source images found</h3>
          <p>Upload a workbook or load a project to start image import planning.</p>
        </Tile>
      ) : (
        <div className="vm-table-wrap image-import-table-wrap">
          <table className="vm-table image-import-table" aria-label="Image import planning rows">
            <thead>
              <tr>
                <th>Source image</th>
                <th>VMs</th>
                <th>Owners</th>
                <th>Target catalog ID</th>
                <th>Import status</th>
                <th>Estimated time</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {imageRows.map((row) => (
                <tr key={row.sourceImage}>
                  <td>
                    <strong>{row.sourceImage}</strong>
                  </td>
                  <td>{row.vmCount}</td>
                  <td>{row.owners || <span className="empty-value">Unassigned</span>}</td>
                  <td>
                    <TextInput
                      id={`catalog-${row.sourceImage}`}
                      labelText="Target catalog ID"
                      value={row.targetCatalogId}
                      onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                        updateImageStatus(row.sourceImage, { targetCatalogId: event.target.value })
                      }
                    />
                  </td>
                  <td>
                    <Select
                      id={`import-status-${row.sourceImage}`}
                      labelText="Import status"
                      value={row.importStatus}
                      onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                        updateImageStatus(row.sourceImage, { importStatus: event.target.value as ImageImportStatusValue })
                      }
                    >
                      {imageImportStatusOptions.map((status) => (
                        <SelectItem key={status || 'blank'} value={status} text={status || 'Not started'} />
                      ))}
                    </Select>
                  </td>
                  <td>
                    <TextInput
                      id={`estimated-${row.sourceImage}`}
                      labelText="Estimated import time"
                      value={row.estimatedImportTime}
                      onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                        updateImageStatus(row.sourceImage, { estimatedImportTime: event.target.value })
                      }
                    />
                  </td>
                  <td>
                    <TextArea
                      id={`image-notes-${row.sourceImage}`}
                      labelText="Notes"
                      value={row.notes}
                      onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                        updateImageStatus(row.sourceImage, { notes: event.target.value })
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layer>
  );
}

// Made with Bob
