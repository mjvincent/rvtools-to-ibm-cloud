# Carbon UAT Session Worksheet

Copy this worksheet for each Carbon manual review session. Keep the copy in a
sanitized evidence folder or ticket. Do not edit this master worksheet with
customer-specific values.

Use this with:

- [Carbon Manual UAT Evidence Index](carbon-manual-uat-evidence-index.md)
- [Carbon Manual UAT Runbook](carbon-manual-uat-runbook.md)
- [Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md)

## Session Metadata

| Field | Value |
| --- | --- |
| Session date |  |
| Carbon commit SHA |  |
| Branch or release candidate tag |  |
| Reviewer name and role |  |
| Migration SME |  |
| Accessibility reviewer |  |
| Browser and version |  |
| Operating system |  |
| Assistive technology |  |
| Viewport or zoom level |  |
| Workbook label | small-sample / workshop-sample / customer-workbook-a |
| Runtime | Docker Compose / hosted / other |
| Evidence folder or ticket |  |
| Session result | Not started / Pass / Pass with issues / Fail |

## Pre-Session Checks

| Check | Result | Evidence or notes |
| --- | --- | --- |
| `git status --short --branch` is clean or expected differences are recorded. |  |  |
| `git rev-parse HEAD` recorded. |  |  |
| Carbon UI, FastAPI, Streamlit fallback, and Postgres are healthy or hosted runtime health is recorded. |  |  |
| Latest Python and Carbon validation output is attached or linked. |  |  |
| Reviewer understands sensitive-data rules before capturing screenshots or notes. |  |  |

## Walkthrough Notes

| Step | Expected outcome | Result | Notes / evidence |
| --- | --- | --- | --- |
| Open Carbon shell | Page loads without app console errors and navigation is visible. |  |  |
| Open `Help` and `Step help` | Reviewer understands the current workflow and next step. |  |  |
| Open user guide in a separate window | Guide can stay visible while working. |  |  |
| Upload workbook | Summary, readiness, and assignment rows populate. |  |  |
| Save project | Project save status is clear and no false success is shown. |  |  |
| Refresh and reload project | Assignments, planning fields, and workflow state reload. |  |  |
| Complete one keyboard assignment | Reviewer can assign without drag/drop. |  |  |
| Complete one drag/drop assignment | Placement modal appears and the assignment persists. |  |  |
| Review Network Plan validation | Findings are understandable and actionable. |  |  |
| Edit a network component | Modal fields are labeled and cancel/save behavior is clear. |  |  |
| Review VM Overrides | Override reason and exclusion behavior are understandable. |  |  |
| Review Remediation Backlog | Status, owner, due date, and notes are editable and clear. |  |  |
| Review Image Import Planning | Import status and target image ID expectations are clear. |  |  |
| Review Migration Ops | Ready, review, and blocked cutover states are understandable. |  |  |
| Run Export preflight | Blockers/warnings explain fix location and next action. |  |  |
| Use a `Review issue` route | Route lands in the expected workflow and context. |  |  |
| Preview Terraform package | Files can be filtered, inspected, downloaded, and preview closed. |  |  |
| Download readiness report | JSON download is available and contains review evidence. |  |  |
| Download Terraform ZIP | ZIP download occurs only after blockers are resolved or absent. |  |  |
| Compare or accept output | Carbon output is acceptable against Streamlit/parity evidence. |  |  |

## Accessibility Notes

| Area | Result | Notes / evidence |
| --- | --- | --- |
| Keyboard focus order |  |  |
| Keyboard activation for buttons, checkboxes, menus, modals, and preview controls |  |  |
| Drag/drop alternatives |  |  |
| Screen-reader navigation and selected workflow state |  |  |
| Readiness-chip names and routing |  |  |
| Table, row, and checkbox names |  |  |
| Notifications for upload, save, preflight, preview, and export |  |  |
| Modal focus behavior |  |  |
| Responsive layout and 200% zoom |  |  |

## Error-Recovery Notes

| Scenario | Expected outcome | Result | Notes / evidence |
| --- | --- | --- | --- |
| Upload failure | Error is visible and current valid workbook state is not replaced. |  |  |
| Save/autosave failure | User is told work is not safely saved and can retry. |  |  |
| Preflight blockers | ZIP generation is blocked and next actions are visible. |  |  |
| Preview failure | Error is visible and retry is possible. |  |  |
| ZIP generation failure | Generation state resets and retry is possible. |  |  |
| Browser refresh with unsaved work | Dirty/saved state is understandable. |  |  |

## Issues Found

| ID | Severity | Workflow | Steps to reproduce | Expected | Actual | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-YYYYMMDD-001 |  |  |  |  |  |  |  |  |

## Accepted Gaps

| Gap | Reason accepted | Mitigation | Owner | Revisit date |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Session Decision

| Question | Answer |
| --- | --- |
| Did the reviewer complete the primary workflow without facilitator help? |  |
| Are all blocker/high findings closed or explicitly accepted? |  |
| Are medium/low findings tracked with owners and revisit dates? |  |
| Is Carbon acceptable for pilot use with Streamlit fallback for this reviewed scope? |  |
| Is Carbon acceptable as the default UI based on this session alone? | No |
| Final decision | Pass / Pass with issues / Fail / Continue evidence collection |

## Sensitive-Data Check

Before storing this worksheet, confirm it does not contain raw RVTools rows,
private workbook paths, full VM names, IP addresses, CIDR plans, owner names,
application names, screenshots with sensitive values, IBM Cloud credentials,
Terraform state, API keys, or other secrets.
