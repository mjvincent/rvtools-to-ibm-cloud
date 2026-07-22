# Carbon Pilot Dry-Run Evidence - 2026-07-22

This records a sanitized automated dry run for Carbon pilot readiness evidence.
It is not a human UAT sign-off, hosted-runtime approval, or production
promotion decision.

## Review Summary

| Field | Value |
| --- | --- |
| Review date | 2026-07-22 |
| Evidence type | Automated local dry run |
| Branch | `codex/carbon-pilot-dry-run-evidence` |
| Starting commit | `a7bfca4` |
| Reviewer | Codex automated evidence capture |
| Workbook labels | `small-sample`, `workshop-sample` |
| Runtime | Local command validation, not hosted runtime |
| Result | Pass with remaining human/hosted evidence gaps |
| Production decision | No-go for replacing Streamlit |
| Streamlit fallback | Required for any pilot |

## Evidence Sources Used

| Evidence | Command or source | Result |
| --- | --- | --- |
| Sample and workshop parsing | `venv/bin/python -m pytest tests/test_sample_workbooks.py -q` | Included in focused run |
| Carbon handoff parity | `venv/bin/python -m pytest tests/test_carbon_handoff_parity.py -q` | Included in focused run |
| Carbon sample/workshop performance guards | `venv/bin/python -m pytest tests/test_carbon_large_workbook_performance.py -q` | Included in focused run |
| Focused dry-run command | `venv/bin/python -m pytest tests/test_sample_workbooks.py tests/test_carbon_handoff_parity.py tests/test_carbon_large_workbook_performance.py -q` | 23 passed, 1 skipped |

The skipped test is expected unless `CARBON_PERF_CUSTOMER_WORKBOOKS` is set for
private customer-scale workbook timing evidence.

## What This Dry Run Supports

- Checked-in small and workshop workbook parsing still works.
- Carbon handoff parity checks still cover representative package evidence.
- Carbon API ZIP, package preview, operational handoff, and performance guards
  are current for the checked-in sample coverage.
- Current evidence remains suitable for prototype evaluation and release
  candidate discussion.

## What This Dry Run Does Not Approve

- It does not approve Carbon as the default UI.
- It does not replace migration-user UAT.
- It does not replace keyboard-only, screen-reader, responsive, or high-zoom
  manual review.
- It does not prove hosted-runtime health checks, logs, alerts, backup/restore,
  retention, access control, support ownership, or rollback readiness.
- It does not prove customer-scale private workbook parity unless a sanitized
  private evidence packet is attached separately.

## Open Promotion Gaps

| Gap | Required next evidence |
| --- | --- |
| Human migration-user UAT | Complete the Carbon UAT session worksheet and results template with named reviewers. |
| Accessibility sign-off | Complete manual keyboard, screen-reader, responsive, and high-zoom review. |
| Hosted operations | Complete the hosted operations readiness checklist for the intended pilot runtime. |
| Customer-scale validation | Attach sanitized private workbook performance/parity evidence or an accepted exception. |
| Final decision | Complete the Carbon promotion decision packet with owners, risks, accepted gaps, and go/no-go outcome. |

## Sensitive-Data Statement

This dry-run record uses only checked-in sample labels and command summaries. It
does not include raw RVTools rows, private workbook paths, full VM names, IP
addresses, CIDR plans, owner names, application names, screenshots with
sensitive values, IBM Cloud credentials, Terraform state, API keys, or other
secrets.
