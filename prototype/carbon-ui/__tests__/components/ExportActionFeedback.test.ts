import {
  exportActionFailureMessage,
  packagePreviewGeneratedMessage,
  planningStateDownloadedMessage,
  planningStateImportedMessage,
  preflightCompleteMessage,
  previewFileDownloadedMessage,
  readinessReportDownloadedMessage,
  terraformZipBlockedMessage,
  terraformZipDownloadedMessage,
} from '../../components/workflows/export/ExportActionFeedback';

describe('ExportActionFeedback', () => {
  it('explains clear preflight results and the next action', () => {
    expect(preflightCompleteMessage({ blockers: 0, warnings: 0, info: 0, total: 0 })).toBe(
      'Preflight complete: 0 blocker(s), 0 warning(s). Next: preview package files or download the Terraform ZIP.',
    );
  });

  it('routes preflight blockers to remediation before package download', () => {
    expect(preflightCompleteMessage({ blockers: 2, warnings: 1, info: 0, total: 3 })).toContain(
      'Next: use the remediation queue or Resolve next issue',
    );
  });

  it('keeps Terraform ZIP downloaded in success copy for progress tracking', () => {
    expect(terraformZipDownloadedMessage(1)).toContain('Terraform ZIP downloaded with 1 warning(s).');
    expect(terraformZipDownloadedMessage(0)).toContain('Terraform ZIP downloaded.');
  });

  it('explains package preview and artifact downloads', () => {
    expect(packagePreviewGeneratedMessage(4)).toContain('Next: inspect key Terraform and handoff files');
    expect(readinessReportDownloadedMessage()).toContain('Next: share it with reviewers');
    expect(planningStateDownloadedMessage()).toContain('source RVTools workbook');
    expect(planningStateImportedMessage('planning-state.json')).toContain('Next: review restored assignments');
    expect(previewFileDownloadedMessage('README.md')).toContain('Downloaded README.md.');
  });

  it('explains blocked ZIP and generic action failures', () => {
    expect(terraformZipBlockedMessage(3)).toBe(
      'Terraform ZIP blocked by 3 preflight blocker(s). Next: use Resolve next issue or the remediation queue, then rerun the download.',
    );
    expect(exportActionFailureMessage({
      action: 'Terraform preview',
      error: new Error('Preview service unavailable.'),
      fallback: 'Terraform preview failed.',
      nextStep: 'retry after the backend is healthy.',
    })).toBe(
      'Terraform preview failed: Preview service unavailable. Next: retry after the backend is healthy.',
    );
  });
});
