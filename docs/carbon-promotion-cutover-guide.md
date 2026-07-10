# Carbon Promotion and Cutover Guide

This guide defines how to move Carbon from prototype to production without
forking the project or weakening the current Streamlit production path.

## Current Position

Streamlit remains the supported production UI. Carbon is the enterprise UI
candidate that uses the same parser, readiness logic, FastAPI persistence,
handoff package generation, Terraform renderer, and Postgres project store.

Do not split Streamlit and Carbon into separate repositories. A fork would make
the shared migration engine harder to validate and would increase the risk that
Terraform, handoff files, pricing logic, or readiness behavior diverge.

Use one repository with:

- Streamlit in `app.py` and `streamlit_app/`
- Carbon in `prototype/carbon-ui/`
- FastAPI in `prototype/api/`
- shared engines in `assessment_quality/`, `handoff/`, `models/`,
  `terraform_carbon_renderer_modular.py`, and related Python modules
- feature branches, tags, and releases for promotion checkpoints

## Promotion Gates

Carbon is eligible for production promotion only when these gates are green:

| Gate | Required Evidence |
| --- | --- |
| Core workflow | Workbook upload, project save/load, assignment, preflight, package preview, and ZIP export work through Carbon. |
| Feature parity | Wave planning, remediation, image import, migration ops, overrides, decision audit, handoff package, and planning-state reload match Streamlit contracts. |
| Real-workbook parity | Representative RVTools workbooks compare cleanly for handoff artifacts, with documented exceptions for Carbon-specific preflight checks. |
| Runtime readiness | Docker Compose and the intended hosted runtime start API, Carbon UI, Streamlit, and Postgres reliably. |
| Accessibility and browser coverage | Keyboard, screen-reader, multi-browser, and UAT checks pass for the primary workflow using the [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md), with outcomes captured in the [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md). |
| Operations | Backup/restore, rollback, logging, monitoring, data retention, and support ownership are documented in the [Carbon Operations Runbook](carbon-operations-runbook.md). |
| User acceptance | Migration users complete at least one realistic assessment through Carbon and approve the workflow. |

## Pre-Cutover Checklist

Before promotion:

1. Freeze a release candidate branch.
2. Run full validation:

   ```bash
   make compile
   venv/bin/python -m pytest -q
   cd prototype/carbon-ui
   npx tsc --noEmit --incremental false
   npm test -- --runInBand
   npm run test:e2e
   ```

3. Run Docker Compose and verify health for Streamlit, API, Carbon UI, and
   Postgres.
4. Upload at least one small and one large representative RVTools workbook in
   Carbon.
5. Save, reload, and autosave a Carbon project.
6. Generate a Terraform ZIP from Carbon and inspect:
   - `main.tf`
   - `network-plan.json`
   - `migration-manifest.json`
   - `decision-audit.csv`
   - `remediation-backlog.csv`
   - `image-import-plan.csv`
   - `cutover-readiness.csv`
   - mapping/readiness CSVs
7. Confirm Streamlit can still generate a package from the same workbook.
8. Complete the [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md) for the release candidate, record the decision in the [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md), and attach evidence to the promotion review.
9. Back up Postgres and the artifact volume using the
   [Carbon Operations Runbook](carbon-operations-runbook.md), or use the
   deployment platform's native backup mechanism.
10. Capture the current production image/tag/commit for rollback.
11. Fill in the support ownership and rollback authority matrix in the
    [Carbon Operations Runbook](carbon-operations-runbook.md).

## Cutover Pattern

Prefer a staged cutover:

1. **Shadow mode**: Carbon is available to internal users while Streamlit remains
   the official production path.
2. **Pilot mode**: One migration assessment is completed in Carbon and compared
   with Streamlit output.
3. **Default switch**: Documentation and launcher links point users to Carbon,
   while Streamlit remains available as fallback.
4. **Stabilization window**: Keep both UIs deployed while monitoring user issues,
   package outputs, and persistence behavior.
5. **Retirement decision**: Remove Streamlit from the default deployment only
   after a deliberate go/no-go review.

## Rollback Plan

Rollback should be simple because Streamlit remains in the same repository and
uses the same shared engine.

If Carbon promotion fails:

1. Repoint user documentation and launcher links to Streamlit.
2. Keep the same Postgres data unless the failure is data-related.
3. Re-run Streamlit package generation for affected projects or workbooks.
4. Preserve the failing Carbon project state for debugging.
5. Open a regression issue with:
   - workbook name or fixture
   - project ID
   - Carbon commit
   - generated package ZIP
   - expected Streamlit behavior
   - observed Carbon behavior

Do not revert shared engine changes unless the regression is proven to be in
shared logic and affects Streamlit too.

## Data Handling

RVTools workbooks, generated Terraform, planning-state JSON, and handoff CSVs
can contain sensitive infrastructure and migration data.

Before Carbon production use:

- require authenticated access
- use HTTPS
- restrict access to approved migration users
- define retention for uploaded workbooks and generated artifacts
- document and test database and artifact backup/restore
- avoid storing IBM Cloud API keys in project state or generated packages
- keep Terraform state files out of the repository

## Post-Cutover Monitoring

Track:

- upload failures by workbook type or size
- API errors during save/load/autosave
- Terraform ZIP generation failures
- preflight blocker patterns
- package parity regressions
- user-reported accessibility or browser issues
- Postgres storage growth

Use [Carbon Operations Runbook](carbon-operations-runbook.md) for the service
names, health endpoints, log commands, backup commands, restore checklist, and
incident response flow. The same runbook defines the support owner matrix and
rollback authority required before promotion.

## Go / No-Go Review

The go/no-go review should answer:

- Can Carbon complete the same assessment and handoff package as Streamlit?
- Are known differences intentional and documented?
- Can users recover work through saved projects or exported planning state?
- Have keyboard, screen-reader, responsive, error-recovery, and UAT checklist items been completed?
- Can the team roll back to Streamlit within the same day?
- Are support and data-retention responsibilities assigned?

If any answer is no, keep Streamlit as production and continue Carbon hardening.
