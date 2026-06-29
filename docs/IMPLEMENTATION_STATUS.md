# Carbon UI Integration - Implementation Status

## Overview

This document tracks the implementation status of the Carbon UI integration with
the RVTools to IBM Cloud migration tool.

**Last Updated**: 2026-06-29  
**Current Phase**: Carbon UI Phase 4 started with Remediation Tracker parity  
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
- [ ] Decision audit and complete handoff parity

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
- Jest: 129 tests passing
- Playwright: 1 browser smoke passing
- Docker Compose: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright smoke covers workbook upload, project save/load, subnet
drag/drop, multi-select security/storage/wave drops, autosave reload, and cleanup
of temporary smoke projects.

---

## Current Limitations

Carbon is not ready to replace Streamlit yet. Remaining gaps:

1. **Feature parity**
   - Wave Planning full Streamlit bulk-assignment and handoff parity
   - Remediation Tracker full Streamlit finding/category and handoff parity
   - Image Import Planning full handoff/export parity
   - Migration Ops full handoff/export parity
   - Decision audit and full CSV/handoff parity

2. **Production readiness**
   - Large-workbook performance benchmark
   - Accessibility audit
   - Full browser coverage beyond the smoke path
   - User documentation for Carbon-specific workflows
   - Promotion/cutover guide from Streamlit to Carbon

3. **UX polish**
   - Editable network diagram nodes
   - Richer validation and preflight feedback in Carbon
   - Terraform preview inside the UI

---

## Roadmap

### Promotion Gate Review
- [x] Review against `docs/carbon-react-ui-strategy.md`
- [ ] Run full repo validation
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
- [ ] Decision audit

### Phase 5: Complete Handoff Package Parity
- [ ] All CSV exports
- [ ] Migration manifest parity
- [ ] Preflight parity
- [ ] Planning-state import/export parity

### Phase 6: Polish and Promotion
- [ ] Accessibility audit
- [ ] Performance benchmark
- [ ] Documentation
- [ ] User acceptance testing
- [ ] Go/no-go promotion decision

---

## Related Documentation

- [Carbon React UI Strategy](./carbon-react-ui-strategy.md)
- [Carbon Promotion Gate Review](./carbon-promotion-gate-review.md)
- [Carbon UI Integration Summary](./carbon-ui-integration-summary.md)
- [Carbon Network Schema Spec](./carbon-network-schema-spec.md)
- [Carbon Integration Diagrams](./carbon-integration-diagrams.md)
- [Terraform Modular Implementation](./TERRAFORM_MODULAR_IMPLEMENTATION.md)
