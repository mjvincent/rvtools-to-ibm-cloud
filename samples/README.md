# Sample RVTools Workbooks

Use these workbooks to test the application before uploading production RVTools exports.

## `rvtools-small-complete.xlsx`

Generated sanitized workbook with a small three-VM inventory and all RVTools tabs known to the app:

- Core tabs: `vInfo`, `vDisk`, `vCPU`, `vMemory`, `vHost`, `vCluster`, `vNetwork`.
- Readiness/context tabs: `vSnapshot`, `vTools`, `vCD`, `vUSB`, `vHealth`, `vPartition`, `vPort`, `dvPort`, `vSwitch`, `dvSwitch`.

This is the best first workbook for confirming the app launches, parses RVTools data, renders every tab, and builds a Terraform handoff package. In the Streamlit sidebar, click `Load Sample Workbook` to use this workbook directly without browsing for the file. Open `Help And Samples` in the sidebar to compare this first-run sample with the larger workshop workbook.

Regenerate it from the repository root with:

```bash
make sample-workbook
```

or:

```bash
venv/bin/python scripts/generate_sample_workbook.py
```

## `SizingWorkshop-RVTools.xlsx`

Larger generic workshop workbook for a more realistic user test. It intentionally includes source-data issues and planning gaps that should produce readiness and preflight findings. For example, VM `wowas3` should show network readiness review because its connected source NIC lacks a usable network name. Export preflight can also flag `unknown-net` until a valid target CIDR is supplied.

Use this workbook to practice the full workflow: readiness review, remediation backlog, VM exclusion or correction decisions, wave planning, Migration Ops, and package preflight.

See `../docs/sample-findings-walkthrough.md` for the expected practice findings.
