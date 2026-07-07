# Carbon Promotion Gate Review

**Review date**: 2026-07-02
**Reviewed state**: Carbon UI Phases 1-4 in progress on
`feature/carbon-ui-network-planning-phase1`  
**Recommendation**: Do not promote Carbon to production yet. Continue running
Streamlit as the supported UI while Carbon closes the remaining parity and
production-readiness gaps.

## Executive Summary

Carbon has crossed the prototype viability threshold and now covers the core
planning path: upload, persistence, network planning, drag-and-drop assignment,
autosave, VM overrides, Phase 4 planning workflow surfaces, Terraform ZIP
export, package parity status, and Docker Compose runtime are implemented and
verified.

Carbon has not crossed the production replacement threshold. The remaining gaps
are mostly production-hardening and deeper parity evidence: additional
real-workbook handoff fixture coverage, broader accessibility and browser
coverage, broader large-workbook performance coverage beyond the workshop
sample, production support posture, and a formal Streamlit-to-Carbon cutover
plan.

## Gate Matrix

| Gate | Status | Evidence | Remaining Work | Recommended Phase |
| --- | --- | --- | --- | --- |
| Gate 1: Core Functionality | Pass | Workbook upload calls FastAPI summary; project save/load uses Postgres; drag/drop assigns subnet/security/storage/wave; Terraform ZIP export works from saved Carbon network plans. | Keep maintaining regression coverage as parity work lands. | Maintenance |
| Gate 2: Feature Parity | Partial | Carbon now has workflow surfaces for wave planning, remediation backlog, image import planning, migration ops, VM overrides, decision audit, handoff ZIP files, and Streamlit-vs-Carbon fixture comparisons. | Add more real-workbook edge fixtures and close remaining Streamlit bulk/edge workflow gaps before promotion. | Phase 4 and Phase 5 |
| Gate 3: Network Planning | Partial | Carbon supports VPC/subnet/security/storage/wave/network component planning, saved network plans, diagram display, Terraform generation, package inventory parity status, backend package preflight feedback, safe preflight next-step actions, and a full package browser preview in Export. | Add richer network component editing, clickable/editable diagram nodes, and richer validation beyond package preflight. | Phase 5 and Phase 6 |
| Gate 4: User Experience | Partial | Native drag/drop supports single and multi-select assignment with confirmation modal, drop highlighting, row tags, row-level unassign, readiness-chip routing, and explicit checkbox/drop-zone accessible labels. | Run accessibility audit, keyboard-only DnD review, mobile/tablet review, and large-workbook UX/performance tests beyond the workshop sample. | Phase 6 |
| Gate 5: Quality and Testing | Partial | Verified: Python compile/full pytest, Carbon TypeScript, Jest, Playwright smoke, handoff parity fixtures, real-workbook operational overlay parity, planning-state JSON import/export, backend preflight endpoint/UI feedback and next-step actions, API ZIP inventory guard, UI/backend ZIP inventory drift guard, and workshop large-workbook summary/ZIP performance guard. | Add broader e2e coverage for failure paths, multiple browsers, additional large workbooks, accessibility automation, and more real-workbook parity fixtures. | Phase 4-6 |
| Gate 6: Production Readiness | Partial | Docker Compose starts Streamlit, API, Carbon UI, and Postgres; Carbon healthcheck reports healthy; persistence warning exists; user manual now documents the Carbon checkpoint and production boundary. | Add operational monitoring/logging review, backup/recovery guidance, promotion/cutover guide, and support posture. | Phase 6 |

## Validation Evidence

Latest completed validation:

```bash
make compile
venv/bin/python -m pytest -q
cd prototype/carbon-ui
npx tsc --noEmit --incremental false
npm test -- --runInBand
npm run test:e2e
```

Observed results:
- Python compile: passed
- Python pytest: 348 passed
- Carbon TypeScript: 0 errors
- Carbon Jest: 141 passed
- Carbon Playwright smoke: passed
- Docker Compose health: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright smoke covers workbook upload, project save/load, subnet
drag/drop, multi-select subnet/security/storage/wave drops, row-level unassign,
autosave reload, package preview handoff CSV switching/download, drag/drop accessibility
labels, row checkbox accessible names, and temporary smoke-project cleanup.

The Python parity suite now includes Streamlit-vs-Carbon single-VM, edge-case,
multi-VM, workshop real-workbook subset, and sample-workbook operational overlay
comparisons, including real-workbook disk/partition mapping parity;
manifest handoff references; sample-workbook handoff contract assertions;
sample-workbook API ZIP inventory and handoff CSV payload
verification; API preview-vs-ZIP file/content parity; and a Carbon Export UI
inventory drift test against backend ZIP
inventory constants.
The Python suite also guards workshop workbook summary parsing and Carbon
Terraform ZIP generation performance.

## Phase 4 Status

Current feature-parity status:

1. **Remediation Tracker**
   - Carbon workflow exists with generated readiness backlog rows,
     editable owner/status/due-date/notes fields, CSV import/export, and
     project-state persistence in both Carbon and Streamlit-compatible tracker
     shapes.
   - Handoff ZIP includes `remediation-backlog.csv`; multi-VM parity fixtures
     compare operational handoff behavior.
   - Remaining: more real-workbook finding/category edge coverage.

2. **Image Import Planning**
   - Carbon workflow exists with inferred source-image grouping,
     editable import status, target catalog ID, estimated import time, notes,
     CSV import/export, project-state persistence, and IMG readiness-chip
     routing.
   - Handoff ZIP includes `image-import-plan.csv`; multi-VM parity fixtures
     cover mixed import states.
   - Remaining: more real-workbook image grouping and custom-image ID edge
     coverage.

3. **Migration Ops**
   - Carbon workflow exists with VM-level cutover readiness, summaries
     by wave and cutover group, blockers from planning gaps, readiness signals,
     unresolved remediation, image import state, and cutover-readiness CSV
     export.
   - Handoff ZIP includes `cutover-readiness.csv`; multi-VM parity fixtures
     cover mixed waves, remediation, image import, and blocked readiness.
   - Remaining: more real-workbook cutover edge coverage.

4. **Wave Planning Parity**
   - Carbon workflow supports per-VM wave, cutover group, owner,
     application, priority, dependency group, CSV import/export, completion
     metrics, and application/dependency conflict detection.
   - Handoff parity fixtures cover mixed wave and cutover-group output.
   - Remaining: Streamlit bulk-assignment ergonomics and more real-workbook
     wave/cutover edge coverage.

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
   - Streamlit-vs-Carbon fixture coverage now includes a synthetic fixture,
     multi-NIC/disk/partition/memory/readiness edge fixture, multi-VM
     operational fixture, workshop real-workbook subset fixture,
     sample-workbook operational overlay fixture, sample-workbook contract
     assertions, API ZIP inventory verification, Export UI/backend inventory
     drift protection, and workshop workbook performance coverage for summary
     parsing and Terraform ZIP generation.
   - Remaining: additional real-workbook edge fixtures and promotion-gate
     evidence for large or unusual customer workbooks.

## Phase 5 Backlog

- Use [Carbon Handoff Parity](carbon-handoff-parity.md) as the package
  inventory and implementation tracker.
- Add additional real-workbook Streamlit-vs-Carbon fixture comparisons.
- Improve any workbook-derived source metadata gaps found by those fixtures.
- Extend Carbon-side preflight feedback with optional safe autofill for low-risk findings.
- Extend planning-state reload coverage through Playwright and user acceptance.

## Phase 6 Backlog

- Accessibility audit, including keyboard-only workflows and DnD alternatives.
- Broader performance benchmark suite for large RVTools workbooks.
- Multi-browser e2e coverage.
- Keep Carbon-specific user documentation current as promotion criteria change.
- Production support model, monitoring/logging review, and backup/recovery notes.
- Streamlit-to-Carbon migration and cutover guide.

## Go / No-Go

**Current decision**: No-go for replacing Streamlit.

**Rationale**: Carbon now proves the core architecture, differentiated DnD
experience, Phase 4 workflow surfaces, and a substantial handoff parity path.
The production Streamlit app remains the supported UI until Carbon has deeper
real-workbook parity evidence, broader accessibility/browser/performance
coverage, and production support documentation.

**Next review trigger**: Re-run this gate review after additional real-workbook
edge fixtures, broader large-workbook performance validation, and broader
accessibility coverage are complete.
