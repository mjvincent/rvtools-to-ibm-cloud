'use client';

import React, { useMemo } from 'react';
import { Layer, Tag, Tile } from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import WorkflowHeaderHelp from '../ui/WorkflowHeaderHelp';
import type {
  AssignmentVm,
  CutoverReadinessRow,
  CutoverStatus,
  CutoverSummaryRow,
  ImageImportStatus,
  RemediationTracker,
} from '../../types/network-planning';

const resolvedRemediationStatuses = new Set(['resolved', 'closed', 'complete', 'completed']);

function sourceImageForRow(row: AssignmentVm) {
  return row.originalSpecs || row.imageReasons || row.profile || row.name;
}

function statusFromCategories(categories: string[]): CutoverStatus {
  if (categories.length === 0) return 'Ready';
  if (categories.some((category) => category !== 'Readiness Review')) return 'Blocked';
  return 'Review';
}

function clean(value: unknown, fallback = '') {
  if (value === undefined || value === null) return fallback;
  const text = String(value).trim();
  return text || fallback;
}

function remediationRowsForVm(vmId: string, remediationTracker: RemediationTracker) {
  return Object.entries(remediationTracker).filter(([blockerId, entry]) => {
    const idVm = clean(entry.vmKey || entry.vm_key) || blockerId.split('::', 1)[0].split(':', 1)[0];
    return idVm === vmId && !resolvedRemediationStatuses.has(entry.status.toLowerCase());
  });
}

export function buildCutoverReadinessRows(
  assignmentRows: AssignmentVm[],
  remediationTracker: RemediationTracker,
  imageImportStatus: ImageImportStatus,
): CutoverReadinessRow[] {
  return assignmentRows.flatMap((row) => {
    const blockers: Array<[string, string, string]> = [];
    const missing = [
      ['Wave', row.wave],
      ['Cutover Group', row.cutoverGroup],
      ['Owner', row.owner],
      ['Application', row.application],
    ].filter(([, value]) => !value).map(([label]) => label);

    if (missing.length) {
      blockers.push([
        'Missing Planning',
        `Missing required planning fields: ${missing.join(', ')}`,
        'Complete Wave Planning fields before scheduling cutover.',
      ]);
    }

    [
      ['Image Readiness', row.image, row.imageReasons, 'Resolve image readiness blockers.'],
      ['Migration Readiness', row.migration, row.migrationReasons, 'Resolve migration readiness blockers.'],
      ['Memory Readiness', row.memory, row.memoryReasons, 'Resolve memory readiness blockers.'],
      ['Network Readiness', row.networkReadiness, row.networkReasons, 'Resolve network readiness blockers.'],
    ].forEach(([field, status, reason, action]) => {
      const normalizedStatus = clean(status).toLowerCase();
      if (normalizedStatus === 'blocked') {
        blockers.push(['Readiness Blocker', `${field}: ${reason || 'Blocked'}`, action]);
      } else if (normalizedStatus === 'review') {
        blockers.push(['Readiness Review', `${field}: ${reason || 'Needs review'}`, `Review ${field.toLowerCase()} before cutover.`]);
      }
    });

    remediationRowsForVm(row.id, remediationTracker).forEach(([blockerId, entry]) => {
      const blockerType = clean(
        entry.blockerType || entry.blocker_type || entry.type,
        blockerId.split('::')[1] || 'Remediation item',
      );
      const description = clean(
        entry.blockerDescription || entry.blocker_description || entry.description || entry.notes,
        blockerId,
      );
      const status = clean(entry.status, 'Open');
      blockers.push([
        'Unresolved Remediation',
        `${blockerType}: ${description} (${status})`,
        'Resolve or formally defer the remediation backlog item.',
      ]);
    });

    const sourceImage = sourceImageForRow(row);
    const importStatus = imageImportStatus[sourceImage]?.importStatus || '';
    if (importStatus !== 'Imported') {
      blockers.push([
        'Image Import Pending',
        `${sourceImage} import status is ${importStatus || 'not started'}`,
        'Import the source image and record status as Imported.',
      ]);
    }

    const cutoverStatus = statusFromCategories(blockers.map(([category]) => category));
    const base = {
      vmName: row.name,
      wave: row.wave,
      cutoverGroup: row.cutoverGroup,
      owner: row.owner,
      application: row.application,
      cutoverStatus,
    };

    if (blockers.length === 0) {
      return [{
        ...base,
        blockerCategory: 'Ready',
        blockerReason: 'No cutover blockers found',
        recommendedNextAction: 'Proceed with cutover scheduling.',
      }];
    }

    return blockers.map(([blockerCategory, blockerReason, recommendedNextAction]) => ({
      ...base,
      blockerCategory,
      blockerReason,
      recommendedNextAction,
    }));
  });
}

export function summarizeCutoverReadiness(
  rows: CutoverReadinessRow[],
  groupField: 'wave' | 'cutoverGroup',
): CutoverSummaryRow[] {
  const summary = new Map<string, {
    vms: Set<string>;
    ready: Set<string>;
    review: Set<string>;
    blocked: Set<string>;
    missingPlanning: number;
    unresolvedRemediation: number;
    imagePending: number;
  }>();

  rows.forEach((row) => {
    const group = row[groupField] || 'Unassigned';
    const item = summary.get(group) || {
      vms: new Set<string>(),
      ready: new Set<string>(),
      review: new Set<string>(),
      blocked: new Set<string>(),
      missingPlanning: 0,
      unresolvedRemediation: 0,
      imagePending: 0,
    };
    item.vms.add(row.vmName);
    if (row.cutoverStatus === 'Ready') item.ready.add(row.vmName);
    if (row.cutoverStatus === 'Review') item.review.add(row.vmName);
    if (row.cutoverStatus === 'Blocked') item.blocked.add(row.vmName);
    if (row.blockerCategory === 'Missing Planning') item.missingPlanning += 1;
    if (row.blockerCategory === 'Unresolved Remediation') item.unresolvedRemediation += 1;
    if (row.blockerCategory === 'Image Import Pending') item.imagePending += 1;
    summary.set(group, item);
  });

  return [...summary.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([group, item]) => ({
    group,
    vms: item.vms.size,
    ready: item.ready.size,
    review: item.review.size,
    blocked: item.blocked.size,
    missingPlanning: item.missingPlanning,
    unresolvedRemediation: item.unresolvedRemediation,
    imagePending: item.imagePending,
  }));
}

function csvEscape(value: string | number) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

export function cutoverReadinessCsv(rows: CutoverReadinessRow[]) {
  const headers = [
    'VM Name',
    'Wave',
    'Cutover Group',
    'Owner',
    'Application',
    'Cutover Status',
    'Blocker Category',
    'Blocker Reason',
    'Recommended Next Action',
  ];
  const lines = rows.map((row) => [
    row.vmName,
    row.wave,
    row.cutoverGroup,
    row.owner,
    row.application,
    row.cutoverStatus,
    row.blockerCategory,
    row.blockerReason,
    row.recommendedNextAction,
  ].map(csvEscape).join(','));
  return [headers.join(','), ...lines].join('\n');
}

function SummaryTable({ title, rows }: { title: string; rows: CutoverSummaryRow[] }) {
  return (
    <div className="migration-summary-table">
      <h3>{title}</h3>
      {rows.length === 0 ? (
        <Tile className="empty-state">
          <p>No planning data is available yet.</p>
        </Tile>
      ) : (
        <div className="vm-table-wrap">
          <table className="vm-table migration-ops-summary-table" aria-label={title}>
            <thead>
              <tr>
                <th>Group</th>
                <th>VMs</th>
                <th>Ready</th>
                <th>Review</th>
                <th>Blocked</th>
                <th>Missing planning</th>
                <th>Remediation</th>
                <th>Image pending</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.group}>
                  <td>{row.group}</td>
                  <td>{row.vms}</td>
                  <td>{row.ready}</td>
                  <td>{row.review}</td>
                  <td>{row.blocked}</td>
                  <td>{row.missingPlanning}</td>
                  <td>{row.unresolvedRemediation}</td>
                  <td>{row.imagePending}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function MigrationOpsWorkflow() {
  const { state } = useAppState();
  const { assignmentRows, remediationTracker, imageImportStatus } = state;

  const rows = useMemo(
    () => buildCutoverReadinessRows(assignmentRows, remediationTracker, imageImportStatus),
    [assignmentRows, remediationTracker, imageImportStatus],
  );
  const waveSummary = useMemo(() => summarizeCutoverReadiness(rows, 'wave'), [rows]);
  const cutoverSummary = useMemo(() => summarizeCutoverReadiness(rows, 'cutoverGroup'), [rows]);
  const vmStatuses = useMemo(() => {
    const statuses = new Map<string, CutoverStatus>();
    rows.forEach((row) => statuses.set(row.vmName, row.cutoverStatus));
    return [...statuses.values()];
  }, [rows]);
  const blockers = rows.filter((row) => row.blockerCategory !== 'Ready');
  const csvHref = `data:text/csv;charset=utf-8,${encodeURIComponent(cutoverReadinessCsv(rows))}`;

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Migration Ops</h2>
          <p>Track cutover readiness across waves, remediation, and image imports.</p>
        </div>
        <div className="workflow-header-actions">
          <WorkflowHeaderHelp workflow="migrationOps" />
          <Tag type={blockers.length ? 'red' : 'green'}>
            {blockers.length} open blocker(s)
          </Tag>
        </div>
      </div>

      <div className="summary-grid migration-ops-summary">
        <Tile>
          <h3>Ready</h3>
          <p>{vmStatuses.filter((status) => status === 'Ready').length}</p>
        </Tile>
        <Tile>
          <h3>Review</h3>
          <p>{vmStatuses.filter((status) => status === 'Review').length}</p>
        </Tile>
        <Tile>
          <h3>Blocked</h3>
          <p>{vmStatuses.filter((status) => status === 'Blocked').length}</p>
        </Tile>
        <Tile>
          <h3>Open blockers</h3>
          <p>{blockers.length}</p>
        </Tile>
      </div>

      <div className="export-actions">
        <a
          className={`cds--btn cds--btn--secondary${rows.length === 0 ? ' cds--btn--disabled' : ''}`}
          href={csvHref}
          download="cutover-readiness.csv"
          aria-disabled={rows.length === 0}
          onClick={(event) => {
            if (rows.length === 0) event.preventDefault();
          }}
        >
          Export cutover readiness CSV
        </a>
      </div>

      <div className="migration-ops-grid">
        <SummaryTable title="By Wave" rows={waveSummary} />
        <SummaryTable title="By Cutover Group" rows={cutoverSummary} />
      </div>

      <div className="vm-table-wrap migration-ops-detail-wrap">
        <table className="vm-table migration-ops-detail-table" aria-label="Cutover readiness detail">
          <thead>
            <tr>
              <th>VM</th>
              <th>Wave</th>
              <th>Cutover group</th>
              <th>Owner</th>
              <th>Status</th>
              <th>Blocker</th>
              <th>Next action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${row.vmName}-${row.blockerCategory}-${index}`}>
                <td>
                  <strong>{row.vmName}</strong>
                  <span>{row.application || 'No application'}</span>
                </td>
                <td>{row.wave || <span className="empty-value">Unassigned</span>}</td>
                <td>{row.cutoverGroup || <span className="empty-value">Unassigned</span>}</td>
                <td>{row.owner || <span className="empty-value">Unassigned</span>}</td>
                <td>
                  <Tag type={row.cutoverStatus === 'Ready' ? 'green' : row.cutoverStatus === 'Review' ? 'purple' : 'red'}>
                    {row.cutoverStatus}
                  </Tag>
                </td>
                <td>
                  <strong>{row.blockerCategory}</strong>
                  <span>{row.blockerReason}</span>
                </td>
                <td>{row.recommendedNextAction}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layer>
  );
}

// Made with Bob
