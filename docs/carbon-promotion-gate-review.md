# Carbon Promotion Gate Review

**Review date**: 2026-07-09
**Reviewed state**: Carbon UI Phases 1-6 in progress on
`feature/carbon-ui-network-planning-phase1`  
**Recommendation**: Do not promote Carbon to production yet. Continue running
Streamlit as the supported UI while Carbon closes the remaining parity and
production-readiness gaps.

## Executive Summary

Carbon has crossed the prototype viability threshold and now covers the core
planning path: upload, persistence, network planning, drag-and-drop assignment,
autosave, VM overrides, Phase 4 planning workflow surfaces, Terraform ZIP
export, package parity status, guided remediation queue, readiness reporting,
and Docker Compose runtime are implemented and verified.

Carbon has not crossed the production replacement threshold. The remaining gaps
are mostly production-hardening and deeper parity evidence: additional
real-workbook handoff fixture coverage, broader accessibility and browser
coverage, additional customer-scale performance fixtures beyond the workshop
sample, production support posture, and a formal Streamlit-to-Carbon cutover
plan.

## Gate Matrix

| Gate | Status | Evidence | Remaining Work | Recommended Phase |
| --- | --- | --- | --- | --- |
| Gate 1: Core Functionality | Pass | Workbook upload calls FastAPI summary; project save/load uses Postgres; drag/drop assigns subnet/security/storage/wave; Terraform ZIP export works from saved Carbon network plans. | Keep maintaining regression coverage as parity work lands. | Maintenance |
| Gate 2: Feature Parity | Partial | Carbon now has workflow surfaces for wave planning, remediation backlog, image import planning, migration ops, VM overrides, decision audit, handoff ZIP files, export readiness queue, readiness report, and Streamlit-vs-Carbon fixture comparisons. | Add more real-workbook edge fixtures and close remaining Streamlit bulk/edge workflow gaps before promotion. | Phase 5 and Phase 6 |
| Gate 3: Network Planning | Partial | Carbon supports VPC/subnet/security/storage/wave/network component planning, saved network plans, diagram display, Terraform generation, package inventory parity status, backend package preflight feedback, safe preflight next-step actions, a remediation queue, and a full package browser preview in Export. | Add richer network component editing, clickable/editable diagram nodes, and richer validation beyond package preflight and queue feedback. | Phase 5 and Phase 6 |
| Gate 4: User Experience | Partial | Native drag/drop supports single and multi-select assignment with confirmation modal, drop highlighting, row tags, row-level unassign, readiness-chip routing, explicit checkbox/drop-zone accessible labels, keyboard-operable assignment buttons, guided remediation queue routing, bulk high-confidence suggestion review, and Playwright coverage for keyboard navigation and review-chip routing across Chromium, Firefox, and WebKit. | Run the [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md), then complete broader screen-reader/manual accessibility review, mobile/tablet review, and large-workbook UX/performance tests beyond the workshop sample. | Phase 6 |
| Gate 5: Quality and Testing | Partial | Verified: Python compile/full pytest, Carbon TypeScript, Jest, multi-browser Playwright smoke, handoff parity fixtures, real-workbook operational overlay parity, planning-state JSON import/export, backend preflight endpoint/UI feedback and next-step actions, API ZIP inventory guard, UI/backend ZIP inventory drift guard, export readiness queue tests, sample-workbook summary performance guards, optional private customer-workbook summary guard hook, and workshop state/assignment/preview/ZIP performance guards. | Add broader e2e coverage for failure paths, captured evidence from private customer-scale workbooks, accessibility automation, and more real-workbook parity fixtures. | Phase 5-6 |
| Gate 6: Production Readiness | Partial | Docker Compose starts Streamlit, API, Carbon UI, and Postgres; local health/log checks are documented; Carbon healthcheck reports healthy; persistence warning exists; user manual now documents the Carbon checkpoint and production boundary; promotion/cutover guide now documents staged rollout and rollback; operations runbook documents backup/recovery, monitoring/logging, incident response, support ownership matrix, rollback authority, a successful local restore drill, and local monitoring evidence. | Wire hosted-runtime alerts/log sinks and fill in named production support owners before promotion. | Phase 6 |

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
- Python pytest: 355 passed, 1 skipped
- Carbon TypeScript: 0 errors
- Carbon Jest: 171 passed
- Carbon Playwright: 24 passed across Chromium, Firefox, and WebKit
- Docker Compose health: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright coverage includes workbook upload, project save/load, subnet
drag/drop, multi-select subnet/security/storage/wave drops, row-level unassign,
autosave reload, persistence outage warning display, Export preflight blocker
routing to remediation review, Export remediation queue high-confidence bulk
fix application, suggestion audit/undo, Export preview/download/save-before-export
failure handling, package preview handoff CSV switching/download, keyboard
navigation, keyboard assignment through explicit Assign buttons,
readiness-chip review routing, drag/drop accessibility labels, row checkbox
accessible names, package preview close behavior, and temporary smoke-project
cleanup across Chromium, Firefox, and WebKit. The suite runs with one worker because the smoke tests share the
same FastAPI/Postgres backend during project save/load and cleanup.

The Python parity suite now includes Streamlit-vs-Carbon single-VM, edge-case,
multi-VM, workshop real-workbook subset, workshop operational edge subset, and
sample-workbook operational overlay comparisons, including real-workbook
disk/partition mapping parity and exact non-preflight handoff file parity for the sample workbook;
manifest handoff references; sample-workbook handoff contract assertions;
sample-workbook API ZIP inventory and handoff CSV payload
verification; API preview-vs-ZIP file/content parity; and a Carbon Export UI
inventory drift test against backend ZIP
inventory constants.
The Python suite also guards summary parsing across both checked-in real sample
workbooks, supports optional private customer-workbook summary guards through
`CARBON_PERF_CUSTOMER_WORKBOOKS`, and guards workshop project state save/load,
VM assignment update, Carbon Terraform preview, and ZIP generation performance.

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

## Phase 6 Backlog

- Accessibility audit, including keyboard-only workflows and DnD alternatives, using the [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md).
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
experience, Phase 4 workflow surfaces, and a substantial handoff parity path.
The production Streamlit app remains the supported UI until Carbon has deeper
real-workbook parity evidence, broader accessibility/browser/performance
coverage, and production support documentation.

**Next review trigger**: Re-run this gate review after additional real-workbook
edge fixtures, additional customer-scale performance validation, and broader
accessibility coverage are complete.
