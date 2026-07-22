# Carbon Real-Workbook Parity Evidence

**Evidence date**: 2026-07-22
**Branch**: `codex/carbon-real-workbook-parity-evidence`
**Decision use**: Carbon promotion evidence only. Streamlit remains the supported production UI until all promotion gates are closed.

This page records the checked-in workbook evidence that supports Carbon's
current handoff parity claim. It is intended to make the Carbon replacement
conversation easier to review without asking a reviewer to rediscover the test
suite from scratch.

## Workbooks Covered

| Workbook | Purpose | Evidence |
| --- | --- | --- |
| `samples/rvtools-small-complete.xlsx` | Clean first-run sample used by new users and smoke tests. | Parser summary, operational overlay parity, API ZIP inventory, package preview-vs-ZIP parity, and performance guard coverage. |
| `samples/SizingWorkshop-RVTools.xlsx` | Larger workshop exercise with expected readiness and preflight findings. | Parser summary, unknown-network subset parity, operational edge subset parity, API ZIP handoff evidence, and performance guard coverage. |

## Executable Evidence Map

| Evidence area | Test coverage |
| --- | --- |
| Sample and workshop parser acceptance | `tests/test_sample_workbooks.py` |
| Sample and workshop summary/performance guardrails | `tests/test_carbon_large_workbook_performance.py` |
| Exact handoff parity for synthetic and edge fixtures | `tests/test_carbon_handoff_parity.py` |
| Workshop real-workbook unknown-network parity | `test_carbon_workshop_workbook_unknown_network_subset_matches_streamlit_handoff` |
| Workshop operational edge parity for overrides, exclusions, remediation, image import, wave/cutover metadata, and cutover readiness | `test_carbon_workshop_operational_edge_subset_matches_streamlit_handoff` |
| Small-sample operational overlay parity | `test_carbon_sample_workbook_operational_overlays_match_streamlit_handoff` |
| Small-sample API ZIP handoff inventory | `test_carbon_sample_workbook_api_zip_matches_expected_handoff_inventory` |
| Workshop API ZIP operational handoff evidence | `test_carbon_workshop_api_zip_preserves_operational_handoff_evidence` |
| Carbon package preview matches generated ZIP content | `test_carbon_package_preview_matches_api_zip_contents` |

## What This Proves

- Carbon can ingest the bundled small sample and the larger workshop workbook
  through the shared parser/API path.
- Carbon package generation includes the expected Streamlit handoff inventory
  plus documented Carbon-only `network-plan.json` state.
- Representative real-workbook rows preserve operational handoff evidence for
  VM decisions, remediation, image import planning, cutover readiness, planning
  state, manifest references, and mapping/readiness exports.
- The Carbon package preview is checked against the actual downloadable ZIP so
  users are not shown a different inventory than the one they receive.
- Performance guards cover the checked-in samples and generated large Carbon
  state shapes.

## Known Limits

- The checked-in workbooks do not replace private customer-scale validation.
- The workshop workbook provides a larger representative exercise, but it is
  not a complete substitute for unusual customer RVTools exports.
- Accessibility, manual UAT, hosted-runtime operations, support ownership, and
  rollback authority still need formal closure before Carbon can replace
  Streamlit.
- Intentional Carbon-only output, currently `network-plan.json`, must remain
  documented in the parity tracker and covered by inventory drift tests.

## Reproduce

Run the focused evidence checks from the repository root:

```bash
venv/bin/python -m pytest \
  tests/test_sample_workbooks.py \
  tests/test_carbon_large_workbook_performance.py \
  tests/test_carbon_handoff_parity.py \
  tests/test_carbon_real_workbook_parity_evidence_docs.py \
  -q
```

For a full promotion-readiness pass, also run the standard Python, Carbon
TypeScript, Jest, Playwright, Docker Compose, and Terraform package validation
commands documented in [Carbon Promotion Gate Review](carbon-promotion-gate-review.md)
and [Testing](testing.md).
