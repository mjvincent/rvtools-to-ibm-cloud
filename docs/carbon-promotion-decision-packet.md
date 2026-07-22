# Carbon Promotion Decision Packet

Copy this packet for each Carbon release-candidate decision. It is the concise
front door for the go/no-go meeting; attach or link the detailed evidence files
instead of duplicating them here.

Streamlit remains the supported production UI and rollback path until a
completed packet explicitly approves a Carbon pilot or later default promotion.

## Decision Summary

| Field | Value |
| --- | --- |
| Decision date |  |
| Release candidate branch/tag |  |
| Carbon commit SHA |  |
| Decision owner |  |
| Product owner |  |
| Migration SME |  |
| Accessibility reviewer |  |
| Operations owner |  |
| Security/data owner |  |
| Rollback decision maker |  |
| Decision | No-go / Pilot with Streamlit fallback / Promote later |
| Pilot scope, if approved |  |
| Streamlit fallback status | Available / Not available |

## Required Evidence Links

| Evidence area | Required source | Status |
| --- | --- | --- |
| Feature and output parity | [Carbon Handoff Parity](carbon-handoff-parity.md) and [Carbon Real-Workbook Parity Evidence](carbon-real-workbook-parity-evidence.md) | Not started |
| Manual UAT | [Carbon Manual UAT Evidence Index](carbon-manual-uat-evidence-index.md), completed [Carbon UAT Session Worksheet](carbon-uat-session-worksheet.md), and completed [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md) | Not started |
| Accessibility | [Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md) and reviewer notes for keyboard, screen-reader, responsive, and high-zoom review | Not started |
| Hosted operations | [Carbon Hosted Operations Readiness Checklist](carbon-hosted-operations-readiness.md) and [Carbon Operations Runbook](carbon-operations-runbook.md) | Not started |
| Cutover and rollback | [Carbon Promotion and Cutover Guide](carbon-promotion-cutover-guide.md) plus named rollback authority | Not started |
| Validation commands | Python pytest, Python compile, Terraform package validation, Carbon TypeScript, Carbon Jest, Carbon build, and applicable Playwright evidence | Not started |
| Open issues and accepted gaps | Issue tracker links with severity, owner, mitigation, and revisit date | Not started |

Use the GitHub `Carbon pilot finding` issue template for every UAT or pilot
finding that could affect pilot scope, default promotion, accessibility,
operations, output parity, or Streamlit fallback.

## Gate Checklist

| Gate | Required answer | Actual answer | Evidence / notes |
| --- | --- | --- | --- |
| Can Carbon complete workbook intake, save/load, planning, preflight, preview, and ZIP export? | Yes |  |  |
| Does Carbon output match Streamlit contracts or documented intentional differences? | Yes |  |  |
| Can migration users complete the workflow without facilitator help? | Yes |  |  |
| Can keyboard-only and screen-reader users complete the primary workflow? | Yes |  |  |
| Are hosted health checks, logs, alerts, retention, backup/restore, artifact handling, and access controls accepted? | Yes |  |  |
| Are product, technical, operations, security/data, support, and rollback owners named? | Yes |  |  |
| Is Streamlit reachable as fallback during pilot/stabilization? | Yes |  |  |
| Are all blocker/high issues closed or explicitly accepted? | Yes |  |  |
| Are remaining medium/low issues tracked with owners and revisit dates? | Yes |  |  |

## Open Risks

| Risk | Severity | Impact | Mitigation | Owner | Revisit date |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Accepted Gaps

| Gap | Reason accepted | Pilot constraint | Owner | Revisit date |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Decision Rules

- Choose `No-go` if any blocker/high issue is unresolved, Streamlit fallback is
  unavailable, hosted operations evidence is missing, or output parity is not
  accepted.
- Choose `Pilot with Streamlit fallback` only when all required gates pass or
  accepted gaps are documented with owners and revisit dates.
- Choose `Promote later` only after a successful pilot, updated evidence packet,
  support readiness, rollback readiness, and formal approval.

## Sign-Off

| Role | Name | Decision | Date | Notes |
| --- | --- | --- | --- | --- |
| Product owner |  | Approve / Approve with issues / Reject |  |  |
| Migration SME |  | Approve / Approve with issues / Reject |  |  |
| Accessibility reviewer |  | Approve / Approve with issues / Reject |  |  |
| Operations owner |  | Approve / Approve with issues / Reject |  |  |
| Security/data owner |  | Approve / Approve with issues / Reject |  |  |
| Rollback decision maker |  | Approve / Approve with issues / Reject |  |  |

## Final Outcome

| Question | Answer |
| --- | --- |
| Is Carbon approved for pilot use with Streamlit fallback? |  |
| Is Carbon approved as the default UI? | No |
| If approved for pilot, what is the maximum user/workbook scope? |  |
| What date will this decision be revisited? |  |
| Final decision summary |  |
