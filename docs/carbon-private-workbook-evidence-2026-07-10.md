# Carbon Private Workbook Evidence - 2026-07-10

This records sanitized Carbon performance evidence from one local private
RVTools workbook. The raw workbook is not committed, and the ignored local JSON
evidence remains under `private-evidence/`.

Do not add workbook filenames, local paths, VM names, host names, IP addresses,
owners, application names, or screenshots containing source workbook content to
this record.

## Summary

| Field | Value |
| --- | --- |
| Review date | 2026-07-10 |
| Carbon branch | `feature/carbon-ui-network-planning-phase1` |
| Carbon commit | `1d6c624c` |
| Workbook label | `local-private-workbook` |
| Assignment rows | 168 |
| Summary parse elapsed | 1.716 seconds |
| Threshold | 45.0 seconds |
| Result | Pass |
| HTTP status | 200 |

## Commands

```bash
CARBON_PERF_CUSTOMER_WORKBOOKS='local-private-workbook=<private workbook path>' \
CARBON_PERF_CUSTOMER_SUMMARY_MAX_SECONDS=45 \
venv/bin/python scripts/collect_carbon_perf_evidence.py \
  --from-env \
  --json \
  --output private-evidence/carbon-private-workbook-evidence-20260710.json
```

```bash
CARBON_PERF_CUSTOMER_WORKBOOKS='<private workbook path>' \
CARBON_PERF_CUSTOMER_SUMMARY_MAX_SECONDS=45 \
venv/bin/python -m pytest \
  tests/test_carbon_large_workbook_performance.py::test_private_customer_workbook_summary_performance_guard \
  -q
```

## Validation

| Check | Result |
| --- | --- |
| Sanitized evidence helper | Passed |
| Private workbook summary performance guard | Passed |
| Evidence leak scan for workbook filename/path/IP patterns | Passed |
| Evidence output ignored by git | Passed |

## Promotion Interpretation

This closes one private-workbook timing capture for Carbon summary parsing. It
does not fully close the customer-scale performance promotion item by itself.
Before promotion, capture at least one additional larger private workbook that
represents the upper end of expected migration exports.
