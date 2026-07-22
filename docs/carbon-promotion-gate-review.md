# Carbon Promotion Gate Review

**Review date**: 2026-07-22
**Reviewed state**: Carbon UI through workflow progress guidance, inline step
help, collapsible completion checklists, dependency security maintenance, and
the FastAPI/Postgres package-generation path on `main`.
**Recommendation**: Do not promote Carbon to production yet. Continue running
Streamlit as the supported UI while Carbon closes the remaining parity and
production-readiness gaps.

## Executive Summary

Carbon has crossed the prototype viability threshold and now covers the core
planning path: upload, persistence, network planning, drag-and-drop assignment,
autosave, VM overrides, Phase 4 planning workflow surfaces, Terraform ZIP
export, package parity status, guided remediation queue, readiness reporting,
workflow progress guidance, inline step help, visible collapsible completion
checklists, and Docker Compose runtime are implemented and verified.

Carbon has not crossed the production replacement threshold. The remaining gaps
are mostly production-hardening and deeper parity evidence: additional
real-workbook handoff fixture coverage, broader accessibility and browser
coverage, additional customer-scale performance fixtures beyond the workshop
sample, production support posture, and a formal Streamlit-to-Carbon cutover
plan.

The next promotion work should be evidence-heavy rather than feature-heavy:
prove Carbon output parity across more representative workbooks, complete
manual accessibility/UAT evidence, validate the hosted runtime and support
model, then run a formal go/no-go review.

## Gate Matrix

| Gate | Status | Evidence | Remaining Work | Recommended Phase |
| --- | --- | --- | --- | --- |
| Gate 1: Core Functionality | Pass | Workbook upload calls FastAPI summary; project save/load uses Postgres; drag/drop assigns subnet/security/storage/wave; Terraform ZIP export works from saved Carbon network plans. | Keep maintaining regression coverage as parity work lands. | Maintenance |
| Gate 2: Feature Parity | Partial | Carbon now has workflow surfaces for wave planning, remediation backlog, image import planning, migration ops, VM overrides, decision audit, handoff ZIP files, export readiness queue, readiness report, and Streamlit-vs-Carbon fixture comparisons. | Add more real-workbook edge fixtures and close remaining Streamlit bulk/edge workflow gaps before promotion. | Phase 5 and Phase 6 |
| Gate 3: Network Planning | Partial | Carbon supports VPC/subnet/security/storage/wave/network component planning, diagram-driven network component edit handoff, local network validation findings, saved network plans, diagram display, Terraform generation, package inventory parity status, backend package preflight feedback, safe preflight next-step actions, a remediation queue, and a full package browser preview in Export. | Verify the network editing and validation flow through accessibility and UAT evidence, then continue backend parity coverage. | Phase 5 and Phase 6 |
| Gate 4: User Experience | Partial | Native drag/drop supports single and multi-select assignment with confirmation modal, drop highlighting, row tags, row-level unassign, readiness-chip routing, explicit checkbox/drop-zone accessible labels, keyboard-operable assignment buttons, guided remediation queue routing, bulk high-confidence suggestion review, bulk override cleanup, workflow progress guidance, workflow-header step help, user-guide popup routing, and collapsible completion checklists. Playwright coverage covers keyboard navigation and review-chip routing across Chromium, Firefox, and WebKit. The manual review checklist and results/sign-off template are prepared. | Run the [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md), record outcomes in the [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md), then complete broader screen-reader/manual accessibility review, mobile/tablet review, and large-workbook UX/performance tests beyond the workshop sample. | Phase 6 |
| Gate 5: Quality and Testing | Partial | Verified: Python compile/full pytest, Carbon TypeScript, Jest, multi-browser Playwright smoke, handoff parity fixtures, real-workbook operational overlay parity, planning-state JSON import/export, backend preflight endpoint/UI feedback and next-step actions, API ZIP inventory guard, UI/backend ZIP inventory drift guard, export readiness queue tests, sample-workbook summary performance guards, optional private customer-workbook summary guard hook, sanitized private-workbook evidence helper/template, workshop state/assignment/preview/ZIP performance guards, generated 3,000-row Carbon API state/update guards, and generated 5,000-row Carbon UI filtering guards. | Add broader e2e coverage for failure paths, captured evidence from private customer-scale workbooks, accessibility automation, and more real-workbook parity fixtures. | Phase 5-6 |
| Gate 6: Production Readiness | Partial | Docker Compose starts Streamlit, API, Carbon UI, and Postgres; local health/log checks are documented; Carbon healthcheck reports healthy; persistence warning exists; user manual now documents the Carbon checkpoint and production boundary; promotion/cutover guide now documents staged rollout and rollback; operations runbook documents backup/recovery, monitoring/logging, incident response, support ownership matrix, rollback authority, a successful local restore drill, local monitoring evidence, and a hosted operations readiness checklist. | Complete hosted-runtime alerts/log sinks, retention, backup/restore, support ownership, access control, artifact handling, and rollback evidence before promotion. | Phase 6 |

## Validation Evidence

Latest completed validation:

```bash
make compile
venv/bin/python -m pytest -q
cd prototype/carbon-ui
npx tsc --noEmit
npm test -- --runInBand
CARBON_BASE_URL=http://localhost:3000 npx playwright test
```

Observed results:
- Python compile: passed
- Python pytest: 360 passed, 1 skipped
- Carbon TypeScript: 0 errors
- Carbon Jest: 249 passed
- Carbon Playwright: 27 passed across Chromium, Firefox, and WebKit
- Docker Compose health: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright coverage includes workbook upload, project save/load, subnet
drag/drop, multi-select subnet/security/storage/wave drops, row-level unassign,
autosave reload, persistence outage warning display, Export preflight blocker
routing to remediation review, Export remediation queue high-confidence bulk
fix application, suggestion audit/undo, profile override save/load/export
parity, bulk override missing-reason cleanup, Export
preview/download/save-before-export failure handling, package preview handoff CSV
switching/download, keyboard navigation, keyboard assignment through explicit Assign buttons,
Network Plan validation/component-edit accessible role coverage,
readiness-chip review routing, drag/drop accessibility labels, row checkbox
accessible names, package preview close behavior, and temporary smoke-project
cleanup across Chromium, Firefox, and WebKit. The suite runs with one worker because the smoke tests share the
same FastAPI/Postgres backend during project save/load and cleanup.
Fast Jest coverage now also guards Export preflight service failures,
save-before-preview failures, and ZIP generation failures so Carbon does not
show stale success or call later backend steps after an earlier rejection.
It also guards malformed planning-state imports so invalid JSON or incomplete
schema files surface errors without replacing the current exportable project
state. Intake unit coverage now also verifies workbook upload failures preserve
the current workbook state and that a successful retry clears the previous
upload error. Shared Carbon API error handling also normalizes transport
outages and non-JSON backend failures into recovery guidance for checking the
FastAPI service, Docker Compose or dev-server logs, and retrying.

The Python parity suite now includes Streamlit-vs-Carbon single-VM, edge-case,
multi-VM, workshop real-workbook subset, workshop operational edge subset, and
sample-workbook operational overlay comparisons, including real-workbook
disk/partition mapping parity and exact non-preflight handoff file parity for the sample workbook;
manifest handoff references; sample-workbook handoff contract assertions;
sample-workbook API ZIP inventory and handoff CSV payload
verification; API preview-vs-ZIP file/content parity; and a Carbon Export UI
inventory drift test against backend ZIP
inventory constants. Carbon performance coverage now includes generated
3,000-row API project-state save/load/update guards and generated 5,000-row UI
VM Assignment search/sort plus VM Overrides missing-reason filtering guards.
The Python suite also guards summary parsing across both checked-in real sample
workbooks, supports optional private customer-workbook summary guards through
`CARBON_PERF_CUSTOMER_WORKBOOKS`, and guards workshop project state save/load,
VM assignment update, Carbon Terraform preview, and ZIP generation performance.
The checked-in real-workbook evidence map is recorded in
[Carbon Real-Workbook Parity Evidence](carbon-real-workbook-parity-evidence.md).

## Phase 4 Status

Current feature-parity status:

1. **Remediation Tracker**
   - Carbon workflow exists with generated readiness backlog rows,
     editable owner/status/due-date/notes fields, CSV import/export, and
     project-state persistence in both Carbon and Streamlit-compatible tracker
     shapes.
   - Component coverage verifies image, migration, memory, and network blocker
     categories, saved blocker metadata, lowercase readiness states, field
     edits, unmatched CSV import rows, fallback signature imports, and unknown
     status normalization.
   - Handoff ZIP includes `remediation-backlog.csv`; multi-VM parity fixtures
     compare operational handoff behavior, manifest remediation summaries, and
     closed/resolved remediation filtering for cutover readiness.
   - Remaining: broader real-workbook finding/category edge coverage.

2. **Image Import Planning**
   - Carbon workflow exists with inferred source-image grouping,
     owner rollups, editable import status, target catalog ID, estimated import
     time, notes, guarded CSV import/export, project-state persistence, and IMG
     readiness-chip routing.
   - Handoff ZIP includes `image-import-plan.csv` and
     `image-import-variables.tfvars.example`; parity fixtures cover mixed
     import states, manifest summaries, custom image IDs, and cutover impact.
   - Remaining: broader real-workbook image grouping edge coverage.

3. **Migration Ops**
   - Carbon workflow exists with VM-level cutover readiness, summaries
     by wave and cutover group, blockers from planning gaps, readiness signals,
     unresolved remediation, Streamlit-compatible remediation metadata, image
     import state, and cutover-readiness CSV export.
   - Handoff ZIP includes `cutover-readiness.csv`; multi-VM parity fixtures
     cover mixed waves, remediation descriptions, image import, blocked
     readiness, and resolved-remediation filtering.
   - Remaining: broader real-workbook cutover edge coverage.

4. **Wave Planning Parity**
   - Carbon workflow supports per-VM wave, cutover group, owner,
     application, priority, dependency group, scoped bulk assignment, CSV
     import/export, completion metrics, and application/dependency conflict
     detection.
   - Component coverage verifies all editable wave fields, bulk assignment
     scopes, unmatched CSV import rows, completion status, and
     application/dependency conflict warnings.
   - Handoff parity fixtures cover mixed wave and cutover-group output.
   - Remaining: broader real-workbook wave/cutover edge coverage.

5. **Decision Audit and Handoff Parity**
   - VM Overrides workflow exists with profile/storage override values,
     required reason capture, VM exclusion reasons, Assignment row routing, and
     decision-audit CSV export.
   - Carbon Terraform ZIP now includes `decision-audit.csv` with pricing impact
     columns through the Carbon-to-handoff normalizer.
   - Carbon Terraform ZIP now also includes `remediation-backlog.csv`,
     `image-import-plan.csv`, `cutover-readiness.csv`, and `planning-state.json`
     from saved Carbon state.
   - Carbon Terraform ZIP now includes the remaining handoff artifact inventory:
     manifest, assessment quality, preflight, pricing diagnostics,
     mapping/readiness CSVs, image import variables, and runbook.
   - Carbon Export now includes package parity status, readiness checklist,
     backend preflight routing, remediation queue, suggested fixes, bulk
     high-confidence application, suggestion audit/undo, readiness report JSON,
     and package preview close/download controls.
   - Streamlit-vs-Carbon fixture coverage now includes a synthetic fixture,
     multi-NIC/disk/partition/memory/readiness edge fixture, multi-VM
     operational fixture, workshop real-workbook subset fixture,
     workshop real-workbook operational edge fixture for overrides, exclusions,
     remediation, image import, wave/cutover metadata, unknown-network readiness,
     and exact operational handoff parity, sample-workbook operational overlay fixture with exact non-preflight
     handoff file parity, sample-workbook contract assertions, API ZIP
     inventory verification, Export UI/backend inventory
     drift protection, and performance coverage for sample-workbook summary
     parsing plus workshop project state save/load, VM assignment update,
     Terraform preview, and Terraform ZIP generation.
   - Remaining: additional real-workbook edge fixtures and promotion-gate
     evidence for large or unusual customer workbooks.

## Phase 5 Backlog

- Use [Carbon Handoff Parity](carbon-handoff-parity.md) as the package
  inventory and implementation tracker.
- Add additional real-workbook Streamlit-vs-Carbon fixture comparisons.
- Improve any workbook-derived source metadata gaps found by those fixtures.
- Extend Carbon-side remediation guidance with additional safe autofill options for low-risk findings.
- Extend failure-path browser coverage beyond persistence outage, remediation-route preflight blockers, and Export preview/download/save-before-export failures.
- Extend planning-state reload coverage through Playwright and user acceptance.

## Replacement Gap Checklist

Carbon should remain a candidate UI, not the default UI, until these checklist
items are complete:

| Gap Area | Current State | Required Closure |
| --- | --- | --- |
| Feature parity | Core planning workflows, overrides, remediation, image import, migration ops, package preview, ZIP generation, guided help, and completion checklists are implemented. | Confirm remaining Streamlit edge workflows are either implemented in Carbon or explicitly declared out of Carbon promotion scope. |
| Export/package parity | Handoff inventory and API ZIP parity are strongly covered for checked-in fixtures and sample/workshop paths. | Add at least one additional representative real-workbook parity run, preferably a sanitized customer-scale workbook or documented private evidence run. |
| Real workbook validation | Small sample, workshop sample, generated large-state tests, optional private workbook hooks, and a checked-in evidence map exist. | Add at least one additional representative real-workbook parity run, preferably a sanitized customer-scale workbook or documented private evidence run. |
| Accessibility and UAT | Keyboard and browser automation exists; checklist, result template, runbook, and manual evidence index exist. | Complete manual keyboard, screen-reader, responsive, browser, and migration-user UAT review and store results in the template. |
| Deployment and operations | Docker Compose, runbook, restore drill, local monitoring, health checks, and hosted operations readiness checklist are documented. | Validate the intended hosted runtime, log sinks, alerts, retention policy, backup/restore path, support escalation flow, artifact handling, and rollback authority. |
| Support and rollback | Promotion/cutover guide defines staged rollout and rollback pattern. | Fill named support owners, rollback authority, release-candidate commit/tag, and same-day rollback acceptance criteria. |
| Production decision | Current decision is no-go. | Run a formal go/no-go review after the evidence above is current and linked, then record the outcome in the [Carbon Promotion Decision Packet](carbon-promotion-decision-packet.md). |

## Phase 6 Backlog

- Accessibility audit, including keyboard-only workflows and DnD alternatives, using the [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md) and recording sign-off in the [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md).
- Use the [Carbon Manual UAT Evidence Index](carbon-manual-uat-evidence-index.md)
  to assemble release-candidate evidence packets and track open human review
  areas.
- Additional customer-scale performance benchmark fixtures for large RVTools
  workbooks.
- Multi-browser e2e coverage.
- Keep Carbon-specific user documentation current as promotion criteria change.
- Repeat the documented restore drill from
  [Carbon Operations Runbook](carbon-operations-runbook.md) against the intended
  hosted runtime or platform-managed backup system.
- Wire hosted-runtime alerts, log sinks, and retention policy for the chosen
  platform.
- Fill in named production support owners and rollback authority in the
  operations runbook.
- Keep [Carbon Promotion and Cutover Guide](carbon-promotion-cutover-guide.md)
  current as deployment decisions change.

## Go / No-Go

**Current decision**: No-go for replacing Streamlit.

**Rationale**: Carbon now proves the core architecture, differentiated DnD
experience, Phase 4 workflow surfaces, and a substantial handoff parity path
for the checked-in sample and workshop workbooks. The production Streamlit app
remains the supported UI until Carbon has broader customer-scale workbook
evidence, accessibility/browser/performance coverage, and production support
documentation.

**Next review trigger**: Re-run this gate review after additional real-workbook
edge fixtures, additional customer-scale performance validation, and broader
accessibility coverage are complete.
