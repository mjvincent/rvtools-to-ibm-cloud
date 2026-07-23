import type { PreflightResponse } from '../../../hooks/useApi';

export function preflightCompleteMessage(summary: PreflightResponse['summary']) {
  if (summary.blockers > 0) {
    return `Preflight complete: ${summary.blockers} blocker(s), ${summary.warnings} warning(s). Next: use the remediation queue or Resolve next issue before previewing or downloading handoff artifacts.`;
  }
  if (summary.warnings > 0) {
    return `Preflight complete: 0 blocker(s), ${summary.warnings} warning(s). Next: review warnings, then preview package files or download the Terraform ZIP.`;
  }
  return 'Preflight complete: 0 blocker(s), 0 warning(s). Next: preview package files or download the Terraform ZIP.';
}

export function packagePreviewGeneratedMessage(fileCount: number) {
  return `Package preview generated for ${fileCount} file(s). Next: inspect key Terraform and handoff files, then download the ZIP when reviewers are satisfied.`;
}

export function terraformZipBlockedMessage(blockers: number) {
  return `Terraform ZIP blocked by ${blockers} preflight blocker(s). Next: use Resolve next issue or the remediation queue, then rerun the download.`;
}

export function terraformZipDownloadedMessage(warnings: number) {
  if (warnings > 0) {
    return `Terraform ZIP downloaded with ${warnings} warning(s). Next: give the ZIP to the Terraform operator and review the included operator README before running Terraform.`;
  }
  return 'Terraform ZIP downloaded. Next: give the ZIP to the Terraform operator and review the included operator README before running Terraform.';
}

export function readinessReportDownloadedMessage() {
  return 'Export readiness report downloaded. Next: share it with reviewers or continue resolving any open Export readiness issues.';
}

export function planningStateDownloadedMessage() {
  return 'Planning state JSON downloaded. Next: keep it with the source RVTools workbook so this planning session can be restored later.';
}

export function planningStateImportedMessage(fileName: string) {
  return `Imported planning state from ${fileName}. Next: review restored assignments and save the project to persist them.`;
}

export function previewFileDownloadedMessage(path: string) {
  return `Downloaded ${path}. Next: continue reviewing package files or download the full Terraform ZIP.`;
}

export function exportActionFailureMessage(params: {
  action: string;
  error: unknown;
  fallback: string;
  nextStep: string;
}) {
  const cause = params.error instanceof Error ? params.error.message : params.fallback;
  return `${params.action} failed: ${cause} Next: ${params.nextStep}`;
}
