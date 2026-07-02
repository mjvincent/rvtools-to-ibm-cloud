# Carbon UI Integration - Implementation Status

## Overview

This document tracks the implementation status of the Carbon UI integration with
the RVTools to IBM Cloud migration tool.

**Last Updated**: 2026-07-02  
**Current Phase**: Carbon UI Phase 4 feature-parity workflows in progress  
**Production UI**: Streamlit remains production until Carbon closes the remaining
feature-parity and production-readiness gaps.

---

## Completed Implementation

### Foundation and Backend

**Network Planning Schema**
- [x] TypeScript schema in `prototype/carbon-ui/types/network-planning.ts`
- [x] CIDR and network validation in `prototype/carbon-ui/utils/network-validation.ts`
- [x] Python dataclasses in `models/network_planning.py`
- [x] Pydantic validation schemas in `prototype/api/schemas.py`

**FastAPI Endpoints**
- [x] `POST /api/projects/{id}/network-plan`
- [x] `GET /api/projects/{id}/network-plan`
- [x] `PUT /api/projects/{id}/vm-assignments`
- [x] `POST /api/projects/{id}/terraform`
- [x] Postgres-backed project CRUD and project-state persistence

**Terraform Renderer**
- [x] Modular Carbon renderer supports VPCs, subnets, security groups, storage,
  waves, network components, and VM assignments
- [x] Terraform ZIP generation works from saved Carbon network plans
- [x] Direct API smoke verified ZIP generation with `application/zip` response

### Carbon UI Phase 1: Component Architecture

- [x] `app/page.tsx` is a thin shell around the Carbon workbench
- [x] 8 workflow tabs live under `components/workflows/`
- [x] Shared primitives live under `components/ui/`
- [x] Shared state lives in `store/AppContext.tsx`
- [x] API client lives in `hooks/useApi.ts`
- [x] React component tests run with Jest jsdom and Testing Library

### Carbon UI Phase 2: API Wiring and Export

- [x] Workbook intake calls the real upload/summary API
- [x] Project create/update/load/list/delete is wired to FastAPI/Postgres
- [x] Full network-plan save/load is wired
- [x] VM assignment updates are debounced and persisted
- [x] Dirty-state autosave persists active projects
- [x] Persistence-unavailable warning is shown when API/Postgres is unavailable
- [x] Export tab saves latest network plan and downloads Terraform ZIP
- [x] Docker Compose Carbon UI healthcheck uses Node `fetch()` and reports healthy

### Carbon UI Phase 3: Drag-and-Drop Assignment

- [x] Native drag/drop components under `components/dnd/`
- [x] `DraggableVmRow`
- [x] `SubnetDropZone`
- [x] `PlacementModal`
- [x] Single VM drag
- [x] Multi-select drag
- [x] Drop targets for subnet, security, storage, and wave modes
- [x] Confirmation modal before assignment
- [x] Row-level unassign action for the active assignment mode
- [x] Subnet and wave Carbon `Tag` chips in VM rows
- [x] DnD updates flow through existing autosave and VM debounce paths
- [x] Drop zones, assignment buttons, and VM row selectors expose descriptive accessible labels
- [x] Playwright smoke verifies single drag, multi-select drag, unassign persistence, autosave reload, and drag/drop accessibility labels

### Carbon UI Phase 4: Streamlit Feature Parity

- [x] Remediation Backlog workflow added to Carbon navigation
- [x] Remediation rows derive from Carbon VM readiness signals
- [x] Owner, status, due date, and notes are editable in Carbon state
- [x] Remediation tracker persists through project-state save/load and autosave
- [x] Remediation CSV export is available from the Carbon workflow
- [x] Remediation CSV import matches by blocker ID or Streamlit fallback signature
- [x] VM readiness chips are self-describing and route non-ready signals to review workflows
- [x] Image Import Planning workflow with grouped rows, import status, catalog ID, CSV import/export, and project persistence
- [x] Migration Ops cutover readiness dashboard with wave/cutover summaries and CSV export
- [x] Wave Planning per-VM fields, CSV import/export, completion metrics, and conflict detection
- [x] VM Overrides workflow with profile/storage override reasons, exclusion reasons, decision-audit CSV export, project persistence, and Assignment row routing
- [x] Carbon Terraform ZIP includes `decision-audit.csv` with override reasons and pricing impact columns
- [x] Carbon Terraform ZIP includes state-native handoff files: `remediation-backlog.csv`, `image-import-plan.csv`, `cutover-readiness.csv`, and `planning-state.json`
- [x] Carbon Terraform ZIP includes the remaining handoff artifact inventory: manifest, assessment quality, preflight, pricing diagnostics, mapping/readiness CSVs, image import tfvars, and runbook
- [x] Carbon intake preserves hidden workbook details for handoff fidelity, including disk, partition, NIC, memory, pricing, and readiness-finding fields
- [x] Sample-workbook Carbon handoff contract coverage validates decision audit, remediation backlog, image import plan, cutover readiness, and planning-state fields
- [x] Sample-workbook API ZIP inventory coverage verifies full handoff inventory, Carbon modular Terraform files, and documented Carbon-only `network-plan.json`
- [x] First edge-case Streamlit-vs-Carbon fixture comparison covers multi-NIC, disk, partition, memory-readiness, and readiness-finding CSV fidelity
- [x] Multi-VM Streamlit-vs-Carbon fixture comparison covers mixed waves, profile/storage overrides, exclusions, remediation, image import, cutover readiness, and planning-state parity
- [x] Workshop real-workbook subset comparison covers unknown-network, low-confidence assessment-quality, missing-vMemory, image-import, and cutover-readiness parity
- [x] Sample-workbook operational overlay comparison covers real workbook rows with wave/cutover, remediation, image import, profile/storage overrides, and planning-state parity
- [x] Carbon Export workflow shows package parity status, corrected modular Terraform inventory, and documented Carbon-only ZIP additions before download
- [x] Carbon Export UI inventory is backed by a shared JSON contract and tested against the backend ZIP inventory constants
- [x] Carbon Export workflow supports planning-state JSON export/import for offline handoff and reload review
- [x] Carbon Export workflow can save the latest plan, run backend package preflight, and display blocker/warning findings before ZIP download
- [x] Workshop large-workbook performance guard covers FastAPI summary parsing and Carbon Terraform ZIP generation
- [ ] Complete workbook-detail fidelity and parity comparison coverage

---

## Verification Status

Latest verified commands:

```bash
cd prototype/carbon-ui
npx tsc --noEmit --incremental false
npm test -- --runInBand
npm run test:e2e
```

Results:
- TypeScript: 0 errors
- Jest: 138 tests passing
- Playwright: 1 browser smoke passing
- Python pytest: 347 tests passing
- Docker Compose: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright smoke covers workbook upload, project save/load, subnet
drag/drop, multi-select subnet/security/storage/wave drops, row-level unassign
persistence, drag/drop accessibility labels, autosave reload, and cleanup of
temporary smoke projects.

The Python parity suite includes `tests/test_carbon_handoff_parity.py`, which
now covers Streamlit-vs-Carbon fixture parity, an edge-case mapping/readiness
fixture for multi-NIC and disk/partition fidelity, a multi-VM operational
fixture for overrides, exclusions, remediation, image import, cutover readiness,
and planning-state parity, a workshop real-workbook subset fixture for
unknown-network and low-confidence assessment-quality behavior, and
sample-workbook operational overlays for wave/cutover, remediation, image
import, profile/storage overrides, and planning-state parity, plus
sample-workbook Carbon handoff contract fields for `decision-audit.csv`,
`remediation-backlog.csv`, `image-import-plan.csv`, `cutover-readiness.csv`,
and `planning-state.json`. It also verifies the sample-workbook API ZIP
inventory from `POST /api/projects/{project_id}/terraform` and guards the
workshop workbook summary/ZIP path against performance regressions.

---

## Current Limitations

Carbon is not ready to replace Streamlit yet. Remaining gaps:

1. **Feature parity**
   - Wave Planning full Streamlit bulk-assignment and handoff parity
   - Remediation Tracker full Streamlit finding/category and handoff parity
   - Image Import Planning full handoff/export parity
   - Migration Ops full handoff/export parity
   - Broader Streamlit-vs-Carbon fixture comparison coverage for full handoff
     packages and edge-case workbooks

2. **Production readiness**
   - Broader large-workbook performance benchmark suite beyond the workshop sample
   - Accessibility audit
   - Full browser coverage beyond the smoke path
   - Promotion/cutover guide from Streamlit to Carbon

3. **UX polish**
   - Editable network diagram nodes
   - Richer validation beyond package preflight feedback
   - Terraform preview inside the UI

---

## Roadmap

### Promotion Gate Review
- [x] Review against `docs/carbon-react-ui-strategy.md`
- [x] Run current repo validation: Python pytest, Carbon TypeScript, Carbon Jest, and Carbon Playwright smoke
- [x] Document gate pass/fail status in
  `docs/carbon-promotion-gate-review.md`
- [x] Start Phase 4 before additional UX/accessibility polish

### Phase 4: Streamlit Feature Parity
- [x] Remediation Tracker initial Carbon workflow
- [x] Wave Planning initial parity workflow
- [ ] Wave Planning bulk-assignment and handoff parity
- [ ] Remediation Tracker full finding/category and handoff parity
- [x] Image Import Planning initial Carbon workflow
- [ ] Image Import Planning full handoff/export parity
- [x] Migration Ops initial Carbon workflow
- [ ] Migration Ops full handoff/export parity
- [x] Decision audit initial Carbon workflow
- [x] Decision audit pricing impact and handoff ZIP parity
- [x] State-native Carbon handoff ZIP files
- [x] Full handoff artifact inventory in Carbon ZIP
- [x] Initial Streamlit-vs-Carbon handoff fixture comparison coverage
- [x] Real workbook operational overlay fixture coverage
- [x] Workshop large-workbook performance guard
- [ ] Additional real-workbook edge fixture coverage

### Phase 5: Complete Handoff Package Parity
- [ ] All CSV exports
- [ ] Migration manifest parity
- [x] Backend package preflight endpoint and Carbon Export UI feedback
- [x] Planning-state JSON export/import in Carbon Export workflow

### Phase 6: Polish and Promotion
- [ ] Accessibility audit
- [x] Workshop large-workbook performance guard
- [ ] Broader performance benchmark suite
- [x] Carbon checkpoint documented in user manual
- [ ] Promotion/cutover documentation
- [ ] User acceptance testing
- [ ] Go/no-go promotion decision

---

## Related Documentation

- [Carbon React UI Strategy](./carbon-react-ui-strategy.md)
- [Carbon Promotion Gate Review](./carbon-promotion-gate-review.md)
- [Carbon Handoff Parity](./carbon-handoff-parity.md)
- [Carbon UI Integration Summary](./carbon-ui-integration-summary.md)
- [Carbon Network Schema Spec](./carbon-network-schema-spec.md)
- [Carbon Integration Diagrams](./carbon-integration-diagrams.md)
- [Terraform Modular Implementation](./TERRAFORM_MODULAR_IMPLEMENTATION.md)
