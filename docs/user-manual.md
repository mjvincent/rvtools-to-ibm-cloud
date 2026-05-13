# RVTools to IBM Cloud VPC User Manual

## Purpose
This manual explains how to use the RVTools to IBM Cloud VPC application, what each web interface field means, and how to interpret every major file generated in the Terraform ZIP bundle.

The application converts VMware RVTools XLSX exports into an IBM Cloud VPC Terraform project and a migration handoff package. It helps teams plan target infrastructure, right-size compute, map disks and NICs, assess image readiness, and identify source-side migration cleanup items.

This tool does not move VMware workloads by itself. It does not convert VMDK files, upload images to IBM Cloud Object Storage, import custom images, call RackWare, execute Terraform, or perform application cutover.

## Table of Contents
- [Audience](#audience)
- [Application Outcomes](#application-outcomes)
- [Required Inputs](#required-inputs)
- [Optional RVTools Inputs](#optional-rvtools-inputs)
- [Installation and Launch](#installation-and-launch)
- [End-to-End Workflow](#end-to-end-workflow)
- [Sidebar Settings](#sidebar-settings)
- [Dashboard Metrics](#dashboard-metrics)
- [Assessment Quality](#assessment-quality)
- [Pricing Settings](#pricing-settings)
- [Terraform Overrides](#terraform-overrides)
- [Main Table Reference](#main-table-reference)
- [Editable Columns](#editable-columns)
- [Read-Only Columns](#read-only-columns)
- [Readiness Assessments](#readiness-assessments)
- [Build Terraform Project](#build-terraform-project)
- [Generated ZIP Contents](#generated-zip-contents)
- [Terraform Output Reference](#terraform-output-reference)
- [Migration Handoff Files](#migration-handoff-files)
- [Recommended Migration Planning Workflow](#recommended-migration-planning-workflow)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Glossary](#glossary)
- [Related Documentation](#related-documentation)

## Audience
This manual is intended for:
- Cloud architects planning IBM Cloud VPC target environments.
- VMware administrators exporting RVTools inventory data.
- Migration teams preparing image import, replication, or migration-tool workflows.
- Application owners reviewing migration scope and readiness.
- FinOps or infrastructure teams reviewing right-sizing and cost estimates.

## Application Outcomes
After uploading an RVTools XLSX export, the application can produce:
- A Streamlit assessment workbench with focused Overview, Readiness, VM Review, Networks, Storage, and Export tabs.
- A per-VM decision table with right-sizing recommendations, override controls, source metadata, disk mapping, network mapping, and readiness assessments available through focused views.
- A downloadable business case CSV.
- A downloadable Terraform ZIP bundle.
- A migration handoff package inside the ZIP for migration planning and downstream tooling.

## Required Inputs
The application expects a standard RVTools `.xlsx` workbook.

The following worksheets are required for the core workflow:

| RVTools worksheet | Purpose |
| --- | --- |
| `vInfo` | VM inventory, CPU, memory, power state, source network, guest OS, host, cluster, datacenter, and general VM metadata. |
| `vDisk` | Disk capacity and disk metadata. Used for total storage, boot/data disk split, and per-disk handoff mapping. |
| `vCPU` | CPU performance metrics. Used for contention detection and right-sizing safety logic. |
| `vMemory` | Memory telemetry. Used for memory readiness, pressure detection, and conservative RAM sizing. |
| `vHost` | Host CPU speed and core capacity. Used for N+1 headroom and vCPU-to-pCore ratio. |
| `vCluster` | Cluster CPU capacity. Used for N+1 headroom calculation. |
| `vNetwork` | NIC, source network, IP, MAC, adapter, switch, and connection metadata. Used for multi-NIC mapping and target subnet/security group mapping. |

## Optional RVTools Inputs
These worksheets improve readiness and storage planning context but are not required for Terraform generation:

| RVTools worksheet | Purpose |
| --- | --- |
| `vSnapshot` | Detects active snapshots and total snapshot size. Large snapshot footprints can block migration readiness. |
| `vTools` | Detects VMware Tools status, upgrade status, heartbeat, application status, and operation readiness. |
| `vCD` | Detects connected or starts-connected CD/DVD and ISO media. Connected media can block migration readiness. |
| `vUSB` | Detects connected USB devices. USB dependencies can block migration readiness. |
| `vHealth` | Provides RVTools health findings where they can be associated with a workload. |
| `vPartition` | Provides partition labels, capacity, consumed space, free space, and free percentage for storage planning review. |

If an optional readiness tab is missing, the related readiness checks are skipped. Missing optional tabs do not block ZIP generation.
The Assessment Quality report still records missing optional tabs so reviewers can see when migration readiness confidence is based on partial workbook coverage.

## Installation and Launch
Run the application from the repository root.

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Start the Streamlit application:

```bash
streamlit run app.py
```

3. Open the Streamlit URL shown in the terminal.

4. Upload an RVTools XLSX export in the sidebar.

## End-to-End Workflow
1. Export the VMware inventory from RVTools as an XLSX workbook.
2. Launch the Streamlit app.
3. Select the target IBM Cloud region and zone.
4. Select the right-sizing threshold.
5. Enter the project name.
6. Upload the RVTools workbook.
7. Review the `Overview` tab for estate health and recommended next actions.
8. Review the `Readiness` tab and resolve `Blocked` items before migration execution.
9. Use `VM Review` to adjust exclusion, profile, storage tier, network, subnet, and security group decisions.
10. Use `Networks` and `Storage` to confirm placement and disk planning details.
11. Use `Export` to confirm VPC name, address prefix strategy, deployment target, and subnet CIDRs.
12. Download the business case CSV if needed.
13. Click `Build Terraform Project`.
14. Download the Terraform ZIP bundle.
15. Review the generated Terraform and migration handoff files before applying or sharing with migration tooling.


## Assessment Workbench Tabs
### Overview
Shows the estate-level health summary, in-scope and excluded VM counts, monthly estimate, potential savings, blocker count, assessment quality summary, and recommended next actions. Start here after each upload.

### Readiness
Groups image, migration, and memory readiness by `Blocked`, `Review`, and `Ready`. Blocked and Review rows are sorted first so remediation planning starts with the highest-impact items.

### VM Review
Shows the main decision fields instead of every generated column. Use this tab to exclude VMs and adjust profile, storage tier, network, subnet, or security group intent. Advanced generated fields remain available in the expander for audit and troubleshooting.

### Networks
Shows discovered networks, default CIDRs, VM network placement, multi-NIC count, and unknown network signals. Use this before export to confirm subnet and security group intent.

### Storage
Shows total storage, data disk counts, boot/data planning signals, partition coverage, storage tier choices, and image readiness context. Use this to validate data disk volume planning before package generation.

### Export
Contains Terraform deployment settings, custom CIDR fields, package readiness metrics, business case CSV download, and Terraform ZIP build/download controls.

## Sidebar Settings
### Target IBM Region
The IBM Cloud region where the target VPC infrastructure should be generated.

Current options:
- `us-south`
- `us-east`
- `eu-gb`
- `jp-tok`

### Target IBM Zone
The IBM Cloud zone used for subnet, VSI, and volume placement. The available zone list changes based on the selected region.

### Standard Thresholds
Controls the utilization factor used for right-sizing:

| Option | Meaning |
| --- | --- |
| `Conservative (30%)` | More aggressive reduction of CPU requirement. Best for early planning only. |
| `IBM Standard (40%)` | Default balanced setting. |
| `Moderate (50%)` | Retains more headroom than the default. |
| `Aggressive (70%)` | Keeps more of the original CPU allocation. |
| `Custom` | Lets the user choose a custom percentage from 1 to 100. |

The selected threshold is used unless a VM is detected as resource constrained. If a VM shows CPU contention or throttling, the application uses a safety match behavior to reduce migration risk.

### Project Name
The project name is used in generated Terraform variable values, tags, filenames, and handoff context.

### Generate Security Groups
When enabled, the networking module generates security groups and the VSI module references them. When disabled, generated security group references use `N/A` in the handoff files and security group resources are omitted.

### Pricing Mode
Controls the source of IBM Cloud profile and pricing data.

| Value | Meaning |
| --- | --- |
| `Static fallback` | Uses bundled profile and price estimates. Works offline and without IBM credentials. |
| `Cached IBM catalog` | Uses `data/ibm_vpc_pricing_cache.json` if present, otherwise falls back to static pricing. |
| `Live IBM profile discovery` | Uses IBM Cloud VPC profile discovery when `IBMCLOUD_API_KEY` is available. Exact pricing is still marked by confidence metadata. |

Pricing mode affects estimated cost and profile options, but does not change generated Terraform resource structure.

For live mode, set `IBMCLOUD_API_KEY` in the shell that starts Streamlit or in a local `.env` file at the repository root. Restart Streamlit after creating or changing `.env`.

### Download Business Case CSV
The Export tab downloads the current full planning table as a CSV. This file is useful for stakeholder review before building the full Terraform project.

## Dashboard Metrics
### Total VMs
The total number of VMs parsed from the RVTools workbook.

### Monthly Spend
Estimated monthly IBM Cloud cost for VMs that are not excluded. This combines compute and storage estimates from the current recommendations and overrides.

### N+1 Headroom
Estimated cluster CPU headroom after subtracting the largest host capacity and current VM CPU demand. It is intended as a planning signal, not a formal capacity guarantee.

### Potential Savings
The difference between a conservative baseline estimate and the current right-sized estimate for non-excluded VMs.

### Zombie VMs
Count of VMs flagged as likely underutilized. A VM can be flagged when CPU usage is very low and observed MHz demand is low.

### Image Ready
Count of non-excluded VMs with no detected custom image planning blockers.

### Image Review
Count of non-excluded VMs that need image planning review.

### Image Blocked
Count of non-excluded VMs with detected custom image blockers, such as a boot disk exceeding IBM Cloud VPC custom image limits.

### Migration Ready
Count of non-excluded VMs with no detected operational migration readiness findings from the available RVTools tabs.

### Migration Review
Count of non-excluded VMs that need owner review before migration planning.

### Migration Blocked
Count of non-excluded VMs with source-side findings that should be remediated before export, replication, image import, or cutover scheduling.

### Memory Ready
Count of non-excluded VMs with no detected memory pressure or memory sizing constraints.

### Memory Review
Count of non-excluded VMs that need owner review for memory sizing, reservations, limits, hot-add, or light memory pressure.

### Memory Blocked
Count of non-excluded VMs with severe memory pressure or memory limits that should be remediated before resizing.

## Assessment Quality
The `Overview` tab includes an advisory Assessment Quality report. It explains how complete the uploaded RVTools workbook is before teams rely on sizing, readiness, network, or storage outputs.

The report does not block package generation and does not change readiness statuses, Terraform resources, VM exclusions, or cost estimates.

### Overall Confidence
The conservative rollup across inventory, storage, network, memory, and migration readiness confidence.

| Value | Meaning |
| --- | --- |
| `High` | The relevant worksheets are present and populated. |
| `Medium` | The app can continue with fallback data or partial coverage. Review before using outputs for migration waves. |
| `Low` | One or more important planning areas are missing, empty, or based on no optional readiness coverage. |

### Required Tabs
Shows how many required worksheets are present and populated out of the required set: `vInfo`, `vDisk`, `vCPU`, `vMemory`, `vHost`, `vCluster`, and `vNetwork`.

### Optional Readiness Tabs
Shows how many optional readiness worksheets are present and populated out of `vSnapshot`, `vTools`, `vCD`, `vUSB`, and `vHealth`.

Missing optional readiness tabs lower migration readiness confidence, but they do not create `Blocked` findings by themselves.

### Missing or Empty Tabs
Counts worksheets that are missing from the workbook or present with no rows. Open the worksheet coverage details expander to see the tab name, category, row count, confidence, and planning impact.

## Pricing Settings
The app records pricing metadata so users can understand whether estimates came from static fallback data, a cache file, or live IBM profile discovery.

### Pricing Source
Where the price/profile data came from.

### Pricing Confidence
How trustworthy the price/profile mapping is. Examples include:
- `fallback-static`
- `cached-exact`
- `profile-live-price-static`
- `profile-live-price-missing`

### Pricing Last Updated
Timestamp from the cache or live discovery process when available.

### Profile Hourly
Hourly profile price used in the monthly compute estimate.

## Terraform Overrides
The `Export` tab controls target infrastructure settings.

### VPC Name
The target IBM Cloud VPC name used in generated Terraform.

### Address Prefix Strategy
Controls how VPC address prefixes are generated:

| Value | Meaning |
| --- | --- |
| `manual` | Generates explicit address prefixes and subnet CIDRs. This is best for migrations that need predictable addressing or IP parity planning. |
| `auto` | Lets IBM Cloud assign address prefixes automatically. This is useful for exploratory or greenfield deployments. |

### Deployment Target
Controls generated Terraform state behavior:

| Value | Meaning |
| --- | --- |
| `Plain CLI` | Includes local backend behavior suitable for local Terraform CLI execution. |
| `IBM Schematics` | Omits the local backend block so IBM Schematics can manage Terraform state. |

### Custom CIDRs per Subnet
For each discovered network, the app creates a CIDR input. These CIDRs are used for generated VPC address prefixes and subnets.

Review these carefully before applying Terraform. The generated CIDRs are planning defaults and may need adjustment to fit the target IBM Cloud network design.

## Main Table Reference
The `VM Review` tab is the primary decision and override surface. It shows the key fields by default, while advanced generated fields remain available in an expander. Some columns are editable, while others are generated from RVTools data or application logic.

## Editable Columns
### `Exclude?`
When checked, the VM is excluded from the Terraform ZIP and migration handoff files. Powered-off VMs are checked by default because they usually require scope validation.

### `IBM Profile`
The recommended IBM Cloud VSI profile. This can be edited directly, but the preferred override field is `Override Profile` because it preserves the original recommendation in handoff files.

### `Override Profile`
Optional user-selected VSI profile. When set, generated Terraform uses this profile instead of the recommendation.

### `Storage Tier`
Recommended IBM Cloud block storage tier. This can be edited directly, but the preferred override field is `Override Storage Tier`.

### `Override Storage Tier`
Optional user-selected block storage tier. When set, generated data disk volumes use this tier.

Current storage tier options:
- `3iops-tier`
- `5iops-tier`
- `10iops-tier`

### `Subnet`
Target subnet mapping for the VM primary network. By default this references the generated networking module output for the discovered source network.

### `Security Group`
Target security group mapping for the VM primary network. When security group generation is enabled, this references the generated networking module security group output.

### `Network`
Primary source network selected for target subnet/security group mapping. When `vNetwork` includes NIC detail, this is derived from the first connected NIC.

## Read-Only Columns
### `VM Key`
Stable internal key used to correlate rows across RVTools tabs. It is usually based on VM name, VM UUID, or VM ID.

### `VM Name`
Display name used in the UI, CSV files, manifest, and generated naming context.

### `Power State`
Source VM power state from RVTools.

### `Source IP`
Primary source IP address.

### `NIC Count`
Number of discovered NICs for the VM.

### `Primary Network`
Source network for the primary connected NIC.

### `Primary IP`
IP address for the primary connected NIC.

### `Guest OS`
Guest operating system from RVTools metadata.

### `Disk Count`
Number of discovered disks for the VM.

### `Data Disk Count`
Number of non-boot disks. The first discovered disk is treated as the boot disk; additional disks are treated as data disks.

### `Firmware`
Source firmware value when available. Used for image readiness planning.

### `Boot Disk GB`
Inferred boot disk size in GB. Used for IBM Cloud custom image readiness checks.

### `Guest Customization`
Expected guest initialization requirement:
- Windows workloads generally require `cloudbase-init`.
- Linux workloads generally require `cloud-init`.
- Unrecognized operating systems require validation.

### `Image Readiness`
Advisory image planning status: `Ready`, `Review`, or `Blocked`.

### `Readiness Reasons`
Explanation for the image readiness status.

### `Migration Readiness`
Advisory migration planning status: `Ready`, `Review`, or `Blocked`.

### `Migration Readiness Reasons`
Explanation of operational migration readiness findings.

### `Snapshot Count`
Number of active snapshots detected from `vSnapshot`.

### `Snapshot Size MiB`
Total active snapshot size detected from `vSnapshot`.

### `VMware Tools Status`
Consolidated VMware Tools, upgrade, heartbeat, application, and operation readiness status from `vTools`.

### `Mounted Media`
Connected or starts-connected CD/DVD or ISO media from `vCD`.

### `USB Devices`
Count of connected USB devices from `vUSB`.

### `Health Warnings`
Count of matched RVTools health warnings from `vHealth`.

### `Memory Readiness`
Advisory memory status: `Ready`, `Review`, or `Blocked`.

### `Memory Readiness Reasons`
Explanation of memory pressure, constraints, or sizing choices.

### `Configured Memory MiB`
Configured source VM memory from `vMemory` or `vInfo`.

### `Active Memory MiB`
Active memory observed in RVTools `vMemory`.

### `Consumed Memory MiB`
Consumed memory observed in RVTools `vMemory`.

### `Ballooned Memory MiB`
Memory ballooning observed in RVTools `vMemory`.

### `Swapped Memory MiB`
Swapped memory observed in RVTools `vMemory`.

### `Memory Reservation MiB`
Configured memory reservation from RVTools.

### `Memory Limit MiB`
Configured memory limit from RVTools. A positive limit below configured memory is treated as a blocker.

### `Memory Hot Add`
Indicates whether memory hot-add is enabled for the source VM.

### `Sizing Memory MiB`
Memory value used by the recommendation engine for IBM Cloud profile selection.

### `Memory Sizing Basis`
Explains why the sizing memory value was chosen.

### `Pricing Source`
Where the pricing value came from.

### `Pricing Confidence`
How confidently the app mapped the price to the profile.

### `Pricing Last Updated`
Timestamp for cached or live pricing metadata when available.

### `Profile Hourly`
Hourly profile value used in compute cost estimates.

### `Host`
Source ESXi host.

### `Cluster`
Source VMware cluster.

### `Datacenter`
Source VMware datacenter.

### `Original Specs`
Original VM CPU and memory allocation.

### `Compute (Mo)`
Estimated monthly compute cost.

### `Storage (Mo)`
Estimated monthly storage cost.

### `Baseline Cost (Mo)`
Estimated monthly cost using a conservative baseline sizing model.

### `Savings (Mo)`
Estimated monthly savings compared with the baseline.

### `Monthly Cost`
Estimated total monthly cost for the recommended or overridden target configuration.

### `Right-Sized`
Indicates whether the recommendation reduced CPU compared with the original VM allocation.

### `Total Storage GB`
Total discovered VM storage in GB.

### `Data Status`
Health and right-sizing signal. Examples include:
- `Healthy`
- `Missing CPU`
- `Missing Storage`
- `High Contention`
- `CPU Throttled`
- `Zombie VM`

### `v_p_Ratio`
Estimated vCPU-to-physical-core ratio for the VM host.

### `Ready_Pct`
CPU Ready percentage from RVTools.

### `Overall_MHz`
Observed CPU demand from RVTools.

## Readiness Assessments
The application includes three separate readiness layers.

### Image Readiness
Image readiness focuses on IBM Cloud VPC custom image planning.

| Status | Meaning |
| --- | --- |
| `Ready` | No metadata blockers were found. The VM still requires conversion, staging, import, and validation. |
| `Review` | Metadata or layout requires validation before image planning. |
| `Blocked` | A detected image planning blocker should be resolved before image import planning. |

Common `Review` reasons:
- Guest OS missing or unrecognized.
- Firmware missing.
- Boot disk below 10 GB.
- Multiple disks detected.
- VM is powered off.

Common `Blocked` reasons:
- Boot disk exceeds the IBM Cloud VPC custom image size limit.

### Migration Readiness
Migration readiness focuses on source-side operational cleanup before export, replication, image import, or cutover.

| Status | Meaning |
| --- | --- |
| `Ready` | No migration readiness findings were detected from available RVTools tabs. |
| `Review` | Owner validation is needed before scheduling migration activity. |
| `Blocked` | Remediation should occur before export, replication, image import, or cutover scheduling. |

Common `Review` reasons:
- Smaller active snapshots.
- VMware Tools not running, old, upgradeable, or missing.
- Guest heartbeat or application status concerns.
- Powered-off VM scope validation.
- Non-severe RVTools health warning.

Common `Blocked` reasons:
- Large active snapshot footprint.
- Connected ISO/CD media.
- Attached USB devices.
- Severe health warning when available.

### Memory Readiness
Memory readiness focuses on RAM pressure and constraints before profile sizing.

| Status | Meaning |
| --- | --- |
| `Ready` | No memory pressure or memory sizing constraints were detected. |
| `Review` | Memory sizing should be validated because of reservations, hot-add, light pressure, or conservative reduction. |
| `Blocked` | Severe swapping/ballooning or a memory limit below configured memory should be remediated before resizing. |

Common `Review` reasons:
- Memory reservation detected.
- Memory hot-add enabled.
- Active memory is materially below configured memory and a conservative reduction was applied.
- Light swapping or ballooning exists.

Common `Blocked` reasons:
- Severe swapping.
- Severe ballooning.
- Memory limit below configured memory.

## Build Terraform Project
On the `Export` tab, click `Build Terraform Project` after reviewing readiness, VM decisions, network placement, storage planning, and Terraform settings.

The app packages:
- Terraform root files.
- Networking module files.
- Storage module files.
- VSI module files.
- Migration handoff files.
- Image import placeholder variables.
- Generated runbook.

After the build completes, click `Download Terraform Bundle`.

## Generated ZIP Contents
The ZIP bundle contains two categories of output:
- Terraform files for the IBM Cloud VPC target foundation.
- Handoff files for migration planning and downstream migration tools.

| File | Purpose |
| --- | --- |
| `main.tf` | Root Terraform module wiring. |
| `variables.tf` | Root Terraform variables. |
| `outputs.tf` | Root Terraform outputs. |
| `terraform.tfvars` | Project, region, and zone values. |
| `modules/networking/main.tf` | VPC, address prefixes, subnets, and security groups. |
| `modules/networking/variables.tf` | Networking module variables. |
| `modules/networking/outputs.tf` | Networking module outputs. |
| `modules/storage/main.tf` | Data disk block volume resources. |
| `modules/storage/variables.tf` | Storage module variables. |
| `modules/storage/outputs.tf` | Storage module outputs. |
| `modules/vsi/main.tf` | VSI resources, network interfaces, and data volume attachments. |
| `modules/vsi/variables.tf` | VSI module variables. |
| `modules/vsi/outputs.tf` | VSI module outputs. |
| `migration-manifest.json` | Structured source-to-target migration handoff document. |
| `vm-mapping.csv` | Spreadsheet-friendly VM-level migration mapping. |
| `nic-mapping.csv` | Per-NIC source-to-target network mapping. |
| `disk-mapping.csv` | Per-disk boot/data mapping. |
| `partition-mapping.csv` | Per-partition storage planning detail from RVTools `vPartition`. |
| `memory-readiness.csv` | VM-level memory pressure, constraint, and sizing review. |
| `readiness-findings.csv` | Row-level migration readiness findings and remediation actions. |
| `assessment-quality.json` | Structured RVTools worksheet coverage and confidence report. |
| `assessment-quality.csv` | Spreadsheet-friendly worksheet coverage and confidence report. |
| `image-import-variables.tfvars.example` | Placeholder map for IBM Cloud custom image IDs after image import. |
| `migration-runbook.md` | Operational runbook for migration planning and execution. |

## Terraform Output Reference
### Root Module
The root module wires together networking, storage, and VSI modules.

### Networking Module
Generates:
- IBM Cloud VPC.
- VPC address prefixes.
- Subnets.
- Security groups when enabled.
- Outputs consumed by the VSI module.

### Storage Module
Generates IBM Cloud block volumes for non-boot data disks. Boot disks are expected to be covered by the custom image or migration-tool workflow.

Volume capacity is based on `vDisk` capacity. Optional `vPartition` data is exported for planning review but does not change generated Terraform storage resources.

### VSI Module
Generates IBM Cloud Virtual Server for VPC resources.

The first connected NIC is rendered as the primary network interface. Additional connected NICs are rendered as secondary network interfaces. Disconnected NICs remain visible in handoff files but are not generated as active Terraform interfaces.

The VSI module also generates data volume attachments for storage module outputs.

## Migration Handoff Files
### `migration-manifest.json`
A structured JSON document containing project settings and per-VM source, target, migration, assessment, image readiness, migration readiness, memory readiness, disk, and NIC data.

Use it for:
- Automation.
- Migration factory workflows.
- Custom scripts.
- Tool-neutral handoff to migration teams.

### `vm-mapping.csv`
A VM-level spreadsheet for workshop review.

Use it to review:
- Source VM metadata.
- Target profile and storage tier.
- Image readiness.
- Migration readiness.
- Memory readiness and sizing memory.
- Pricing source and confidence.
- Target subnet and security group.
- Estimated cost and savings.

### `nic-mapping.csv`
A per-NIC mapping file.

Use it to review:
- Primary NIC.
- Secondary NICs.
- Disconnected NICs.
- Source network.
- Source IP.
- MAC address.
- Target subnet.
- Target security group.

### `disk-mapping.csv`
A per-disk mapping file.

Use it to review:
- Boot disk vs data disk role.
- Source disk path and capacity.
- Target data volume names.
- Target attachment resource names.
- Storage tier.
- Partition count and summarized partition free-space context when `vPartition` is available.

### `partition-mapping.csv`
A row-level partition mapping file.

Use it to review:
- Source partition labels or drive paths.
- Partition capacity, consumed space, free space, and free percentage.
- Whether a partition matched a source disk by `Disk Key`.
- Unmatched partition rows that need VMware owner validation.

### `memory-readiness.csv`
A VM-level memory readiness and sizing file.

Use it to review:
- Configured, active, and consumed memory.
- Swapping and ballooning.
- Memory reservations and limits.
- Memory hot-add status.
- Sizing memory used for profile selection.
- Recommended, overridden, and effective profile.

### `readiness-findings.csv`
A row-level migration readiness worklist.

Use it to assign owners for:
- Snapshot cleanup.
- ISO/CD disconnect.
- USB dependency removal.
- VMware Tools remediation.
- Health warning review.

### `assessment-quality.json` and `assessment-quality.csv`
Workbook-level quality reports showing required and optional RVTools tab coverage, row counts, confidence, and planning impact.

Use them to review:
- Missing or empty required tabs.
- Missing optional readiness tabs.
- Whether network or storage planning used fallback metadata from `vInfo`.
- Overall confidence before sharing migration wave plans.

### `image-import-variables.tfvars.example`
A placeholder file for custom image IDs after conversion and import.

This file is not automatically consumed by the current VSI module. It provides a stable place to capture image IDs for a later image-import automation phase.

### `migration-runbook.md`
A generated operational runbook customized with project, region, zone, VPC name, deployment target, and recommended workflow.

## Recommended Migration Planning Workflow
1. Review `vm-mapping.csv` with infrastructure, application, security, and migration owners.
2. Confirm which VMs are in scope.
3. Exclude VMs that should not be migrated.
4. Resolve `Image Readiness = Blocked` items.
5. Resolve `Memory Readiness = Blocked` items.
6. Resolve `Migration Readiness = Blocked` items.
7. Assign owners for `Review` items.
8. Review `memory-readiness.csv` for profile sizing validation.
9. Review `nic-mapping.csv` for primary and secondary interface placement.
10. Review `disk-mapping.csv` for data disk placement and sizing.
11. Review `partition-mapping.csv` for partition free-space context and unmatched partition rows.
12. Confirm IBM Cloud region, zone, VPC, subnet, and security group design.
13. Confirm profile and storage tier overrides.
14. Convert, replicate, or migrate images using the selected migration method.
15. Upload converted images to IBM Cloud Object Storage when using custom image import.
16. Import images as IBM Cloud VPC custom images.
17. Record custom image IDs.
18. Review generated Terraform.
19. Apply Terraform using local CLI or IBM Schematics.
20. Validate boot, network, storage attachment, monitoring, backup, security, and application health.
21. Execute DNS, load balancer, IP, or application cutover steps.

## Limitations
The application is a planning and generation tool. It does not:
- Guarantee application compatibility.
- Inspect VMDK contents.
- Convert VMDK files.
- Upload images to IBM Cloud Object Storage.
- Import IBM Cloud custom images.
- Call RackWare or other migration tooling.
- Execute Terraform.
- Validate IBM Cloud quota.
- Validate target IP availability.
- Validate every provider profile in every region.
- Guarantee exact IBM billing catalog pricing unless pricing confidence indicates a trusted exact source.
- Prove that `cloud-init` or `cloudbase-init` is installed inside the guest.
- Decide application migration waves automatically.

Treat all recommendations as planning guidance that must be reviewed by the appropriate technical owners.

## Troubleshooting
### Upload fails or sheets are missing
Confirm the file is an RVTools XLSX export and not a CSV or manually edited workbook. Confirm the required worksheets are present.

### Assessment quality confidence is low
Open the Assessment Quality details in `Overview` or review `assessment-quality.csv`. Re-export RVTools with required worksheets and optional readiness tabs when possible.

### A VM has missing CPU data
Check the `vCPU` worksheet. Missing CPU metrics can cause the VM to be flagged with `Missing CPU`.

### A VM has missing storage data
Check the `vDisk` worksheet and confirm capacity columns are populated.

### Partition data is missing or unmatched
Check the optional `vPartition` worksheet. Rows with missing `Disk Key` values may appear as unmatched partition records when they cannot be safely correlated to a `vDisk` row.

### Networks show as `unknown`
Check `vNetwork` and `vInfo` for populated network or port group fields. If NIC rows are missing, the app falls back to available `vInfo` network data.

### Migration readiness is mostly `Ready`
Confirm optional tabs such as `vSnapshot`, `vTools`, `vCD`, `vUSB`, and `vHealth` were included in the RVTools export.

### Memory readiness is mostly `Review`
Check `vMemory`. Reservations, memory hot-add, and conservative active-memory reductions can trigger `Review`.

### Memory readiness is `Blocked`
Check `vMemory` for swapping, ballooning, or a positive memory limit below configured memory.

### Many VMs are marked `Review` for VMware Tools
Review the `vTools` worksheet. Upgradeable tools, missing tools, heartbeat issues, application status concerns, or operation readiness concerns can trigger `Review`.

### VMs are marked `Blocked` for mounted media
Check the `vCD` worksheet. Disconnect ISO/CD media before migration planning.

### VMs are marked `Blocked` for snapshots
Check `vSnapshot`. Large snapshot footprints should be consolidated or removed before export, replication, or image import planning.

### Terraform CIDRs are not correct
Use the custom CIDR fields in `Terraform Overrides` before building the ZIP.

### Terraform should not generate security groups
Disable `Generate Security Groups` in the sidebar before building the ZIP.

### The ZIP was built before overrides were updated
Change the overrides and click `Build Terraform Project` again. Download the newly generated ZIP.

### Live pricing still says static price
Live profile discovery and exact pricing are separate. If exact IBM catalog pricing cannot be safely mapped, the app uses known fallback pricing and labels the confidence as `profile-live-price-static`.

## Glossary
### Address Prefix
An IBM Cloud VPC address range assigned to a zone before subnet creation.

### Block Volume
IBM Cloud VPC storage volume that can be attached to a VSI. In this app, non-boot data disks generate block volumes.

### Boot Disk
The disk expected to be included in the imported custom image or migration-tool workflow.

### Cloud Object Storage
IBM Cloud Object Storage. Custom images must be staged there before IBM Cloud VPC image import.

### Custom Image
An IBM Cloud VPC image imported from a supported image format such as `qcow2` or `vhd`.

### Data Disk
A non-boot source disk that is planned as an IBM Cloud block volume and VSI attachment.

### Handoff Package
The set of generated files that help migration teams connect Terraform output to image migration, replication, and cutover workflows.

### IBM Schematics
IBM Cloud managed Terraform service.

### Image Readiness
Assessment focused on custom image import prerequisites.

### Migration Readiness
Assessment focused on source-side operational cleanup before migration.

### Memory Readiness
Assessment focused on memory pressure, constraints, and conservative RAM sizing.

### Pricing Confidence
Metadata that explains whether a price is static fallback, cached, live-profile/static-price, or missing.

### Partition Mapping
Advisory storage planning detail from RVTools `vPartition`. It does not change generated IBM Cloud block volume size.

### NIC
Network interface card or virtual network adapter.

### RVTools
A VMware inventory export tool that produces multi-tab XLSX files.

### VSI
IBM Cloud Virtual Server for VPC.

### VMDK
VMware virtual disk file format.

## Related Documentation
- [README](../README.md)
- [Migration Handoff Package](migration-handoff-package.md)
- [Image Readiness Assessment](image-readiness-assessment.md)
- [Migration Readiness Assessment](migration-readiness-assessment.md)
- [Memory Readiness and Sizing](memory-readiness-sizing.md)
- [IBM Catalog Pricing](ibm-catalog-pricing.md)
- [Terraform Overrides Reference](terraform-overrides.md)
- [Right-Sizing Logic](../RIGHT_SIZING_LOGIC.md)
- [Development Log](../DEVELOPMENT_LOG.md)
