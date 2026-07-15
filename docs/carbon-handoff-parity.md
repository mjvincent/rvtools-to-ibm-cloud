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
- `migration-manifest.json`
- `assessment-quality.json`
- `assessment-quality.csv`
- `preflight-report.json`
- `preflight-report.csv`
- `pricing-diagnostics.json`
- `pricing-diagnostics.csv`
- mapping/readiness CSVs
- `image-import-variables.tfvars.example`
- `migration-runbook.md`

Carbon now generates the same major handoff artifact inventory as Streamlit.
The remaining parity work is to keep expanding fixture comparisons so workbook
detail fidelity and operational edge cases are proven before promotion.

## Streamlit Package Contract

The expected package inventory is now captured in
`prototype/api/handoff_parity.py` and covered by
`tests/test_carbon_handoff_parity.py`.

The parity tests now include:

- A synthetic Streamlit-vs-Carbon fixture comparison for exact handoff content
  across the core package files.
- An edge-case Streamlit-vs-Carbon fixture comparison for exact VM, disk,
  partition, NIC, memory-readiness, and readiness-finding CSV content.
- A multi-VM Streamlit-vs-Carbon fixture comparison for exact operational
  handoff parity across decision audit, remediation backlog, image import,
  cutover readiness, manifest references, remediation summary behavior, and
  planning-state content.
- A workshop real-workbook subset comparison from
  `samples/SizingWorkshop-RVTools.xlsx` for unknown-network, low assessment
  confidence, missing-vMemory, disk/partition empty-state, image-import, and
  cutover-readiness parity.
- A sample-workbook operational overlay comparison that now includes exact
  non-preflight handoff file parity, timestamp-normalized planning-state
  parity, and Carbon preflight superset checks for network-plan validation.
- A sample-workbook Carbon contract test using
  `samples/rvtools-small-complete.xlsx` through the FastAPI upload summary path.
- Field-level assertions for `decision-audit.csv`,
  `remediation-backlog.csv`, `image-import-plan.csv`,
  `cutover-readiness.csv`, and `planning-state.json`, including open vs.
  closed remediation behavior in cutover readiness.
- A sample-workbook API ZIP inventory test that calls
  `POST /api/projects/{project_id}/terraform`, verifies the full Streamlit
  handoff inventory is present, verifies the Carbon modular Terraform layout,
  confirms `network-plan.json` is the only non-handoff/non-Terraform extra,
  and checks representative decision-audit, remediation, and image-import CSV
  payloads from the generated ZIP.
- A workshop-workbook API ZIP evidence test that sends a larger representative
  workbook subset through the real FastAPI Terraform ZIP endpoint and verifies
  operational handoff evidence for overrides, exclusions, remediation, image
  import status, cutover blockers, planning state, and saved network-plan state.
- A sample-workbook API preview parity test that compares
  `POST /api/projects/{project_id}/terraform/preview` with the downloaded ZIP
  inventory and representative file contents for manifest, handoff CSV, and
  Carbon state files.
- A Carbon Export UI inventory drift test that compares the shared UI JSON
  inventory with backend handoff, modular Terraform, and Carbon-only ZIP
  constants.

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
| `image-import-variables.tfvars.example` | Yes | Included | Carbon ZIP preserves known custom image IDs and leaves placeholders for images that still need import IDs. |
| `cutover-readiness.csv` | Yes | Included | Carbon ZIP derives cutover readiness from planning fields, remediation tracker, and image import status. |
| `planning-state.json` | Yes | Included | Carbon ZIP includes Streamlit-compatible planning state generated from Carbon rows. |
| `migration-manifest.json` | Yes | Included | Carbon ZIP generates manifest from normalized Carbon rows and references the operational handoff CSVs; additional workbook fixture coverage remains useful for edge fidelity. |
| `decision-audit.csv` | Yes | Included | Carbon ZIP includes profile/storage/exclusion decisions and pricing impact columns via `prototype/api/carbon_handoff.py`. |
| `preflight-report.csv/json` | Yes | Included | Carbon ZIP runs package preflight against Carbon network-plan resources and normalized rows; Export can run the same backend preflight before download. |
| `pricing-diagnostics.csv/json` | Partial | Included | Carbon ZIP includes static-catalog diagnostics; live/cached pricing parity remains future work. |
| mapping/readiness CSVs | Partial | Included | Carbon ZIP includes VM, disk, partition, NIC, memory, and readiness CSVs from normalized rows. Carbon intake now preserves hidden workbook detail fields for these exports. |
| `image-import-variables.tfvars.example` | Yes | Included | Carbon ZIP includes placeholder custom image tfvars. |
| `migration-runbook.md` | Yes | Included | Carbon ZIP reuses the handoff runbook generator. |

## Recommended Implementation Order

1. Add more API-level Streamlit-vs-Carbon fixture comparisons for additional
   edge-case workbooks.
2. Improve any remaining workbook-derived source metadata gaps found by those
   fixture comparisons.
3. Continue tightening Carbon Export workflow feedback as more parity checks
   move from fixture coverage into promotion gates.

## Promotion Gate Impact

Until this parity is complete, Streamlit remains the production UI for migration
handoff packages. Carbon can remain a planning prototype and Terraform renderer,
but it should not be promoted as the supported handoff workflow.
