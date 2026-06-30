# Carbon Promotion Gate Review

**Review date**: 2026-06-29  
**Reviewed state**: Carbon UI Phases 1-3 implemented on
`feature/carbon-ui-network-planning-phase1`  
**Recommendation**: Do not promote Carbon to production yet. Continue running
Streamlit as the supported UI while Carbon enters Phase 4 feature-parity work.

## Executive Summary

Carbon has crossed the prototype viability threshold: upload, persistence,
network planning, Terraform ZIP export, drag-and-drop assignment, autosave, and
Docker Compose runtime are implemented and verified.

Carbon has not crossed the production replacement threshold. The remaining gaps
are mostly feature parity and production readiness: Streamlit-only planning
workflows, accessibility, large-workbook performance, broader browser coverage,
and complete handoff parity.

## Gate Matrix

| Gate | Status | Evidence | Remaining Work | Recommended Phase |
| --- | --- | --- | --- | --- |
| Gate 1: Core Functionality | Pass | Workbook upload calls FastAPI summary; project save/load uses Postgres; drag/drop assigns subnet/security/storage/wave; Terraform ZIP export works from saved Carbon network plans. | Keep adding regression coverage as Phase 4 features land. | Maintenance |
| Gate 2: Feature Parity | Fail | Streamlit remains the only UI with full wave planning, remediation tracker, image import planning, migration ops, decision audit, and complete handoff/CSV parity. | Implement Streamlit-only workflows in Carbon and verify parity against current Streamlit behavior. | Phase 4 and Phase 5 |
| Gate 3: Network Planning | Partial | Carbon supports VPC/subnet/security/storage/wave/network component planning, saved network plans, diagram display, and Terraform generation. | Add richer network component editing, clickable/editable diagram nodes, Carbon-side preflight feedback, and Terraform preview. | Phase 5 and Phase 6 |
| Gate 4: User Experience | Partial | Native drag/drop supports single and multi-select assignment with confirmation modal, drop highlighting, row tags, and row-level unassign. | Run accessibility audit, keyboard-only DnD review, mobile/tablet review, and large-workbook UX/performance tests. | Phase 6 |
| Gate 5: Quality and Testing | Partial | Verified: Python compile, full pytest, Terraform strict validation, Carbon TypeScript, Jest, Playwright smoke, Docker Compose health. | Add broader e2e coverage for failure paths, multiple browsers, large workbooks, accessibility automation, and Phase 4 workflows. | Phase 4-6 |
| Gate 6: Production Readiness | Partial | Docker Compose starts Streamlit, API, Carbon UI, and Postgres; Carbon healthcheck reports healthy; persistence warning exists. | Add Carbon user docs, operational monitoring/logging review, backup/recovery guidance, promotion/cutover guide, and support posture. | Phase 6 |

## Validation Evidence

Latest completed validation:

```bash
make compile
venv/bin/python -m pytest -ra --tb=short
venv/bin/python scripts/validate_terraform_package.py --init-validate
cd prototype/carbon-ui
npx tsc --noEmit --incremental false
npm test -- --runInBand
npm run test:e2e
```

Observed results:
- Python compile: passed
- Python pytest: 327 passed
- Terraform strict init validation: passed with network access to Terraform Registry
- Carbon TypeScript: 0 errors
- Carbon Jest: 129 passed
- Carbon Playwright smoke: passed
- Docker Compose health: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright smoke covers workbook upload, project save/load, subnet
drag/drop, multi-select security/storage/wave drops, autosave reload, and
temporary smoke-project cleanup.

## Phase 4 Backlog

Priority order:

1. **Remediation Tracker**
   - Initial Carbon workflow exists with generated readiness backlog rows,
     editable owner/status/due-date/notes fields, CSV import/export, and
     project-state persistence in both Carbon and Streamlit-compatible tracker
     shapes.
   - Remaining: full Streamlit finding/category parity and remediation state in
     complete export/handoff parity checks.

2. **Image Import Planning**
   - Initial Carbon workflow exists with inferred source-image grouping,
     editable import status, target catalog ID, estimated import time, notes,
     CSV import/export, project-state persistence, and IMG readiness-chip
     routing.
   - Remaining: full handoff/export parity and verification that custom image
     ID behavior remains compatible with generated Terraform.

3. **Migration Ops**
   - Initial Carbon workflow exists with VM-level cutover readiness, summaries
     by wave and cutover group, blockers from planning gaps, readiness signals,
     unresolved remediation, image import state, and cutover-readiness CSV
     export.
   - Remaining: full handoff/export parity against Streamlit package outputs.

4. **Wave Planning Parity**
   - Initial Carbon workflow now supports per-VM wave, cutover group, owner,
     application, priority, dependency group, CSV import/export, completion
     metrics, and application/dependency conflict detection.
   - Remaining: Streamlit bulk-assignment ergonomics and full handoff parity.

5. **Decision Audit and Handoff Parity**
   - Add override/decision audit surfaces.
   - Verify Carbon-generated ZIP contents against Streamlit package contents,
     including CSVs, planning state, runbook, preflight reports, and README.

## Phase 5 Backlog

- Use [Carbon Handoff Parity](carbon-handoff-parity.md) as the package
  inventory and implementation tracker.
- Complete CSV export parity.
- Complete migration manifest parity.
- Complete preflight parity in Carbon UI.
- Add Carbon planning-state import/export.
- Add Terraform preview and package contents preview.

## Phase 6 Backlog

- Accessibility audit, including keyboard-only workflows and DnD alternatives.
- Performance benchmark for large RVTools workbooks.
- Multi-browser e2e coverage.
- Carbon-specific user documentation.
- Production support model, monitoring/logging review, and backup/recovery notes.
- Streamlit-to-Carbon migration and cutover guide.

## Go / No-Go

**Current decision**: No-go for replacing Streamlit.

**Rationale**: Carbon now proves the core architecture and differentiated DnD
experience, but the production Streamlit app still has critical planning
workflows and handoff surfaces that Carbon does not yet reproduce.

**Next review trigger**: Re-run this gate review after Phase 4 feature parity
work lands and the validation suite includes those workflows.
