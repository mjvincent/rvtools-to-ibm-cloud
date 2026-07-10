# Carbon Accessibility and UAT Checklist

Use this checklist to capture manual accessibility, keyboard, and user-acceptance evidence before promoting Carbon from prototype to production. Streamlit remains the supported production UI until these checks are completed and reviewed.

## Review Metadata

| Field | Value |
| --- | --- |
| Review date |  |
| Carbon commit |  |
| Reviewer names |  |
| Browser and version |  |
| Operating system |  |
| Assistive technology |  |
| Workbook used |  |
| Project name |  |
| Result | Not started / Pass / Pass with issues / Fail |
| Evidence location |  |

## Environment Setup

| Check | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- |
| Start local stack with `docker compose up -d --build carbon-ui` or the approved runtime startup path. | API, Streamlit, Carbon UI, and Postgres are healthy. |  |  |
| Open Carbon at `http://localhost:3000`. | Carbon loads without console errors from the app itself. Browser-extension warnings are documented separately. |  |  |
| Open Streamlit at `http://localhost:8501`. | Streamlit remains available as production fallback. |  |  |
| Run `docker compose ps`. | All four services report healthy/running. |  |  |
| Confirm test evidence is current. | Latest validation includes Python pytest, Carbon TypeScript, Jest, Playwright, and Docker health. |  |  |

## Keyboard Navigation

| Check | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- |
| Navigate the primary page shell with `Tab` and `Shift+Tab`. | Focus order is logical and visible. |  |  |
| Move through left navigation by keyboard. | Each workflow can be reached without a mouse. |  |  |
| Activate primary buttons with keyboard. | Buttons respond to `Enter` or `Space` as expected. |  |  |
| Use form controls in saved project, upload, assignment, override, and export areas. | Labels are announced and the current value is clear. |  |  |
| Confirm focus after modal open and close. | Focus moves into modal content and returns to the originating control after close. |  |  |
| Confirm no keyboard trap exists. | Reviewer can leave every panel, modal, dropdown, and preview area. |  |  |

## Screen Reader Review

Use VoiceOver, NVDA, JAWS, or the assistive technology required by the deployment environment.

| Check | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- |
| Page landmark and application name are understandable. | Reviewer can identify the app and current workflow. |  |  |
| Side navigation announces item names and selected state. | Active workflow is clear. |  |  |
| Readiness chips announce status and target route. | Non-ready chips explain what they represent and where review will go. |  |  |
| VM row checkboxes announce VM identity. | Row selection is understandable without visual context. |  |  |
| Drop zones and explicit assignment controls announce target names. | Drag/drop alternatives are discoverable. |  |  |
| Notifications announce success and error state. | Upload, save, export, and preflight messages are perceivable. |  |  |
| Terraform preview area announces selected file and content. | Reviewer can understand the selected file and close/download controls. |  |  |

## Critical Workflow UAT

| Flow | Steps | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- | --- |
| Workbook intake | Upload a representative RVTools workbook. | Upload succeeds, summary metrics populate, and no persistence warning appears. |  |  |
| Saved project | Save the project, refresh the page, then reload the saved project. | Project data, assignments, overrides, and workflow state reload correctly. |  |  |
| VM assignment by keyboard | Select one or more VM rows, choose subnet/security/storage/wave mode, and use explicit assignment controls. | Assignment is applied without drag/drop and can be saved. |  |  |
| Drag/drop assignment | Drag one VM and then multiple selected VMs to a target. | Confirmation modal appears and assignments persist. |  |  |
| Unassign | Remove one subnet, security group, storage, or wave assignment from a row. | Only the selected assignment type is cleared. |  |  |
| VM overrides | Add a VSI profile override, storage override, exclusion reason, and override reason. | Values persist and decision audit reflects the change. |  |  |
| Remediation backlog | Edit owner, status, due date, and notes. | Changes persist and export to CSV when requested. |  |  |
| Image import planning | Update import status, catalog ID, estimated time, and notes. | Changes persist and affect cutover readiness. |  |  |
| Migration ops | Review wave and cutover readiness. | Unresolved remediation, image import, and readiness blockers are visible. |  |  |
| Export readiness queue | Run preflight, use `Review issue`, then return to Export Readiness. | Review route lands in the correct workflow with useful VM/context selection. |  |  |
| Bulk suggested fixes | Select high-confidence queue suggestions, apply them, and inspect the suggestion audit. | Changes are applied intentionally, audited, and can be undone. |  |  |
| Terraform preview | Use `Preview Terraform`, filter files, download selected file, and close preview. | Preview is usable, selected download works, and `Close preview` collapses the panel. |  |  |
| ZIP download | Resolve blockers or use a clean project, then click `Download Terraform ZIP`. | Preflight runs first and the ZIP downloads only when blockers are clear. |  |  |
| Readiness report | Download the Carbon readiness report. | JSON includes checklist, planning gaps, preflight findings, suggestion audit, and package inventory. |  |  |

## Visual and Responsive Review

| Check | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- |
| Desktop viewport around 1920x1080. | No overlapping text, clipped controls, or unreadable cards. |  |  |
| Laptop viewport around 1366x768. | Primary workflows remain usable without hidden critical controls. |  |  |
| Narrow viewport around 390x844. | Navigation, queue rows, preview, and action groups wrap without overlap. |  |  |
| High zoom at 200%. | Content remains readable and keyboard operable. |  |  |
| Color contrast spot check. | Status tags, warnings, and buttons remain readable. |  |  |
| Long VM names and project names. | Text wraps or truncates cleanly without layout breakage. |  |  |

## Error and Recovery Review

| Scenario | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- |
| API unavailable during save/load. | Carbon shows persistence warning and does not imply work is safely saved. |  |  |
| Export preflight returns blockers. | ZIP download is blocked and queue provides useful next actions. |  |  |
| Terraform preview fails. | Error message is visible and retry is possible. |  |  |
| ZIP download fails. | Generation state resets and the user can retry. |  |  |
| Save-before-export fails. | Export does not continue with stale state. |  |  |
| Browser refresh after unsaved changes. | Saved/dirty state messaging is understandable. |  |  |

## Handoff Evidence

Attach or link the following when completing a promotion review:

- Browser and assistive-technology notes.
- Screenshots or screen recordings for any failed or unclear flow.
- Carbon readiness report JSON.
- Terraform ZIP generated by Carbon.
- Streamlit comparison ZIP or parity-test output when relevant.
- `docker compose ps` output or hosted-runtime health evidence.
- Commit SHA and validation command output.

## Decision Summary

| Question | Answer | Notes |
| --- | --- | --- |
| Can a keyboard-only user complete workbook intake, assignment, overrides, preflight review, preview, and ZIP download? |  |  |
| Can a screen-reader user understand workflow state, readiness status, queue actions, and export results? |  |  |
| Can users recover from common save, preflight, preview, and ZIP errors? |  |  |
| Are Carbon outputs acceptable compared with Streamlit for the reviewed workbook? |  |  |
| Are remaining issues documented with owner and severity? |  |  |
| Is Carbon ready for pilot use with Streamlit fallback? |  |  |

