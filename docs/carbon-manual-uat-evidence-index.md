# Carbon Manual UAT Evidence Index

**Created**: 2026-07-22
**Purpose**: Track the evidence needed before Carbon can move from prototype
evaluation toward pilot use with Streamlit fallback.

This index does not replace the manual review. It gives reviewers one place to
see what is already covered by automation, what must still be tested by people,
and which files belong in a release-candidate evidence packet.

## Current Decision

Carbon is not ready to replace Streamlit. The current target is to collect
enough evidence for a controlled pilot while keeping Streamlit as the supported
production UI and rollback path.
Streamlit remains available as fallback during any Carbon pilot.

## Evidence Sources

| Evidence source | Use it for | Status |
| --- | --- | --- |
| [Carbon Manual UAT Runbook](carbon-manual-uat-runbook.md) | Reviewer sequence, setup, evidence list, pass/fail rules, and data-handling guardrails. | Ready |
| [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md) | Step-by-step manual keyboard, screen-reader, workflow, responsive, and recovery checklist. | Ready |
| [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md) | Release-candidate sign-off packet with issue log and promotion decision. | Ready |
| [Carbon UAT Session Worksheet](carbon-uat-session-worksheet.md) | Fillable per-review working copy for one reviewer session before summarizing results. | Ready |
| [Carbon Real-Workbook Parity Evidence](carbon-real-workbook-parity-evidence.md) | Checked-in sample/workshop workbook parser, parity, API ZIP, preview, and performance evidence. | Ready |
| [Carbon Accessibility and UAT Results - Focused Automated Pass](carbon-accessibility-uat-results-2026-07-10-focused.md) | Automated focused evidence for VM Overrides and Export Readiness accessibility fixes. | Complete for focused scope |
| [Carbon Accessibility and UAT Results - Network Plan Focused Pass](carbon-accessibility-uat-results-2026-07-15-network-plan.md) | Automated focused evidence for Network Plan component editing and validation. | Complete for focused scope |

## Manual Evidence Still Required

| Area | Minimum evidence needed | Owner |
| --- | --- | --- |
| Migration-user walkthrough | A migration reviewer completes the small sample workflow from intake through ZIP export without facilitator intervention. | Migration SME |
| Screen-reader review | VoiceOver, NVDA, JAWS, or target-environment assistive technology review covers navigation, readiness chips, notifications, tables, modals, validation findings, and package preview. | Accessibility reviewer |
| Responsive/high-zoom review | Desktop, laptop, narrow viewport, and 200% zoom screenshots or notes show no blocking overlap or unreachable controls. | Accessibility reviewer |
| Error recovery | Reviewer exercises or inspects failed upload/save/preflight/preview/ZIP paths and confirms recovery instructions are clear. | Release owner |
| Output acceptability | Carbon ZIP or sanitized inventory is accepted against Streamlit output or checked-in parity evidence for the reviewed workbook. | Migration SME |
| Pilot decision | Results template includes named reviewers, decisions, accepted gaps, owners, and revisit dates. | Release owner |

## Evidence Packet Checklist

Create one sanitized folder or ticket for each release-candidate review. Include:

- completed `carbon-accessibility-uat-checklist.md`
- completed copy of `carbon-uat-session-worksheet.md` for each reviewer session
- completed `carbon-accessibility-uat-results-template.md`
- Carbon commit SHA and branch/tag
- validation command output
- `docker compose ps` output or hosted-runtime health evidence
- browser and assistive-technology notes
- responsive/high-zoom notes or screenshots
- sanitized screenshots or short recordings for failed or confusing flows
- Carbon readiness report JSON
- Carbon Terraform ZIP or sanitized ZIP inventory
- Streamlit comparison ZIP or parity-test output when used
- issue log with owner, severity, status, and revisit date

## Data Handling Rules

Do not include raw customer RVTools content, private workbook filenames, full
VM names, IP addresses, CIDR plans, owner names, application names, IBM Cloud credentials,
Terraform state, API keys, or screenshots containing sensitive inventory.
Use labels such as `small-sample`, `workshop-sample`,
`customer-workbook-a`, or `pilot-assessment-1`.

## Recommended First Review

1. Run the automated validation suite from [Testing](testing.md).
2. Use `samples/rvtools-small-complete.xlsx` for the first manual review.
3. Complete the runbook sequence end to end.
4. Record results in the template.
5. Open follow-up issues for every medium or higher finding.
6. Repeat with `samples/SizingWorkshop-RVTools.xlsx` after the small sample pass.
7. Repeat with a sanitized private workbook label before any pilot decision.

## Promotion Impact

Carbon can move toward pilot only after the manual evidence packet shows that
real users can understand the workflow, recover from common failures, and
produce acceptable Terraform handoff output while Streamlit remains available
as fallback.
