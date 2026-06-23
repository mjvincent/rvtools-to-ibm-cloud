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
  projects, project state, and artifacts.
- `prototype/carbon-ui` provides the experimental IBM Carbon Design System UI.
- `docker-compose.yml` starts Streamlit, FastAPI, and Postgres together.
- Postgres stores project metadata and planning-state JSON.

## Carbon Prototype Scope

The Carbon UI should prove enterprise value through real workflow slices:

1. Upload an RVTools workbook and return estate/readiness summary.
2. Save and load Carbon project state through FastAPI/Postgres.
3. Display readiness and assessment quality in an IBM Cloud-style shell.
4. Keep deeper VM review, wave planning, image import planning, and export
   package actions mocked until the shell proves useful.

## Promotion Gates

Carbon should not replace Streamlit until it can:

- Upload and parse RVTools workbooks through the shared backend.
- Save, load, rename, and delete project state.
- Reproduce the core Streamlit planning workflows: VM review, wave planning,
  remediation tracking, image import planning, and export package generation.
- Pass browser-level smoke tests for upload, persistence, and primary views.
- Preserve or improve accessibility, performance, and auditability.
- Support the same Docker/Postgres runtime without manual setup.

## Recommendation

Continue Carbon/React as the enterprise UI candidate, but treat it as a product
experiment with objective promotion gates. Streamlit remains the production
application until Carbon provides a complete and demonstrably better workflow.
