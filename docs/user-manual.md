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
- [Priority 2 Migration Planning Workflow](#priority-2-migration-planning-workflow)
- [Experimental Carbon UI Checkpoint](#experimental-carbon-ui-checkpoint)
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
- A Streamlit assessment workbench with focused Overview, Readiness, Remediation Backlog, VM Review, Wave Planning, Image Import Planning, Migration Ops, Networks, Storage, and Export tabs.
- A per-VM decision table with right-sizing recommendations, override controls, source metadata, disk mapping, network mapping, readiness assessments, and migration planning fields available through focused views.
- Migration wave planning with owner, cutover group, priority, application, and dependency tracking.
- Decision audit tracking for profile/storage/network/exclusion overrides and pricing impact analysis.
- Remediation backlog for managing blocking issues with owner, status, due date, and notes.
- Image import planning with per-image status tracking and bulk update capabilities.
- Migration Ops cutover readiness by wave and cutover group.
- A downloadable business case CSV with wave planning metadata.
- Decision audit, remediation backlog, and image import plan CSVs for export and further processing.
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
| `vPort` | Provides standard switch port and port group context for network readiness review. |
| `dvPort` | Provides distributed switch port and distributed port group context for network readiness review. |
| `vSwitch` | Provides standard switch backing, VLAN, MTU, and port capacity context. |
| `dvSwitch` | Provides distributed switch backing, VLAN/segment, MTU, and port capacity context. |

If an optional readiness tab is missing, the related readiness checks are skipped. Missing optional tabs do not block ZIP generation.
The Assessment Quality report still records missing optional tabs so reviewers can see when migration readiness confidence is based on partial workbook coverage.

## Installation and Launch
Run the application from the repository root.

### Python Path
Use this if Python is already installed.

1. Install dependencies:

For the normal local app with database-backed `Save Progress`, start OrbStack or Docker Desktop, then double-click `start-rvtools.command` from the repository root. The launcher builds and starts Streamlit, Postgres, the experimental FastAPI prototype, and Docker volumes for project metadata and artifacts. It waits for the app to become healthy and opens `http://localhost:8501` automatically.

For the same preconfigured launch from a terminal:

```bash
make run
```

Plain Python is a developer-only path and does not start Postgres automatically:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the Streamlit URL shown in the terminal, usually `http://localhost:8501`.

Click `Load Sample Workbook` in the sidebar for a first test run, or upload an RVTools XLSX export. Open `Help And Samples` in the sidebar for sample descriptions, expected workshop findings, recommended workflow, documentation paths, and the reminder that the app generates Terraform handoff files but does not run Terraform or perform cutover. For a larger practice workbook with expected readiness findings, upload `samples/SizingWorkshop-RVTools.xlsx` and review `docs/sample-findings-walkthrough.md`.

The sidebar and major planning controls include hover help for key selections such as target region, sizing threshold, pricing mode, wave fields, image import status, and Export package settings.

Press `Ctrl+C` in the terminal to stop the app.
If you started the preconfigured Docker stack, stop it with `make stop` or by double-clicking `stop-rvtools.command`. This keeps saved projects in the persistent database volume.

### Docker Path
Use this if Docker Desktop or a compatible Docker runtime is already running.

For the simplest database-backed local launch on macOS, start OrbStack or Docker Desktop, then double-click `start-rvtools.command` from the repository root. The launcher builds and starts Streamlit, Postgres, the experimental FastAPI prototype, and Docker volumes for project metadata and artifacts. It waits for the app to become healthy and opens `http://localhost:8501` automatically.

For the same persistent launch from a terminal:

```bash
make run
```

Or run the persistent Compose stack directly:

```bash
docker compose up --build --detach
```

Open `http://localhost:8501` and upload an RVTools XLSX export in the sidebar. Streamlit receives `DATABASE_URL` automatically in the Compose-backed launch, so the sidebar `Save Progress` panel can save planning state to the database.

For a stateless single-container run without database save:

```bash
docker build -t rvtools-to-ibm-cloud .
docker run --rm -p 8501:8501 rvtools-to-ibm-cloud
```

After the prebuilt GHCR image is published, use it with:

```bash
APP_IMAGE=ghcr.io/mjvincent/rvtools-to-ibm-cloud:latest docker compose up --detach
```

See [Deployment Guide](deployment.md) before storing customer RVTools data.

### Makefile Shortcuts
If `make` is available, these shortcuts run the same commands. The Makefile uses `venv/bin/python` when present, otherwise `python3`.

```bash
make run
make test
make start
make stop
make docker-build
make docker-run
make compose-up
make compose-pull
make compose-down
```

For browser access through a container or hosted service, see [Deployment Guide](deployment.md). Hosted deployments should require authenticated access because RVTools exports and generated migration packages can contain sensitive infrastructure data. The app also shows non-blocking reminders near upload and export controls. A static HTML page can link to the app, but it cannot replace the Streamlit/Python backend.

## End-to-End Workflow
1. Export the VMware inventory from RVTools as an XLSX workbook.
2. Launch the Streamlit app.
3. Select the target IBM Cloud region and zone.
4. Select the right-sizing threshold.
5. Enter the project name.
6. Upload the RVTools workbook.
7. Review the `Overview` tab for estate health, recommended next actions, and the Guided Migration Assistant checklist.
8. Review the `Readiness` tab and resolve `Blocked` items before migration execution.
9. Use `VM Review` to adjust exclusion, profile, storage tier, network, subnet, and security group decisions.
10. Use `Networks` and `Storage` to confirm placement and disk planning details.
11. Use `Export` to confirm package settings and subnet CIDRs.
12. Review the package summary, download the business case CSV, or save planning state if needed.
13. Review package preflight findings before building.
14. Click `Build Terraform Project`.
15. Resolve preflight blockers if the build is stopped, then rebuild.
16. Download the Terraform ZIP bundle.
17. Review the generated Terraform, preflight report, pricing diagnostics, and migration handoff files before applying or sharing with migration tooling.


## Assessment Workbench Tabs
### Overview
Shows the estate-level health summary, in-scope and excluded VM counts, monthly estimate, potential savings, blocker count, assessment quality summary, and recommended next actions. Start here after each upload.

The Guided Migration Assistant adds a first-run checklist and an assistive planning panel. `Initialize Pending/Open Defaults` initializes blank image import statuses to `Pending` and creates open remediation tracker entries for current readiness findings. Its hover help explains that it does not mark images as `Imported`, exclude VMs, change target profiles or subnets, build Terraform, or migrate workloads. The optional hard-blocked VM exclusion button queues `Exclude?` changes for review in `VM Review`.

### Readiness
Groups image, migration, memory, and network readiness by `Blocked`, `Review`, and `Ready`. Blocked and Review rows are sorted first so remediation planning starts with the highest-impact items.

### VM Review
Shows the main decision fields instead of every generated column. Use this tab to exclude VMs and adjust profile, storage tier, network, subnet, or security group intent. Advanced generated fields remain available in the expander for audit and troubleshooting.

### Wave Planning
Assigns active VMs to waves, cutover groups, owners, applications, priorities, and dependency groups. Use this tab to coordinate migration execution order, identify application or dependency grouping conflicts before export, and exchange wave-planning CSVs with project teams.

### Image Import Planning
Groups active VMs by inferred source image and tracks image import status, catalog IDs, estimated import timing, and notes. Bulk status actions update selected image groups while preserving existing catalog IDs, timing estimates, and notes.

### Migration Ops
Combines wave planning fields, readiness blockers, remediation status, and image import status into cutover readiness metrics. Use it to review each wave and cutover group before scheduling migration execution.

### Networks
Shows discovered networks, default CIDRs, VM network placement, multi-NIC count, unknown network signals, and source switch/port context when optional network detail tabs are present. Use this before export to confirm subnet, security group, and NIC placement intent.

### Storage
Shows total storage, data disk counts, boot/data planning signals, partition coverage, storage tier choices, and image readiness context. Use this to validate data disk volume planning before package generation.

### Export
Groups final package work into workflow sections for package settings, subnet CIDRs, package summary metrics, bundle contents preview, build readiness checklist, planning downloads, preflight review, Terraform validation guidance, Terraform preview, and Terraform ZIP build/download controls.

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
| `Cached IBM catalog` | Uses `data/ibm_vpc_pricing_cache.json` if present, including IBM Global Catalog billing-dimension metadata from the supported generator. Otherwise falls back to static pricing. |
| `Live IBM profile discovery` | Uses IBM Cloud VPC profile discovery when `IBMCLOUD_API_KEY` is available. Profile discovery remains separate from exact billing-dimension pricing. |

Pricing mode affects estimated cost and profile options, but does not change generated Terraform resource structure.

Populate the cached catalog with the supported standalone generator:

```bash
python scripts/generate_pricing_cache.py --region us-south
```

Use `--dry-run` to validate credentials and IBM Global Catalog mapping without writing the cache file.

For live mode, set `IBMCLOUD_API_KEY` in the shell that starts Streamlit or in a local `.env` file at the repository root. Restart Streamlit after creating or changing `.env`.

When using `start-rvtools.command`, `make run`, or Docker Compose, the local `.env` value is passed into the running app container automatically. The key is not committed, copied into the Docker image, or included in generated handoff files.

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

### Network Detail Tabs
Shows how many optional network-detail worksheets are present and populated out of `vPort`, `dvPort`, `vSwitch`, and `dvSwitch`.

Missing network-detail tabs do not block Terraform generation. When present, they improve network planning evidence and can create advisory `Review` or `Blocked` network readiness findings.

### Missing or Empty Tabs
Counts worksheets that are missing from the workbook or present with no rows. Open the worksheet coverage details expander to see the tab name, category, row count, confidence, and planning impact.

## Pricing Settings
The app records pricing metadata so users can understand whether estimates came from static fallback data, a cache file, or live IBM profile discovery.

### Pricing Source
Where the price/profile data came from.

### Pricing Confidence
How trustworthy the price/profile mapping is. Examples include:
- `fallback-static`
- `exact_catalog`
- `cached_catalog`
- `profile-live-price-static`
- `profile-live-price-missing`

### Pricing Status
Whether the current estimate is backed by exact catalog dimensions, a partial cached catalog, static fallback data, or unmapped catalog metrics.

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

### `Network Readiness`
Advisory network planning status: `Ready`, `Review`, or `Blocked`.

### `Network Readiness Reasons`
Explanation of source NIC, switch, port group, VLAN/segment, or port-capacity findings.

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
The application includes four separate readiness layers.

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

### Network Readiness
Network readiness focuses on source NIC metadata and optional switch/port evidence before migration waves are finalized.

| Status | Meaning |
| --- | --- |
| `Ready` | Connected NICs have usable source network metadata and matched switch/port evidence when optional detail tabs are present. |
| `Review` | Missing, ambiguous, disconnected, or incomplete switch/port context should be validated. |
| `Blocked` | Explicit unusable source port or no-port-capacity evidence should be remediated before migration. |

Network readiness is advisory. It does not change generated Terraform subnet, security group, primary NIC, or secondary NIC behavior.

## Build Terraform Project
On the `Export` tab, click `Build Terraform Project` after reviewing readiness, VM decisions, network placement, storage planning, and Terraform settings.

The `Build Readiness Checklist` is informational. It shows Ready, Review, and Blocked counts, then summarizes readiness blockers, required wave planning fields, image import status, planning-state/session safety, and package preflight signals. It does not block package generation.

Use `Preview Terraform` to save the latest Carbon network plan and inspect the generated package before downloading the ZIP. The preview includes Terraform files, migration handoff files, and Carbon state files with search, package-section filtering, handoff CSV filtering, and selected-file download.

Before the ZIP is created, the app runs package preflight validation. Blockers stop package generation; warnings are shown in the UI and exported in the package. Preflight checks cover blocked readiness, empty scope, unresolved custom image placeholders, CIDR syntax and overlap, duplicate Terraform names, missing subnet/security group mappings, unsupported storage tiers, and profile/region support warnings.

The `Terraform Validation Guidance` section explains checks to run after downloading and extracting the ZIP. Package preflight runs inside the app. Offline format validation uses `python scripts/validate_terraform_package.py` or `terraform fmt -check -recursive`. Strict init validation uses `python scripts/validate_terraform_package.py --init-validate` for CI, release checks, or connected operator review. The local `--allow-provider-download-failure` flag is only for VPN, proxy, DNS, or offline environments where provider downloads fail; do not use it for CI.

The app packages:
- Terraform root files.
- Networking module files.
- Storage module files.
- VSI module files.
- Migration handoff files.
- Preflight and pricing diagnostics reports.
- Image import variable template.
- Generated runbook.

After the build completes, click `Download Terraform Bundle`.

## Generated ZIP Contents
The ZIP bundle contains two categories of output:
- Terraform files for the IBM Cloud VPC target foundation.
- Handoff files for migration planning and downstream migration tools.

| File | Purpose |
| --- | --- |
| `README.md` | Terraform operator instructions, package review checklist, image ID workflow, and local CLI or IBM Schematics notes. |
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
| `provider.tf` | Carbon-generated ZIP only: provider configuration separated from root module logic. |
| `versions.tf` | Carbon-generated ZIP only: Terraform and provider version constraints. |
| `terraform.tfvars.example` | Carbon-generated ZIP only: example variable values for review before creating an operator-owned tfvars file. |
| `network-plan.json` | Carbon-generated ZIP only: saved Carbon network planning state used by the FastAPI Terraform renderer. |
| `migration-manifest.json` | Structured source-to-target migration handoff document. |
| `vm-mapping.csv` | Spreadsheet-friendly VM-level migration mapping. |
| `nic-mapping.csv` | Per-NIC source-to-target network mapping with optional switch/port context. |
| `disk-mapping.csv` | Per-disk boot/data mapping. |
| `partition-mapping.csv` | Per-partition storage planning detail from RVTools `vPartition`. |
| `memory-readiness.csv` | VM-level memory pressure, constraint, and sizing review. |
| `readiness-findings.csv` | Row-level migration readiness findings and remediation actions. |
| `assessment-quality.json` | Structured RVTools worksheet coverage and confidence report. |
| `assessment-quality.csv` | Spreadsheet-friendly worksheet coverage and confidence report. |
| `preflight-report.json` | Structured package preflight blockers and warnings. |
| `preflight-report.csv` | Spreadsheet-friendly package preflight blockers and warnings. |
| `pricing-diagnostics.json` | Structured pricing source, mapped dimensions, fallback, deployment, and unmapped metric details. |
| `pricing-diagnostics.csv` | VM-level pricing diagnostics for review and audit. |
| `cutover-readiness.csv` | Cutover readiness by VM, wave, cutover group, owner, application, blocker category, blocker reason, and recommended next action. |
| `planning-state.json` | Reloadable planning state for VM decisions, wave metadata, remediation tracking, and image import status. |
| `image-import-variables.tfvars.example` | Terraform varfile template for IBM Cloud custom image IDs after image import. |
| `migration-runbook.md` | Operational runbook for migration planning and execution. |

The Export tab shows a Bundle Contents Preview before build so users can identify the major Terraform, handoff, planning-state, image-import, and operator files before downloading the ZIP.

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

Each generated VSI uses `image = var.custom_image_ids["<VM Name>"]`. Populate the `custom_image_ids` map after IBM Cloud custom image import by copying `image-import-variables.tfvars.example`, replacing the placeholders, and passing the populated file to Terraform with `-var-file`.

The first connected NIC is rendered as the primary network interface. Additional connected NICs are rendered as secondary network interfaces. Disconnected NICs remain visible in handoff files but are not generated as active Terraform interfaces.

The VSI module also generates data volume attachments for storage module outputs.

## Migration Handoff Files
### `migration-manifest.json`
A structured JSON document containing project settings and per-VM source, target, migration, assessment, image readiness, migration readiness, memory readiness, network readiness, disk, and NIC data.

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
- Network readiness.
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
- Switch type, port group, VLAN/segment, port key, backing source tab, and match confidence when optional network-detail tabs are available.
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
- Missing optional network-detail tabs.
- Whether network or storage planning used fallback metadata from `vInfo`.
- Overall confidence before sharing migration wave plans.

### `preflight-report.json` and `preflight-report.csv`
Package validation reports showing build blockers and warnings.

Use them to review:
- Blocked readiness signals that stopped package generation.
- `Fix Category` routing for source RVTools/vSphere remediation, app planning updates, package exclusion, or Terraform operator review.
- Invalid, duplicate, or overlapping custom CIDRs.
- Duplicate Terraform resource names after sanitization.
- Missing subnet or security group mappings.
- Unsupported storage tiers or profile/region warnings.
- Unresolved custom image placeholders that must be populated after import.

### `pricing-diagnostics.json` and `pricing-diagnostics.csv`
Pricing diagnostics showing catalog metadata, mapped billing dimensions, selected Power VS deployment information when available, unmapped catalog metrics, and per-VM pricing source/status.

Use them to review:
- Which components are exact catalog, cached catalog, static fallback, or unmapped.
- Which billing dimensions were mapped into rates.
- Which catalog metrics were preserved as unmapped and why.
- Which effective profile and storage tier drove each VM estimate.

### `image-import-variables.tfvars.example`
A Terraform varfile template for custom image IDs after conversion and import.

The generated VSI module consumes the `custom_image_ids` map. Copy this file, replace every placeholder with the imported IBM Cloud VPC custom image ID for the matching VM, and pass the populated file to Terraform with `-var-file`.

### `migration-runbook.md`
A generated operational runbook customized with project, region, zone, VPC name, deployment target, and recommended workflow.

### `decision-audit.csv` (Priority 2)
A decision audit export tracking all profile/storage/network/exclusion override decisions and their pricing impact.

Use it to review:
- Which VMs had overrides applied.
- Profile override decisions and reasoning.
- Storage tier override decisions and reasoning.
- Network decisions and impact on target infrastructure.
- VM exclusion decisions.
- Per-VM baseline cost, estimated cost, savings, and total pricing impact of overrides.
- Ideal for reconciling decisions across large migrations and calculating aggregate cost impact.

### `remediation-backlog.csv` (Priority 2)
A remediation backlog for tracking blocking issues, owners, status, due dates, and notes.

Use it to review:
- Open, in-progress, and resolved blocking issues.
- Ownership assignment for remediation tasks.
- Due dates for tracking remediation progress.
- Overdue items requiring escalation.
- Notes with context for each blocker.
- Export for integration into project management tools (Jira, Azure DevOps, etc.).

### `image-import-plan.csv` (Priority 2)
An image import planning file with per-image sequencing, status tracking, and bulk update fields.

Use it to review:
- Which source images need conversion and import.
- VMs mapped to each source image.
- Target Catalog ID assignments for each image.
- Import status (pending, in-progress, complete, failed).
- Estimated time for each image import.
- Notes for integration with image import pipeline.
- Bulk status updates for tracking import progress across the migration.

### `cutover-readiness.csv`
A Migration Ops export combining wave planning, readiness blockers, remediation status, and image import status.

Use it to review:
- Which VMs are ready, require review, or remain blocked.
- Which wave or cutover group has missing planning fields.
- Which remediation items are still unresolved.
- Which source images have not reached `Imported` status.
- Recommended next actions before cutover scheduling.

### `planning-state.json`
A reloadable planning-state bundle containing VM decision fields, wave planning fields, remediation tracker data, image import status, and project metadata.

Use it from the Export tab to save a planning session and restore it later after uploading the same RVTools workbook. After import, the app summarizes restored VM decisions, wave rows, remediation items, image groups, and skipped rows so reviewers know what was applied.

After a workbook is loaded, the sidebar shows a persistent `Save Progress` panel. Use `Download Planning State` there at any time to save progress locally. The panel also shows the database save area. In the preconfigured launcher path, `Save To Database` is enabled and shows success or recovery messages. If the button is disabled or the panel says database save is not enabled, the current Streamlit process was started as a plain developer session without the database-backed stack. Stop that session and start the app with `start-rvtools.command` or `make run`.

When database save is available, the sidebar also shows `Saved Projects`. Use it to load, rename, or delete saved planning work without going to the Export tab. Load a saved project only after uploading the same source RVTools workbook, so saved VM decisions, wave rows, remediation items, and image-import status can be applied to the current workbook data.

When the app is running with a configured `DATABASE_URL`, the Export tab also shows `Database Project Save/Load` controls. These controls save the same planning-state data to Postgres so teams can reopen a saved project later. They do not replace the RVTools workbook itself; upload the same RVTools workbook before loading a saved database project so VM decisions and wave rows can be matched back to the current assessment data. If database save fails, immediately download `planning-state.json`, keep the source RVTools workbook, restart the app with `start-rvtools.command` or `make run`, then restore after uploading the same workbook.

Planning state does not include the uploaded RVTools workbook itself, generated ZIP bytes after the app closes, live Streamlit session state, Terraform execution state, or imported IBM Cloud images. Download generated ZIPs when they are built, keep the RVTools workbook with the project record, and download planning-state JSON before switching machines or handing work to another teammate.

## Priority 2 Migration Planning Workflow

The application includes four Priority 2 features for large-scale, multi-wave migrations:

### Wave Planning Tab
Organize VMs into migration waves with owner, cutover group, priority, application, and dependency tracking.

Use it to:
- Group related VMs into waves for phased migration.
- Assign owner and cutover group for each wave.
- Set priority (High, Medium, Low) for wave sequencing.
- Assign application names for cross-app dependency tracking.
- Define dependency groups to manage interdependencies.
- Bulk-update wave fields for groups of VMs.
- Export and import wave-planning CSVs for Excel or project-tracker workflows.
- Detect and warn about potential cutover group conflicts.
- Export wave metadata to migration-manifest.json for downstream systems.

### Decision Audit Tab
Track all profile/storage/network/exclusion override decisions and their pricing impact.

Use it to:
- Review which overrides were applied and why.
- Analyze per-VM pricing impact of overrides.
- Export decision-audit.csv for stakeholder review.
- Reconcile total cost impact across the migration.
- Identify override patterns for cost optimization.

### Remediation Backlog Tab
Manage blocking issues with owner, status, due date, and notes for cross-team remediation workflows.

Use it to:
- List all blocking readiness issues.
- Assign owners for remediation tasks.
- Track status (Open, In Progress, Resolved) for each blocker.
- Set due dates and monitor overdue items.
- Add notes with context for remediation teams.
- Export remediation-backlog.csv for project management tools.
- Import a saved remediation CSV to reload status, due date, note, and owner fields in a later session.
- Monitor overall remediation progress with summary metrics.

### Image Import Planning Tab
Sequence custom image imports with per-image status tracking and bulk update capabilities.

Use it to:
- View all source images and their VM mappings.
- Assign Target Catalog IDs for each image (optional, can be filled after import).
- Set import status (Pending, In Progress, Complete, Failed) for each image.
- Add estimated time for import completion.
- Bulk-update status for groups of images.
- Export image-import-plan.csv for integration with image import pipeline.
- Import a saved image-import-plan.csv to reload catalog IDs, import status, timing, and notes.
- Track overall import progress with summary metrics.

### Migration Ops Tab
Review cutover readiness across wave planning, remediation, and image import status.

Use it to:
- See ready, review, blocked, and open blocker counts.
- Compare readiness by wave and cutover group.
- Identify missing wave planning fields before scheduling cutover.
- Identify unresolved remediation and pending image import work.
- Export cutover-readiness.csv for migration command center tracking.

## Experimental Carbon UI Checkpoint
The IBM Carbon UI under `prototype/carbon-ui` is an experimental enterprise UI candidate. Streamlit remains the supported production UI until Carbon passes the promotion gates documented in [Carbon/React UI Strategy](carbon-react-ui-strategy.md), [Carbon Promotion Gate Review](carbon-promotion-gate-review.md), [Carbon Handoff Parity](carbon-handoff-parity.md), and [Carbon Operations Runbook](carbon-operations-runbook.md).

As of July 9, 2026, Carbon includes the core planning path, Phase 4 workflow surfaces, package parity checks, guided export readiness controls, and initial keyboard accessibility coverage needed for continued evaluation:

- **Workbook intake and overview**: Carbon uploads RVTools workbooks through the shared FastAPI summary path, then shows estate metrics, readiness counts, project persistence status, and saved-project controls.
- **Assignment workflow**: VM rows can be selected individually or in groups, then assigned by drag/drop or the explicit `Assign` button.
- **Assignment targets**: Subnet, security group, storage/IOPS, and migration wave buckets all support placement through the same confirmation flow. Assignment bucket regions and explicit `Assign` buttons expose target-specific accessible names for keyboard and assistive-technology review.
- **Confirmation modal**: Drag/drop assignment opens a placement modal that confirms the target bucket and selected VM count before applying changes.
- **Unassign actions**: Row-level actions can clear subnet, security group, storage override, and wave assignments without clearing unrelated fields on other rows.
- **Readiness routing**: Non-ready image, migration, memory, and network readiness chips include descriptive accessible labels. Clicking a reviewable chip routes the user to the matching Carbon workflow for investigation and remediation planning.
- **Override workflow**: Carbon includes a VM Overrides workflow for profile overrides, storage-tier overrides, exclusion reasons, override reasons, pricing-impact review, and decision-audit CSV export. Assignment rows route directly to override review for a selected VM.
- **Wave planning, remediation, image import, and migration ops**: Carbon includes workflow tabs for wave metadata, remediation backlog tracking, image import status, and cutover readiness. These workflows persist through saved project state and contribute to the generated handoff ZIP.
- **Export parity status**: Carbon Export shows package parity status before download. It identifies the Streamlit handoff file set, the Carbon modular Terraform layout, and the documented Carbon-only `network-plan.json` addition.
- **Export readiness guidance**: Carbon Export includes a readiness checklist, backend package preflight, blocker routing, Terraform package preview, and ZIP download gating. ZIP download runs preflight first and stops when blockers remain.
- **Suggested assignment fixes**: Carbon can suggest subnet, security group, storage/IOPS, and wave assignments from similarly named VMs, shared application/network/owner/cutover metadata, or matching bucket purpose. Suggestions show confidence and evidence, and users must explicitly apply them.
- **Suggestion audit and undo**: Applied suggestions are recorded in project state with old value, new value, confidence, reason, evidence, and timestamp. Active suggestion changes can be undone from the Export Readiness audit panel.
- **Readiness report**: Carbon can download a `carbon-export-readiness` JSON report containing checklist status, assignment gaps, latest preflight findings, suggestion audit entries, and package inventory counts for migration review meetings.
- **Terraform ZIP contents**: Carbon-generated ZIPs include the Streamlit handoff inventory, Carbon modular Terraform files, and `network-plan.json`. The UI inventory is backed by a shared JSON contract and tested against backend ZIP inventory constants to prevent drift.
- **Persistence expectations**: Saved projects, network plans, VM assignments, override values, and dirty-state autosave use the shared FastAPI/Postgres prototype stack. If the API or database is unavailable, Carbon shows a persistence warning and the work should be treated as temporary until saved successfully.
- **Accessibility and E2E coverage**: Drag/drop regions, assignment buttons, row checkboxes, and reviewable readiness chips expose descriptive accessible names. Playwright coverage runs in Chromium, Firefox, and WebKit and includes workbook upload, project save/load, keyboard navigation, keyboard assignment, review-chip routing, single and multi-select drag/drop, unassign persistence, autosave reload, and drag/drop accessibility labels.

Use Carbon for prototype evaluation and parity review, not production migration handoff. Use Streamlit for production work until Carbon parity and production-readiness gaps are closed, especially additional real-workbook parity fixtures, broader screen-reader/manual accessibility testing, customer-scale large-workbook performance validation beyond the workshop sample, hosted-runtime operations validation, and a formal go/no-go promotion decision.

## Recommended Migration Planning Workflow
1. Review `vm-mapping.csv` with infrastructure, application, security, and migration owners.
2. Confirm which VMs are in scope.
3. Exclude VMs that should not be migrated.
4. Resolve `Image Readiness = Blocked` items.
5. Resolve `Memory Readiness = Blocked` items.
6. Resolve `Migration Readiness = Blocked` items.
7. Resolve `Network Readiness = Blocked` items.
8. Assign owners for `Review` items.
9. Review `memory-readiness.csv` for profile sizing validation.
10. Review `nic-mapping.csv` for primary, secondary, and source switch/port interface placement.
11. Review `disk-mapping.csv` for data disk placement and sizing.
12. Review `partition-mapping.csv` for partition free-space context and unmatched partition rows.
13. **Use Wave Planning tab to organize VMs into migration waves**, assign owners and cutover groups, track dependencies, and set priorities.
14. **Use Decision Audit tab** to review profile/storage/network override decisions and their pricing impact.
15. **Use Remediation Backlog tab** to track blocking issues, assign owners, set due dates, and monitor remediation progress.
16. **Use Image Import Planning tab** to sequence custom image import stages, set target catalog IDs, and track import status.
17. **Use Migration Ops tab** to confirm cutover readiness by wave and cutover group.
18. Confirm IBM Cloud region, zone, VPC, subnet, and security group design.
19. Confirm profile and storage tier overrides.
20. Review generated Terraform.
21. Convert, replicate, or migrate images using the selected migration method and import status from Image Import Planning tab.
22. Upload converted images to IBM Cloud Object Storage when using custom image import.
23. Import images as IBM Cloud VPC custom images and record custom image IDs.
24. Apply Terraform using local CLI or IBM Schematics.
25. Validate boot, network, storage attachment, monitoring, backup, security, and application health.
26. Execute DNS, load balancer, IP, or application cutover steps following wave plan and cutover group assignments.

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

### Network readiness is mostly `Review`
Check optional `vPort`, `dvPort`, `vSwitch`, and `dvSwitch` exports. Missing or ambiguous switch/port evidence can trigger review findings even when Terraform network generation can continue.

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

### Cached pricing says cached catalog instead of exact catalog
Global Catalog dimensions are used only when they map to one positive, currently effective, linear metric. If some dimensions are missing or ambiguous, the app preserves the mapped catalog metrics, falls back for the rest, and labels the status as `cached_catalog`.

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

### Network Readiness
Assessment focused on source NIC, switch, port group, VLAN/segment, and port evidence for migration planning.

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
- [Network Readiness Assessment](network-readiness-assessment.md)
- [IBM Catalog Pricing](ibm-catalog-pricing.md)
- [Terraform Overrides Reference](terraform-overrides.md)
- [Carbon Operations Runbook](carbon-operations-runbook.md)
- [Right-Sizing Logic](../RIGHT_SIZING_LOGIC.md)
- [Development Log](../DEVELOPMENT_LOG.md)
