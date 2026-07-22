# Carbon Streamlit Parity Roadmap

This roadmap translates the Carbon promotion gates into an execution backlog.
It should be used before any decision to make Carbon the default UI.

Streamlit remains the supported production workbench. Carbon is the enterprise
UI candidate and should keep using the shared FastAPI, parser, readiness,
Terraform, and handoff logic instead of duplicating application behavior.

## Current Recommendation

Do not replace Streamlit yet.

Carbon is now past the basic prototype stage. It can upload workbooks through
FastAPI, save and reload projects, edit assignment/planning state, run package
preflight, preview package contents, and generate Terraform ZIPs with the major
handoff artifact inventory. Recent UX work also added workflow progress
guidance, workflow-header step help, a separate user-guide route, and compact
collapsible completion checklists for each main workflow.

The next work should focus on evidence and backend-backed parity, not more
pure UI reshaping. The highest value is proving that Carbon can complete the
same migration assessment and handoff workflow as Streamlit for representative
workbooks, then closing any workflow gaps found by those comparisons.

As of the July 22, 2026 promotion gap review, the highest-value next branch is
real-workbook parity evidence. Additional visual polish should be secondary
unless manual UAT finds a usability blocker.

The current checked-in sample and workshop workbook evidence is summarized in
[Carbon Real-Workbook Parity Evidence](carbon-real-workbook-parity-evidence.md).

## Capability Matrix

| Capability | Streamlit status | Carbon status | Promotion requirement |
| --- | --- | --- | --- |
| RVTools upload and summary | Production | Implemented through FastAPI | Keep sample and workshop workbook coverage current. |
| Project persistence | Production planning-state JSON plus Postgres save progress | Implemented through FastAPI/Postgres project save/load/autosave | Verify restore behavior with real users and hosted runtime backups. |
| VM review and decisions | Production | Implemented through Carbon assignment and override flows | Confirm equivalent decision audit and package output for representative workbooks. |
| Network/security/storage/wave assignment | Production tab workflows | Implemented with Carbon buckets, drag/drop, bulk assignment, keyboard alternatives, saved network plans, diagram-driven network component edit handoff, and local network validation findings | Continue accessibility review and backend parity evidence. |
| Wave planning | Production | Implemented with editable fields, CSV import/export, and package handoff output | Add more real-workbook cutover and dependency edge coverage. |
| Remediation backlog | Production | Implemented with editable tracker, CSV import/export, package output, and Export remediation queue | Expand readiness-category edge fixtures and failure-path tests. |
| Image import planning | Production | Implemented with grouped source images, editable status, CSV import/export, and package output | Expand image grouping and custom image ID edge coverage. |
| Migration Ops | Production | Implemented with readiness summaries and cutover-readiness export | Validate with realistic wave/cutover planning exercises. |
| Export package build | Production | Implemented through FastAPI Terraform ZIP generation, package preflight, preview, and parity inventory checks | Continue exact Streamlit-vs-Carbon fixture comparisons. |
| Pricing modes | Production static/cached/live behavior | Partial static-catalog diagnostics in Carbon ZIP | Decide whether live/cached pricing belongs in Carbon promotion scope. |
| User guidance | Production Streamlit tabs and manual | Implemented with Carbon progress guide, workflow-header step help, user-guide popup route, and collapsible completion checklists | Validate during UAT that users understand each step and can progress without facilitator help. |
| Accessibility and UAT | Streamlit production baseline | Checklist and templates exist; Carbon has keyboard/browser coverage but needs formal sign-off | Complete checklist and record evidence before pilot/default switch. |
| Operations | Streamlit Docker/local paths documented | Compose stack, operations runbook, backup/restore guidance, and health checks exist | Fill named support owners, hosted logging/alerts, retention, and rollback authority. |

## Recommended Next Branches

1. **Real-workbook parity expansion**
   - Add another checked-in sanitized fixture or optional private-workbook
     evidence run.
   - Compare Carbon and Streamlit handoff outputs for the package files that
     drive migration operations.
   - Prefer API-level ZIP and preview tests when possible so evidence covers
     the same backend path Carbon users exercise.
   - Treat output diffs as product decisions: fix regressions, or document
     intentional Carbon-only preflight differences.
   - Record which workbook, commit, generated package files, and comparison
     result were used as promotion evidence.

2. **Carbon failure-path hardening**
   - Extend browser coverage for API unavailable, package preview failure,
     malformed planning-state import, workbook upload failure, and ZIP
     generation failure.
   - Keep shared API error normalization current so transport outages and
     non-JSON backend failures give users concrete recovery guidance.
   - Keep fast unit coverage for Export failure paths so preflight, preview,
     and ZIP-generation errors cannot regress without running the full browser
     suite.
   - Keep malformed planning-state import coverage so bad JSON or incomplete
     schemas cannot overwrite the current valid Carbon project state.
   - Keep workbook upload failure and retry coverage so parser/API outages do
     not replace the current workbook state or leave stale upload errors.
   - Ensure the UI never implies work is saved or export-ready when the backend
     rejected the operation.

3. **Network planning editor depth**
   - Continue enriching network component editing beyond the current
     diagram-driven edit handoff.
   - Keep the local Network Plan validation panel current for missing VPC
     references, subnet CIDR issues, component attachment warnings, and
     duplicate Terraform labels.
   - Keep the saved `network-plan.json` contract stable.
   - Confirm Terraform output and package preflight still reflect the saved
     plan, not transient UI state.

4. **Accessibility and UAT evidence**
   - Run the manual checklist against the current Carbon workflow.
   - Capture keyboard, screen-reader, browser, and user-acceptance results in
     the results template.
   - Include the progress guide, step help, user-guide popup, and completion
     checklist behavior in reviewer feedback.
   - Promote only if the primary workflow has acceptable evidence.

5. **Production operations closure**
   - Fill named support owner and rollback authority fields.
   - Confirm backup/restore in the intended hosted runtime, not only local
     Docker.
   - Define retention for uploaded RVTools workbooks, saved project state, and
     generated artifacts.

## Near-Term No-Go Items

Carbon should not become the default UI while any of these remain true:

- Real-workbook handoff parity is not current for at least one small sample and
  one larger representative workbook.
- Accessibility and UAT results are not recorded for the primary workflow.
- Support owners, rollback authority, hosted logs, alerts, and retention are
  not assigned.
- Users cannot recover work confidently through saved projects or exported
  planning state.
- Known Carbon-vs-Streamlit differences are not documented.

## What Not To Do Next

- Do not fork Streamlit and Carbon into separate repositories.
- Do not retire Streamlit as the fallback path.
- Do not duplicate parser, readiness, pricing, Terraform, or handoff logic in
  TypeScript.
- Do not add unrelated migration targets while IBM Cloud VPC Terraform remains
  the tool boundary.
- Do not prioritize cosmetic polish over parity evidence, accessibility
  evidence, and failure-path reliability.

## Decision Sequence

1. Finish real-workbook parity expansion.
2. Close critical Carbon workflow and failure-path gaps.
3. Complete accessibility and UAT evidence.
4. Complete hosted operations evidence and support ownership.
5. Run the promotion gate review.
6. Enter shadow mode with Streamlit as fallback.
7. Pilot with one realistic migration assessment.
8. Decide whether Carbon becomes the default UI.

See also:

- [Carbon Promotion and Cutover Guide](carbon-promotion-cutover-guide.md)
- [Carbon Promotion Gate Review](carbon-promotion-gate-review.md)
- [Carbon Handoff Parity](carbon-handoff-parity.md)
- [Carbon Real-Workbook Parity Evidence](carbon-real-workbook-parity-evidence.md)
- [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md)
- [Carbon Operations Runbook](carbon-operations-runbook.md)
