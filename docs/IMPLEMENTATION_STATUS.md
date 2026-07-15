# Carbon UI Integration - Implementation Status

## Overview

This document tracks the implementation status of the Carbon UI integration with
the RVTools to IBM Cloud migration tool.

**Last Updated**: 2026-07-10
**Current Phase**: Carbon UI Phase 6 promotion-readiness evidence and polish
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
- [x] Remediation tracker persists through project-state save/load and autosave, including Streamlit-compatible blocker metadata
- [x] Remediation CSV export is available from the Carbon workflow
- [x] Remediation backlog coverage includes image, migration, memory, and network blocker categories
- [x] Remediation CSV import matches by blocker ID or Streamlit fallback signature, preserves blocker metadata, skips unmatched rows, and normalizes unknown statuses
- [x] VM readiness chips are self-describing and route non-ready signals to review workflows
- [x] Image Import Planning workflow with grouped rows, owner rollups, import status, catalog ID, estimated time, notes, guarded CSV import/export, and project persistence
- [x] Migration Ops cutover readiness dashboard with wave/cutover summaries, Streamlit-compatible remediation metadata, and CSV export
- [x] Wave Planning per-VM fields, bulk assignment, CSV import/export including unmatched-row skips, completion metrics, conflict detection, and dedicated edit coverage for wave/cutover/owner/application/priority/dependency fields
- [x] VM Overrides workflow with profile/storage override reasons, exclusion reasons, decision-audit CSV export, project persistence, and Assignment row routing
- [x] Carbon Terraform ZIP includes `decision-audit.csv` with override reasons and pricing impact columns
- [x] Carbon Terraform ZIP includes state-native handoff files: `remediation-backlog.csv`, `image-import-plan.csv`, `cutover-readiness.csv`, and `planning-state.json`
- [x] Carbon Terraform ZIP includes the remaining handoff artifact inventory: manifest, assessment quality, preflight, pricing diagnostics, mapping/readiness CSVs, image import tfvars, and runbook
- [x] Carbon intake preserves hidden workbook details for handoff fidelity, including disk, partition, NIC, memory, pricing, and readiness-finding fields
- [x] Sample-workbook Carbon handoff contract coverage validates decision audit, remediation backlog, image import plan, cutover readiness, planning-state fields, and remediation summary behavior
- [x] Sample-workbook API ZIP inventory coverage verifies full handoff inventory, Carbon modular Terraform files, and documented Carbon-only `network-plan.json`
- [x] First edge-case Streamlit-vs-Carbon fixture comparison covers multi-NIC, disk, partition, memory-readiness, and readiness-finding CSV fidelity
- [x] Multi-VM Streamlit-vs-Carbon fixture comparison covers mixed waves, profile/storage overrides, exclusions, remediation, image import summaries, custom image tfvars, cutover readiness, and planning-state parity
- [x] Workshop real-workbook subset comparison covers unknown-network, low-confidence assessment-quality, missing-vMemory, image-import, and cutover-readiness parity
- [x] Workshop real-workbook operational edge subset comparison covers overrides, exclusions, remediation, image import status, wave/cutover metadata, unknown-network readiness, and exact operational handoff parity
- [x] Sample-workbook operational overlay comparison covers real workbook rows with wave/cutover, remediation, image import, profile/storage overrides, planning-state parity, and exact non-preflight handoff file parity
- [x] Carbon Export workflow shows package parity status, corrected modular Terraform inventory, and documented Carbon-only ZIP additions before download
- [x] Carbon Export UI inventory is backed by a shared JSON contract and tested against the backend ZIP inventory constants
- [x] Carbon Export workflow supports planning-state JSON export/import for offline handoff and reload review
- [x] Carbon Export workflow can save the latest plan, run backend package preflight, and display blocker/warning findings before ZIP download
- [x] Carbon Export preflight findings provide safe next-step actions that route users to the relevant workflow and VM for remediation, scope, image import, network placement, security, storage, or override review
- [x] Carbon Export remediation queue prioritizes backend preflight blockers, local planning gaps, subnet CIDR gaps, Terraform naming cleanup, and warnings
- [x] Carbon Export `Resolve next issue` and queue-level `Review issue` actions share the same routing model so users land in the correct workflow with the relevant VM or planning context selected
- [x] Carbon Export can infer subnet, security group, storage/IOPS, and wave fixes from VM naming, application/network/owner/cutover metadata, existing assignments, and matching bucket purpose
- [x] Carbon Export supports individual suggested fixes, high-confidence bulk selection, selected bulk application, suggestion audit entries, and undo
- [x] Carbon Export readiness report downloads checklist, planning gaps, preflight findings, suggestion audit, and package inventory as JSON for review meetings
- [x] Carbon Terraform package preview includes in-page browsing, package-section filtering, handoff CSV filtering, selected-file download, and explicit close behavior
- [x] Sample-workbook performance guard covers FastAPI summary parsing across both checked-in real samples, plus workshop project state save/load, VM assignment updates, Terraform preview, and ZIP generation
- [x] Generated 3,000-row Carbon API performance guard covers project-state save/load and VM assignment updates
- [x] Generated 5,000-row Carbon UI performance guard covers VM Assignment search/sort and VM Overrides missing-reason filtering
- [x] Optional private customer-workbook summary performance fixture hook is documented and skipped unless `CARBON_PERF_CUSTOMER_WORKBOOKS` is set
- [x] Sanitized private-workbook evidence helper and template are documented for customer-scale timing capture without paths, filenames, VM names, IPs, owners, or application names; helper supports environment-driven input and ignored local output under `private-evidence/`
- [x] One sanitized local private-workbook timing capture is recorded: 168 assignment rows parsed in 1.716 seconds against a 45-second threshold
- [x] Carbon accessibility and UAT results template is documented for manual review evidence, issue severity tracking, accepted pilot gaps, and promotion sign-off
- [x] Focused automated Carbon accessibility/UAT pass recorded for VM Overrides and Export Readiness, with table naming and package-preview selected-state issues fixed
- [x] Focused automated Carbon accessibility/UAT pass recorded for Network Plan component editing and local validation findings
- [x] Carbon manual UAT runbook packet documented for reviewer setup, workflow sequence, evidence capture, pass/fail rules, and sensitive-data guardrails
- [ ] Complete workbook-detail fidelity and parity comparison coverage

---

## Verification Status

Latest verified commands:

```bash
cd prototype/carbon-ui
npx tsc --noEmit
npm test -- --runInBand
CARBON_BASE_URL=http://localhost:3000 npx playwright test
```

Results:
- Python compile: passed
- Python pytest: 355 passed, 1 skipped
- TypeScript: 0 errors
- Jest: 174 tests passing
- Playwright: 27 tests passing across Chromium, Firefox, and WebKit
- Docker Compose: API, Streamlit, Carbon UI, and Postgres healthy

The Playwright smoke covers workbook upload, project save/load, subnet
drag/drop, multi-select subnet/security/storage/wave drops, row-level unassign
persistence, drag/drop accessibility labels, autosave reload, persistence outage
warning display, Export preflight blocker routing to remediation review, Export
remediation queue high-confidence bulk fix application, suggestion audit/undo,
profile override save/load/export parity, bulk override missing-reason cleanup,
preview/download/save-before-export failure handling, package preview handoff
CSV switching/download, package preview close behavior, keyboard navigation,
readiness-chip review routing, and cleanup of temporary smoke projects across
Chromium, Firefox, and WebKit.

The Python parity suite includes `tests/test_carbon_handoff_parity.py`, which
now covers Streamlit-vs-Carbon fixture parity, an edge-case mapping/readiness
fixture for multi-NIC and disk/partition fidelity, a multi-VM operational
fixture for overrides, exclusions, remediation, image import, cutover readiness,
manifest handoff references, and planning-state parity, a workshop real-workbook subset fixture for
unknown-network, storage mapping empty-state, and low-confidence
assessment-quality behavior, a workshop real-workbook operational edge fixture
for overrides, exclusions, remediation, image import, wave/cutover metadata, and
exact operational handoff parity, and sample-workbook operational overlays for
wave/cutover, remediation, image import, profile/storage overrides, rich
disk/partition mapping, exact non-preflight handoff files, Carbon preflight
superset checks, and planning-state parity, plus
sample-workbook Carbon handoff contract fields for `decision-audit.csv`,
`remediation-backlog.csv`, `image-import-plan.csv`, `cutover-readiness.csv`,
and `planning-state.json`. It also verifies the sample-workbook API ZIP
inventory and key handoff CSV payloads from
`POST /api/projects/{project_id}/terraform`, verifies
`POST /api/projects/{project_id}/terraform/preview` matches the generated ZIP
file paths and representative file contents, and guards the
sample-workbook summary parsing across both checked-in real samples, supports
optional private customer-workbook summary guards via
`CARBON_PERF_CUSTOMER_WORKBOOKS`, and guards workshop project state save/load,
VM assignment update, Terraform preview, and ZIP paths against performance
regressions. It also guards generated 3,000-row Carbon API project-state
save/load and VM assignment updates. The Carbon Jest suite guards generated
5,000-row UI filtering for VM Assignment search/sort and VM Overrides
missing-reason cleanup.

---

## Current Limitations

Carbon is not ready to replace Streamlit yet. Remaining gaps:

1. **Feature parity**
   - Broader Streamlit-vs-Carbon fixture comparison coverage for full handoff
     packages and edge-case workbooks

2. **Production readiness**
   - Captured customer-scale large-workbook performance evidence from private fixtures
   - Broader screen-reader/manual accessibility audit using the checklist and results template
   - Browser-specific coverage beyond the current smoke and failure-path suite
   - Hosted-runtime alerting/log sink configuration
   - Hosted-runtime restore drill validation
   - Named production support owners and rollback authority

3. **UX polish**
   - Editable network diagram nodes
   - Richer validation beyond package preflight and remediation queue feedback

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
- [x] Wave Planning bulk-assignment and handoff parity
- [x] Remediation Tracker full finding/category and handoff parity
- [x] Image Import Planning initial Carbon workflow
- [x] Image Import Planning full handoff/export parity
- [x] Migration Ops initial Carbon workflow
- [x] Migration Ops full handoff/export parity
- [x] Decision audit initial Carbon workflow
- [x] Decision audit pricing impact and handoff ZIP parity
- [x] State-native Carbon handoff ZIP files
- [x] Full handoff artifact inventory in Carbon ZIP
- [x] Initial Streamlit-vs-Carbon handoff fixture comparison coverage
- [x] Real workbook operational overlay fixture coverage
- [x] Workshop real-workbook operational edge fixture coverage
- [x] Sample-workbook summary plus workshop state/assignment/preview/ZIP performance guard
- [x] Generated 3,000-row Carbon API project-state save/load/update performance guard
- [x] Generated 5,000-row Carbon UI Assignment/Overrides filtering performance guard
- [ ] Additional real-workbook edge fixture coverage

### Phase 5: Complete Handoff Package Parity
- [ ] All CSV exports
- [x] Migration manifest references full operational handoff files
- [x] Backend package preflight endpoint and Carbon Export UI feedback
- [x] Carbon Export workflow package browser preview before ZIP download
- [x] Carbon Export package preview selected-file download and handoff CSV filter
- [x] Planning-state JSON export/import in Carbon Export workflow
- [x] Carbon Export readiness report download
- [x] Carbon Export remediation queue with routing, suggested fixes, bulk application, audit, and undo

### Phase 6: Polish and Promotion
- [x] Initial keyboard/accessibility E2E audit for Carbon assignment flow
- [ ] Broader screen-reader/manual accessibility audit
- [x] Multi-browser Playwright smoke coverage for Chromium, Firefox, and WebKit
- [x] Browser failure-path coverage for persistence outage warning, Export preflight blocker routing, preview/download failures, and save-before-export failure
- [x] Sample-workbook summary plus workshop state/assignment/preview/ZIP performance guard
- [x] Generated 3,000-row Carbon API project-state save/load/update performance guard
- [x] Generated 5,000-row Carbon UI Assignment/Overrides filtering performance guard
- [x] Safer private-workbook evidence helper path verified with ignored sanitized output
- [x] First sanitized private-workbook evidence run recorded
- [x] Export readiness workflow user-manual documentation
- [x] Carbon accessibility and UAT checklist created
- [x] Carbon accessibility and UAT results/sign-off template created
- [x] Carbon manual UAT runbook created
- [x] Focused automated accessibility/UAT result recorded for VM Overrides and Export Readiness
- [x] Focused automated accessibility/UAT result recorded for Network Plan component editing and validation
- [ ] Additional customer-scale performance benchmark fixtures
- [x] Carbon checkpoint documented in user manual
- [x] Promotion/cutover documentation
- [x] Backup/recovery and monitoring/logging runbook
- [x] Local Postgres restore drill and artifact archive verification
- [x] Local health/log access verification
- [x] Support ownership and rollback authority model
- [ ] User acceptance testing
- [ ] Go/no-go promotion decision

---

## Related Documentation

- [Carbon React UI Strategy](./carbon-react-ui-strategy.md)
- [Carbon Promotion Gate Review](./carbon-promotion-gate-review.md)
- [Carbon Manual UAT Runbook](./carbon-manual-uat-runbook.md)
- [Carbon Accessibility and UAT Checklist](./carbon-accessibility-uat-checklist.md)
- [Carbon Accessibility and UAT Results Template](./carbon-accessibility-uat-results-template.md)
- [Carbon Accessibility and UAT Focused Results - 2026-07-10](./carbon-accessibility-uat-results-2026-07-10-focused.md)
- [Carbon Accessibility and UAT Network Plan Focused Results - 2026-07-15](./carbon-accessibility-uat-results-2026-07-15-network-plan.md)
- [Carbon Private Workbook Evidence - 2026-07-10](./carbon-private-workbook-evidence-2026-07-10.md)
- [Carbon Promotion and Cutover Guide](./carbon-promotion-cutover-guide.md)
- [Carbon Operations Runbook](./carbon-operations-runbook.md)
- [Carbon Handoff Parity](./carbon-handoff-parity.md)
- [Target Platform Roadmap](./target-platform-roadmap.md)
- [Carbon UI Integration Summary](./carbon-ui-integration-summary.md)
- [Carbon Network Schema Spec](./carbon-network-schema-spec.md)
- [Carbon Integration Diagrams](./carbon-integration-diagrams.md)
- [Terraform Modular Implementation](./TERRAFORM_MODULAR_IMPLEMENTATION.md)
