# Sample RVTools Workbooks

Use these workbooks to test the application before uploading production RVTools exports.

## `rvtools-small-complete.xlsx`

Generated sanitized workbook with a small three-VM inventory and all RVTools tabs known to the app:

- Core tabs: `vInfo`, `vDisk`, `vCPU`, `vMemory`, `vHost`, `vCluster`, `vNetwork`.
- Readiness/context tabs: `vSnapshot`, `vTools`, `vCD`, `vUSB`, `vHealth`, `vPartition`, `vPort`, `dvPort`, `vSwitch`, `dvSwitch`.

This is the best first upload for confirming the app launches, parses RVTools data, renders every tab, and builds a Terraform handoff package.

Regenerate it from the repository root with:

```bash
make sample-workbook
```

or:

```bash
venv/bin/python scripts/generate_sample_workbook.py
```

## `SizingWorkshop-RVTools.xlsx`

Larger generic workshop workbook for a more realistic user test. It intentionally includes source-data issues that should produce readiness and preflight findings. For example, VM `wowas3` has no connected NIC with a usable source network, so the app should recommend correcting the source RVTools/vSphere data or excluding that VM before packaging.

Use this workbook to practice the full workflow: readiness review, remediation backlog, VM exclusion or correction decisions, wave planning, Migration Ops, and package preflight.
