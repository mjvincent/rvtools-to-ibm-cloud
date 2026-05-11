# Migration Readiness Assessment

## Purpose
The migration readiness assessment helps teams find source-side cleanup items before moving VMware workloads to IBM Cloud Virtual Servers for VPC.

The assessment is advisory. It does not change generated Terraform resources, block ZIP generation, convert VMDK files, call migration tools, or automate cutover.

## Status Values
### `Ready`
No migration readiness findings were detected from the available RVTools tabs. Continue with normal image, replication, validation, and cutover planning.

### `Review`
The VM has findings that should be validated by application, VMware, or migration owners. Examples include smaller active snapshots, VMware Tools concerns, guest heartbeat/application status concerns, powered-off source state, or non-severe health warnings.

### `Blocked`
The VM has findings that should be remediated before export, replication, image import, or cutover scheduling. Examples include large active snapshot footprints, mounted ISO/CD media, attached USB devices, or severe health findings when available.

## RVTools Inputs
* `vSnapshot`: Snapshot count and total snapshot size.
* `vTools`: VMware Tools status, upgrade flag, application status, heartbeat status, and operation readiness.
* `vCD`: Connected or starts-connected CD/DVD and ISO media.
* `vUSB`: Connected USB devices.
* `vHealth`: Health warnings when a finding can be matched to a VM name or key.
* `vInfo`: Power state, used to flag powered-off VMs for scope validation.

## Dashboard Fields
* `Migration Readiness`: `Ready`, `Review`, or `Blocked`.
* `Migration Readiness Reasons`: Human-readable explanation of findings.
* `Snapshot Count`: Number of active snapshots found for the VM.
* `Snapshot Size MiB`: Total snapshot size found for the VM.
* `VMware Tools Status`: Consolidated tools, upgrade, heartbeat, and app status.
* `Mounted Media`: Connected CD/DVD or ISO devices.
* `USB Devices`: Count of connected USB devices.
* `Health Warnings`: Count of matched RVTools health warnings.

## Handoff Files
* `migration-manifest.json` includes a `migration_readiness` object per VM.
* `vm-mapping.csv` includes readiness summary columns for spreadsheet review.
* `readiness-findings.csv` includes one row per finding with severity, source tab, evidence, and recommended action.
* `migration-runbook.md` includes readiness review and remediation steps.

## Limitations
RVTools data is inventory metadata. It cannot confirm application consistency, prove that a snapshot is safe to delete, inspect VMDK contents, validate in-guest agents, or determine business criticality. Treat readiness findings as a planning queue that must be confirmed with the workload owner and VMware administrator.

`Ready` means no findings were detected from the available tabs. It does not guarantee that a VM is ready for production cutover.
