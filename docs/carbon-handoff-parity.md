# Carbon Handoff Parity

This document tracks the gap between the production Streamlit handoff package
and the current Carbon/FastAPI Terraform ZIP.

## Current State

Streamlit builds a Terraform package plus operational handoff files in
`streamlit_app/package_builder.py`. Carbon currently calls
`POST /api/projects/{project_id}/terraform`, which renders modular Terraform
from the saved Carbon network plan and writes:

- Terraform module/root files from `terraform_carbon_renderer_modular.py`
- `README.md`
- `network-plan.json`
- `decision-audit.csv`
- `remediation-backlog.csv`
- `image-import-plan.csv`
- `cutover-readiness.csv`
- `planning-state.json`

That means Carbon can generate infrastructure code, but it does not yet produce
the full migration handoff package.

## Streamlit Package Contract

The expected package inventory is now captured in
`prototype/api/handoff_parity.py` and covered by
`tests/test_carbon_handoff_parity.py`.

Required handoff files:

- `migration-manifest.json`
- `assessment-quality.json`
- `assessment-quality.csv`
- `preflight-report.json`
- `preflight-report.csv`
- `pricing-diagnostics.json`
- `pricing-diagnostics.csv`
- `decision-audit.csv`
- `remediation-backlog.csv`
- `image-import-plan.csv`
- `cutover-readiness.csv`
- `planning-state.json`
- `vm-mapping.csv`
- `disk-mapping.csv`
- `partition-mapping.csv`
- `nic-mapping.csv`
- `memory-readiness.csv`
- `readiness-findings.csv`
- `image-import-variables.tfvars.example`
- `migration-runbook.md`

## Carbon Status

| Artifact | Carbon source state exists? | ZIP parity status | Notes |
| --- | --- | --- | --- |
| `remediation-backlog.csv` | Yes | Included | Carbon ZIP normalizes saved remediation tracker state and generated readiness blockers. |
| `image-import-plan.csv` | Yes | Included | Carbon ZIP normalizes saved image import status. |
| `cutover-readiness.csv` | Yes | Included | Carbon ZIP derives cutover readiness from planning fields, remediation tracker, and image import status. |
| `planning-state.json` | Yes | Included | Carbon ZIP includes Streamlit-compatible planning state generated from Carbon rows. |
| `migration-manifest.json` | Partial | Missing | Requires Carbon VM-to-handoff normalization. |
| `decision-audit.csv` | Yes | Included | Carbon ZIP includes profile/storage/exclusion decisions and pricing impact columns via `prototype/api/carbon_handoff.py`. |
| `preflight-report.csv/json` | Partial | Missing | Requires Carbon-side package preflight integration. |
| `pricing-diagnostics.csv/json` | Partial | Missing | Requires pricing/catalog context for Carbon package. |
| mapping/readiness CSVs | Partial | Missing | Requires Carbon assignment rows normalized to handoff records. |
| `image-import-variables.tfvars.example` | Partial | Missing | Requires custom image placeholder export from Carbon rows. |
| `migration-runbook.md` | Yes | Missing | Can reuse handoff runbook generator after context mapping. |

## Recommended Implementation Order

1. Add Carbon-to-handoff VM normalization so existing `handoff` generators can
   produce manifest, mapping, readiness, image variable, and runbook files.
2. Integrate Carbon preflight and pricing diagnostics.
3. Update the Carbon Export workflow to show package contents parity status
   before download.

## Promotion Gate Impact

Until this parity is complete, Streamlit remains the production UI for migration
handoff packages. Carbon can remain a planning prototype and Terraform renderer,
but it should not be promoted as the supported handoff workflow.
