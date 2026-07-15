# Carbon Accessibility and UAT Results - Network Plan Focused Pass

This records a focused automated accessibility/UAT evidence pass for Carbon
Network Plan component editing and local validation findings. It is not a
substitute for the full manual screen-reader and migration-user UAT sign-off
required before production promotion.

## Review Summary

| Field | Value |
| --- | --- |
| Review date | 2026-07-15 |
| Carbon commit SHA | Working tree before commit |
| Release candidate branch/tag | `codex/carbon-accessibility-uat-evidence` |
| Reviewer names and roles | Codex automated audit |
| Migration SME | Not reviewed |
| Accessibility reviewer | Not reviewed |
| Browser and version | Jest/jsdom component checks |
| Operating system | Local macOS development environment |
| Assistive technology | Automated accessible-role queries only |
| Viewports reviewed | Not reviewed in this focused pass |
| Workbook label | Default Carbon sample state |
| Project label | Default Carbon sample project |
| Runtime | Local source validation only |
| API/Postgres mode | Not exercised |
| Result | Pass with focused coverage added |
| Evidence folder or ticket | Local command output |

## Evidence Collected

| Evidence | Location / reference | Notes |
| --- | --- | --- |
| Focused component tests | `npm test -- --runInBand NetworkPlanWorkflow.test.tsx network-validation.test.ts` | Covers validation region, component edit accessible names, and structured validation findings. |
| Carbon TypeScript check | `npx tsc --noEmit --incremental false` | 0 errors. |
| Carbon full Jest suite | `npm test -- --runInBand` | Expected to run before merge. |
| Carbon production build | `npm run build` | Expected to run before merge. |
| Whitespace check | `git diff --check` | Expected to run before merge. |

## Result Matrix

| Area | Result | Severity if not pass | Notes |
| --- | --- | --- | --- |
| Network validation named region | Pass |  | Network validation panel exposes a `region` named `Network validation`. |
| Network validation finding text | Pass |  | Component coverage verifies severity-adjacent content: subject, message, and recommended action are rendered for invalid network resources. |
| Network component edit action names | Pass |  | Existing component edit buttons expose descriptive names such as `Edit network component prod-public-gateway`. |
| Component edit modal handoff | Pass |  | Existing test verifies clicking the edit action opens the shared component draft with selected component values. |
| Manual screen-reader review | Not started |  | Requires VoiceOver, NVDA, JAWS, or deployment-standard assistive technology. |
| Human migration-user UAT | Not started |  | Requires a real reviewer to judge workflow comprehension. |

## Issue Log

| ID | Severity | Workflow | Steps to reproduce | Expected | Actual | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-20260715-001 | Low | Network Plan | Query the local validation panel by accessible role/name. | Panel exposes a clear name to assistive technology. | Panel was visually titled but not an explicit named region. | Component role assertion added. | Codex | Fixed |
| UAT-20260715-002 | Low | Network Plan | Query existing component edit buttons by accessible name. | Button names include the action and target component. | Visible text included the target; explicit accessible labels were added for clarity. | Component role assertions added. | Codex | Fixed |

## Known Gaps Accepted for This Focused Pass

| Gap | Reason accepted | Mitigation | Owner | Revisit date |
| --- | --- | --- | --- | --- |
| Manual screen-reader review not completed | This pass used automated accessible-role queries only. | Complete the full checklist with VoiceOver, NVDA, JAWS, or the target deployment assistive technology. | Release owner | Before promotion |
| Mobile/tablet/high-zoom review not completed | This pass targeted component-level accessibility contracts. | Run the full responsive section of the checklist. | Release owner | Before promotion |
| Human migration-user UAT not completed | Automated tests cannot validate whether the validation findings are understandable to users. | Run at least one realistic pilot assessment with a migration user. | Migration SME | Before promotion |

## Promotion Decision

| Question | Answer |
| --- | --- |
| Is Carbon acceptable for pilot use with Streamlit fallback based on this focused pass alone? | Not decided |
| Is Carbon acceptable as the default UI based on this focused pass alone? | No |
| Are all blocker and high-severity issues closed or explicitly accepted? | No blocker/high issues were found in this focused pass |
| Are remaining medium/low issues tracked with owners? | Yes |
| Final decision | Continue Phase 6 evidence collection |
