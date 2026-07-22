# Carbon/React UI Strategy

## Decision

Keep Streamlit as the production workbench while developing the Carbon/React
interface as a parallel prototype under `prototype/carbon-ui`.

Do not fork the repository or maintain a second application copy. The Carbon UI
must use shared backend services and migration logic through the FastAPI layer
instead of duplicating parser, readiness, pricing, planning, or export logic.

## GitHub Hygiene

- Use feature branches for Carbon work, such as
  `codex/carbon-enterprise-prototype-track`.
- Keep Streamlit production changes and Carbon prototype changes separable in
  commits when practical.
- Keep Carbon code under `prototype/carbon-ui`.
- Keep the shared API under `prototype/api` until it is promoted to a first-class
  backend package.
- Keep Streamlit as the documented supported UI until the Carbon promotion gates
  are met.
- Avoid long-lived forks. Use pull requests, branch review, and small vertical
  slices.

## Current Architecture

- `app.py` and `streamlit_app/` remain the production UI.
- `prototype/api` provides FastAPI endpoints for health, workbook summary,
  projects, project state, artifacts, Carbon network plans, VM assignments, and
  Terraform ZIP generation.
- `prototype/carbon-ui` provides the experimental IBM Carbon Design System UI.
- `docker-compose.yml` starts Streamlit, FastAPI, Carbon UI, and Postgres
  together.
- Postgres stores project metadata and planning-state JSON.

## Carbon Prototype Scope

The Carbon UI should prove enterprise value through real workflow slices:

1. Upload an RVTools workbook and return estate/readiness summary.
2. Save and load Carbon project state through FastAPI/Postgres.
3. Display readiness and assessment quality in an IBM Cloud-style shell.
4. Persist Carbon network plans and VM assignments through the shared API.
5. Generate Terraform ZIP packages from saved Carbon network plans.
6. Provide drag-and-drop VM placement for subnet, security, storage, and wave
   assignment.

Verified as of 2026-07-22: those slices are implemented and covered by
TypeScript, Jest, Playwright smoke validation, handoff parity tests, and Carbon
guidance tests for progress, step help, user-guide routing, and completion
checklists.
Streamlit remains production while Carbon builds deeper real-workbook parity,
accessibility/UAT evidence, and production support evidence.

## Promotion Gates

Carbon should not replace Streamlit until it can:

- [x] Upload and parse RVTools workbooks through the shared backend.
- [x] Save, load, rename, and delete project state.
- [x] Assign VMs to subnet, security, storage, and wave buckets with
  drag-and-drop and autosave.
- [x] Generate Terraform ZIP packages from saved Carbon network plans.
- [x] Reproduce the core Streamlit planning workflow surfaces: VM review, wave
  planning, remediation tracking, image import planning, migration ops, and
  export package generation.
- [x] Provide in-app migration guidance through progress, step-help, and
  completion-checklist affordances.
- [ ] Prove those workflows with enough real-workbook parity and UAT evidence
  to replace Streamlit as the default UI.
- [x] Pass browser-level smoke tests for upload, persistence, DnD assignment,
  autosave reload, and primary views.
- [ ] Preserve or improve accessibility, performance, and auditability.
- [x] Support the same Docker/Postgres runtime without manual setup.

## Recommendation

Continue Carbon/React as the enterprise UI candidate, but treat it as a product
experiment with objective promotion gates. Streamlit remains the production
application until Carbon provides a complete and demonstrably better workflow.

See [Carbon Promotion Gate Review](carbon-promotion-gate-review.md) for the
current gate-by-gate pass/partial/fail assessment and Phase 4 backlog.
See [Carbon Streamlit Parity Roadmap](carbon-streamlit-parity-roadmap.md) for
the recommended next branches before a default-UI decision.
See [Carbon Promotion and Cutover Guide](carbon-promotion-cutover-guide.md) for
the staged rollout, rollback, and support checklist.
See [Target Platform Roadmap](target-platform-roadmap.md) for why IBM Cloud VPC
remains the current target and how future OpenShift Virtualization work should
be scoped.
