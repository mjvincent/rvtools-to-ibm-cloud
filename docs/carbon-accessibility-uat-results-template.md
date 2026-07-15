# Carbon Accessibility and UAT Results Template

Use this template for each Carbon release-candidate review. Pair it with the
[Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md)
so the promotion review has a clear decision record, repeatable evidence, and
named follow-up owners.

Do not paste customer workbook paths, filenames, VM names, IP addresses, owners,
application names, screenshots with sensitive values, or raw RVTools content
into this file. Use sanitized labels such as `customer-workbook-a`,
`large-private-fixture`, or `pilot-assessment-1`.

## Review Summary

| Field | Value |
| --- | --- |
| Review date |  |
| Carbon commit SHA |  |
| Release candidate branch/tag |  |
| Reviewer names and roles |  |
| Migration SME |  |
| Accessibility reviewer |  |
| Browser and version |  |
| Operating system |  |
| Assistive technology |  |
| Viewports reviewed | Desktop / laptop / mobile / high zoom |
| Workbook label |  |
| Project label |  |
| Runtime | Docker Compose / hosted / other |
| API/Postgres mode | Local / hosted / other |
| Result | Not started / Pass / Pass with issues / Fail |
| Evidence folder or ticket |  |

## Evidence Collected

| Evidence | Location / reference | Notes |
| --- | --- | --- |
| Completed checklist |  |  |
| Carbon readiness report JSON |  |  |
| Carbon Terraform ZIP |  |  |
| Streamlit comparison ZIP or parity output |  |  |
| Sanitized large-workbook timing evidence |  |  |
| Browser console/network notes |  |  |
| Docker/runtime health output |  |  |
| Screenshots or recordings |  |  |

## Result Matrix

| Area | Result | Severity if not pass | Notes |
| --- | --- | --- | --- |
| Environment startup and health | Not started / Pass / Pass with issues / Fail |  |  |
| Keyboard navigation | Not started / Pass / Pass with issues / Fail |  |  |
| Screen-reader names, roles, and state | Not started / Pass / Pass with issues / Fail |  |  |
| Workbook intake | Not started / Pass / Pass with issues / Fail |  |  |
| Project save/load/autosave | Not started / Pass / Pass with issues / Fail |  |  |
| VM assignment by keyboard | Not started / Pass / Pass with issues / Fail |  |  |
| Network Plan component editing and validation | Not started / Pass / Pass with issues / Fail |  |  |
| Drag/drop VM assignment | Not started / Pass / Pass with issues / Fail |  |  |
| Readiness-chip review routing | Not started / Pass / Pass with issues / Fail |  |  |
| VM profile/storage overrides | Not started / Pass / Pass with issues / Fail |  |  |
| Remediation queue suggestions | Not started / Pass / Pass with issues / Fail |  |  |
| Image import planning | Not started / Pass / Pass with issues / Fail |  |  |
| Migration operations readiness | Not started / Pass / Pass with issues / Fail |  |  |
| Terraform preview and selected download | Not started / Pass / Pass with issues / Fail |  |  |
| Terraform ZIP export | Not started / Pass / Pass with issues / Fail |  |  |
| Error and recovery paths | Not started / Pass / Pass with issues / Fail |  |  |
| Mobile/tablet/high-zoom layout | Not started / Pass / Pass with issues / Fail |  |  |
| Carbon-vs-Streamlit output acceptability | Not started / Pass / Pass with issues / Fail |  |  |

## Workflow Notes

### Workbook Intake

| Question | Answer |
| --- | --- |
| Did upload complete without app console errors? |  |
| Were summary metrics credible for the workbook? |  |
| Were unsupported workbook values surfaced clearly? |  |

### Assignment and Planning

| Question | Answer |
| --- | --- |
| Could a keyboard-only user complete required assignments? |  |
| Were inferred remediation suggestions understandable? |  |
| Were subnet, security group, storage/IOPS, and wave choices clear? |  |
| Were Network Plan component edit actions and validation findings understandable? |  |
| Were VM override reasons and audit output acceptable? |  |

### Export Readiness

| Question | Answer |
| --- | --- |
| Did preflight findings explain blockers and next actions? |  |
| Did review actions route to the correct workflow and VM/context? |  |
| Did preview open, filter, download selected files, and close correctly? |  |
| Did ZIP export complete only after blockers were resolved? |  |

### Accessibility

| Question | Answer |
| --- | --- |
| Were focus order and visible focus acceptable? |  |
| Were all primary controls operable with `Tab`, `Shift+Tab`, `Enter`, and `Space`? |  |
| Were active navigation, readiness status, notifications, rows, and modals announced clearly? |  |
| Were drag/drop alternatives discoverable and usable? |  |
| Was there any keyboard trap? |  |

## Issue Log

Use one row per finding. Severity guidance:

- `Blocker`: prevents completing a primary migration workflow or creates
  unacceptable accessibility, data loss, or export risk.
- `High`: primary workflow can continue only with a difficult workaround.
- `Medium`: workflow is usable but confusing, inefficient, or missing expected
  feedback.
- `Low`: polish issue that does not block the pilot.

| ID | Severity | Workflow | Steps to reproduce | Expected | Actual | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-001 |  |  |  |  |  |  |  |  |

## Known Gaps Accepted for Pilot

| Gap | Reason accepted | Mitigation | Owner | Revisit date |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Sign-Off

| Role | Name | Decision | Date | Notes |
| --- | --- | --- | --- | --- |
| Migration user / UAT lead |  | Approve / Approve with issues / Reject |  |  |
| Accessibility reviewer |  | Approve / Approve with issues / Reject |  |  |
| Migration SME |  | Approve / Approve with issues / Reject |  |  |
| Release owner |  | Approve / Approve with issues / Reject |  |  |

## Promotion Decision

| Question | Answer |
| --- | --- |
| Is Carbon acceptable for pilot use with Streamlit fallback? |  |
| Is Carbon acceptable as the default UI? |  |
| Are all blocker and high-severity issues closed or explicitly accepted? |  |
| Are remaining medium/low issues tracked with owners? |  |
| Final decision | Promote / Pilot only / Do not promote |
