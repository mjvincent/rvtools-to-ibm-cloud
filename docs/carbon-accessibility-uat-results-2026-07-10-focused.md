# Carbon Accessibility and UAT Results - Focused Automated Pass

This records a focused automated keyboard/accessibility pass for Carbon VM
Overrides and Export Readiness. It is not a substitute for the full manual
screen-reader and UAT sign-off required before production promotion.

## Review Summary

| Field | Value |
| --- | --- |
| Review date | 2026-07-10 |
| Carbon commit SHA | Working tree before commit |
| Release candidate branch/tag | `feature/carbon-ui-network-planning-phase1` |
| Reviewer names and roles | Codex automated audit |
| Migration SME | Not reviewed |
| Accessibility reviewer | Not reviewed |
| Browser and version | Playwright Chromium |
| Operating system | Local macOS development environment |
| Assistive technology | Automated accessible-role queries only |
| Viewports reviewed | Desktop Chromium smoke viewport |
| Workbook label | Checked-in sample workbook |
| Project label | Temporary Carbon smoke project |
| Runtime | Local Next.js dev server on `http://localhost:3002` with Docker Compose API/Postgres |
| API/Postgres mode | Local Docker Compose |
| Result | Pass with issues addressed |
| Evidence folder or ticket | Local command output |

## Evidence Collected

| Evidence | Location / reference | Notes |
| --- | --- | --- |
| Focused component tests | `npm test -- --runInBand __tests__/components/OverridesWorkflow.test.tsx __tests__/components/ExportWorkflow.test.tsx` | 25 passed |
| TypeScript check | `npx tsc --noEmit --incremental false` | 0 errors |
| Focused browser smoke | `CARBON_BASE_URL=http://localhost:3002 npx playwright test e2e/carbon-smoke.spec.ts --project=chromium -g "uploads workbook and round-trips saved project state"` | 1 passed |
| Whitespace check | `git diff --check` | Passed |

## Result Matrix

| Area | Result | Severity if not pass | Notes |
| --- | --- | --- | --- |
| VM Overrides table naming | Pass with issue addressed | Medium | Added accessible table name `VM override rows`. |
| VM profile override fields | Pass |  | Existing labels remained discoverable by accessible name. |
| Export package preview file picker | Pass with issue addressed | Medium | Selected preview file now exposes selected state with `aria-pressed`. |
| Terraform preview close behavior | Pass |  | Existing close control remains explicit and covered. |
| End-to-end upload/save/load/override/preview path | Pass |  | Focused Chromium smoke passed against current source. |

## Issue Log

| ID | Severity | Workflow | Steps to reproduce | Expected | Actual | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-20260710-001 | Medium | VM Overrides | Navigate to VM Overrides and query tables by accessible role/name. | The override table has a clear accessible name. | Table rows were labeled individually, but the table itself was unnamed. | Component and Playwright role assertions added. | Codex | Fixed |
| UAT-20260710-002 | Medium | Export Readiness | Open Package preview and move between preview files. | The currently selected package file exposes selected state beyond visual styling. | Selection was visual-only. | Component and Playwright assertions added for selected preview button state. | Codex | Fixed |

## Known Gaps Accepted for This Focused Pass

| Gap | Reason accepted | Mitigation | Owner | Revisit date |
| --- | --- | --- | --- | --- |
| Manual screen-reader review not completed | This pass used automated accessible-role queries only. | Complete the full checklist with VoiceOver, NVDA, JAWS, or the target deployment assistive technology. | Release owner | Before promotion |
| Mobile/tablet/high-zoom review not completed | This pass targeted the desktop smoke path. | Run the full responsive section of the checklist. | Release owner | Before promotion |
| Human migration-user UAT not completed | Automated smoke tests cannot validate workflow comprehension. | Run at least one realistic pilot assessment with a migration user. | Migration SME | Before promotion |

## Promotion Decision

| Question | Answer |
| --- | --- |
| Is Carbon acceptable for pilot use with Streamlit fallback based on this focused pass alone? | Not decided |
| Is Carbon acceptable as the default UI based on this focused pass alone? | No |
| Are all blocker and high-severity issues closed or explicitly accepted? | No blocker/high issues were found in this focused pass |
| Are remaining medium/low issues tracked with owners? | Yes |
| Final decision | Continue Phase 6 evidence collection |
