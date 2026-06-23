# RVTools to IBM Cloud VPC: Automated Infrastructure Mapping

## Overview
This utility automates the conversion of VMware RVTools exports into modular IBM Cloud VPC Terraform configurations. By correlating performance telemetry and networking metadata across multiple data tabs, the engine generates infrastructure-as-code (IaC) that reflects actual utilization requirements rather than static allocations.

## Quick Start
Choose one path from the repository root.

### Option 1: Preconfigured Local App
Use this for the normal local experience with database-backed `Save Progress`.

Start OrbStack or Docker Desktop, then double-click:

```text
start-rvtools.command
```

The launcher builds and starts Streamlit, Postgres, the prototype API, and persistent Docker volumes. It waits for the app to become healthy and opens `http://localhost:8501` automatically. Streamlit receives `DATABASE_URL`, so the sidebar `Save Progress` panel can save planning state to the database.

If you use `Live IBM profile discovery`, put `IBMCLOUD_API_KEY=...` in a local `.env` file at the repository root before starting the launcher. Compose passes that value into the app container without baking it into the image.

For the same preconfigured launch from a terminal:

```bash
make run
```

Open:

```text
http://localhost:8501
```

To stop the app and database:

```bash
make stop
```

On macOS, you can also double-click `stop-rvtools.command`. Stop keeps the persistent database and artifact volumes. Use `docker compose down --volumes` only when you intentionally want to erase saved projects.

### Option 2: Docker Compose
Use this if you prefer the direct Docker command.

```bash
docker compose up --build --detach
```

Open:

```text
http://localhost:8501
```

This is the same database-backed stack used by the launcher.

For a stateless single-container run without database save:

```bash
docker build -t rvtools-to-ibm-cloud .
docker run --rm -p 8501:8501 rvtools-to-ibm-cloud
```

After the GHCR image is published, use the prebuilt persistent stack with:

```bash
APP_IMAGE=ghcr.io/mjvincent/rvtools-to-ibm-cloud:latest docker compose up --detach
```

Postgres is also exposed on `localhost:5432` for developer-only local Python/Streamlit runs.

```bash
DATABASE_URL=postgresql://rvtools:rvtools@localhost:5432/rvtools \
ARTIFACT_STORAGE_PATH=.local-artifacts \
venv/bin/python -m streamlit run app.py
```

### Option 3: Python Development
Use this only for development when you intentionally do not want the preconfigured Docker/Postgres stack.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Plain Python does not start Postgres by itself. Use `start-rvtools.command` or `make run` for the normal database-backed app.

Other useful commands:

```bash
make test
make sample-workbook
make run
make start
make stop
make docker-build
make docker-run
make compose-up
make compose-pull
make compose-down
```

### What You Need
- A standard RVTools `.xlsx` export.
- Python with `pip`, or Docker.
- Optional Terraform for deeper package validation.
- Optional IBM Cloud API key only when using live catalog discovery.

### First Successful Run
After opening the app, click `Load Sample Workbook` in the sidebar or upload `samples/rvtools-small-complete.xlsx` for a first test run. The sidebar `Help And Samples` panel explains the bundled samples, recommended workflow, documentation paths, and tool boundaries. The workbench should show Overview, Readiness, Remediation Backlog, VM Review, Wave Planning, Image Import Planning, Migration Ops, Networks, Storage, and Export tabs. The Overview tab includes a Guided Migration Assistant with a first-run checklist, safe planning defaults, and a migration action-plan export.

For a larger realistic exercise, upload `samples/SizingWorkshop-RVTools.xlsx`. That workbook intentionally includes source-data issues and planning gaps, so readiness and preflight findings are expected. See `docs/sample-findings-walkthrough.md` for the expected practice findings.

The app is not static HTML. It needs Streamlit/Python running locally or in a hosted container. For a persistent local/team deployment, use `start-rvtools.command`, `make run`, or `docker compose up` to run the app with Postgres and an artifact volume. In Streamlit, the sidebar `Save Progress` panel can download planning-state JSON at any time after upload, save progress to Postgres, and reopen saved projects from the `Saved Projects` panel. Database save stores planning state and project metadata; it does not store the source RVTools workbook or replace downloaded Terraform ZIPs. Keep the source RVTools workbook and upload it again before restoring a saved project.

## Common First-Run Fixes
| Symptom | Fix |
| --- | --- |
| `streamlit: command not found` | Run `python -m pip install -r requirements.txt`, then try `python -m streamlit run app.py`. |
| Port `8501` is busy | Run `streamlit run app.py --server.port 8502` or map Docker to another host port with `docker run --rm -p 8502:8501 rvtools-to-ibm-cloud`. |
| Docker command fails | Confirm Docker Desktop or the Docker daemon is running. |
| App rejects the upload | Confirm the file is an RVTools `.xlsx` workbook, not CSV or a manually edited spreadsheet. |
| Terraform validation fails during init | Confirm VPN/proxy/DNS access to `registry.terraform.io` and provider downloads. For local offline checks, run `python scripts/validate_terraform_package.py` or rerun init validation with `--allow-provider-download-failure` to tolerate provider download failures only. |

## Core Functional Logic

### Network Schema Discovery
The tool identifies on-premises network configurations by correlating data from the vNetwork and vInfo tabs.
* **IP Range Mapping**: Extracts IPv4 gateways and addresses to define VPC Address Prefixes.
* **Subnet Generation**: Automatically configures subnets using a manual address preference, ensuring original CIDR blocks are preserved in the target VPC environment.
* **Resource Linking**: Maps individual Virtual Server Instances (VSIs) to their respective subnets based on on-premises port group assignments.
* **Multi-NIC Mapping**: Uses `vNetwork` rows to preserve primary and secondary NIC placement. Connected secondary NICs generate additional VSI network interfaces.
* **Switch/Port Context**: Optional `vPort`, `dvPort`, `vSwitch`, and `dvSwitch` rows add advisory source switch, port group, VLAN/segment, and port evidence without changing generated Terraform interfaces.

### Performance-Aware Right-Sizing
The mapping engine evaluates compute requirements by analyzing specific performance metrics to mitigate the risk of post-migration performance degradation.
* **Contention Analysis**: Monitors CPU Ready % and Co-Stop telemetry. If a workload shows signs of resource contention on-premises, the tool implements a "Safety Match" policy, maintaining the original core count and memory allocation.
* **Utilization Thresholds**: Allows for the application of variable utilization factors (30% to 70%) to align suggested IBM VPC profiles with specific performance targets.
* **Memory-Aware Sizing**: Uses `vMemory` active, consumed, ballooned, swapped, reservation, limit, and hot-add data to avoid unsafe reductions and provide conservative RAM recommendations.

### Resource Efficiency Auditing
The application performs an automated audit of the inventory to identify underutilized assets.
* **Identification of Low-Utilization Assets**: Workloads exhibiting <5% CPU utilization and <100 MHz overall demand are flagged for review.
* **Capacity Headroom (N+1)**: Calculates available cluster capacity by identifying the largest host speed and evaluating remaining aggregate capacity against total VM demand.

### Per-Disk Volume Mapping
The tool now preserves RVTools `vDisk` detail instead of collapsing all disks into one target volume.
* **Boot Disk Separation**: The first discovered disk is treated as image-covered boot storage.
* **Data Disk Volumes**: Additional disks generate IBM Cloud block volumes and VSI volume attachments.
* **Disk Handoff**: A `disk-mapping.csv` file shows source disk metadata and target Terraform volume/attachment names.
* **Partition Context**: Optional `vPartition` rows add partition labels, capacity, consumed, and free-space context for review without changing generated volume sizes.

### Image Readiness Assessment
The dashboard evaluates source VM metadata for IBM Cloud VPC custom image planning.
* **Readiness Status**: Flags each workload as `Ready`, `Review`, or `Blocked`.
* **Image Constraints**: Checks boot disk size against IBM Cloud custom image limits and records the required `qcow2` or `vhd` conversion target.
* **Guest Preparation**: Identifies the expected guest customization path, such as `cloud-init` for Linux or `cloudbase-init` for Windows.

### Migration Readiness Assessment
The dashboard also evaluates operational migration prerequisites from optional RVTools tabs.
* **Snapshot Review**: Uses `vSnapshot` to flag active snapshots and block large snapshot footprints before export or replication.
* **Guest Health Signals**: Uses `vTools` to flag VMware Tools, heartbeat, application status, upgrade, and operation readiness concerns.
* **Attached Device Cleanup**: Uses `vCD` and `vUSB` to block connected ISO/CD media or USB device dependencies before migration.
* **Health Findings**: Uses `vHealth` where VM-level findings can be matched to the workload inventory.

### Network Readiness Assessment
The dashboard evaluates source NIC metadata and optional switch/port backing.
* **NIC Evidence**: Uses `vNetwork` as the primary NIC inventory and enriches it with `vPort`, `dvPort`, `vSwitch`, and `dvSwitch` when present.
* **Advisory Status**: Flags `Ready`, `Review`, or `Blocked` network signals for migration planning while preserving Terraform output behavior.
* **Handoff Detail**: Adds switch type, port group, VLAN/segment, port key, source tab, and match confidence to NIC planning outputs.

### Assessment Quality Report
The dashboard reports RVTools worksheet coverage and advisory confidence before teams rely on sizing, readiness, network, or storage outputs.
* **Tab Coverage**: Shows required and optional RVTools tabs as `Present`, `Missing`, or `Empty`.
* **Planning Confidence**: Summarizes inventory, storage, network, memory, migration readiness, and overall confidence.
* **Handoff Output**: Adds `assessment-quality.json` and `assessment-quality.csv` to the Terraform ZIP for customer review and downstream planning.

### Memory Readiness Assessment
The dashboard evaluates memory pressure and sizing constraints from RVTools `vMemory`.
* **Pressure Detection**: Flags swapping and ballooning before profile reductions are applied.
* **Constraint Detection**: Captures reservations, memory limits, and hot-add dependencies for owner review.
* **Sizing Guidance**: Uses active memory with a conservative floor when memory can be reduced safely.

### IBM Catalog Pricing
Pricing can run in static, cached, or live profile discovery mode.
* **Static Fallback**: Uses bundled profile and storage rates so the app works offline.
* **Cached Catalog**: Uses `data/ibm_vpc_pricing_cache.json` when available, including IBM Global Catalog billing-dimension metadata generated by the supported cache script.
* **Live Profile Discovery**: Uses IBM Cloud VPC profile discovery when `IBMCLOUD_API_KEY` is available, while preserving explicit pricing confidence metadata.

Use `scripts/generate_pricing_cache.py` to generate the cached catalog from IBM Global Catalog Power VS pricing data. The supported generator maps only uniquely resolved, positive, currently effective, linear billing dimensions as exact; ambiguous or unmapped dimensions remain visible and fall back to bundled estimates.

## Technical Structure
The application is split into focused modules with `MigrationVm` as the internal contract:
1. **Streamlit Entrypoint (`app.py`)**: Keeps the workbench route, upload flow, tab composition, and renderer delegation in one runnable Streamlit entrypoint.
2. **Streamlit Helpers (`streamlit_app/`)**: Owns focused UI helpers such as page header rendering, sidebar settings, overview/readiness rendering, guided migration assistance, VM review decisions, final VM assembly, wave planning, image import planning rendering/status handling, network/storage planning, remediation backlog rendering, Export tab package controls, and Terraform bundle assembly.
3. **RVTools Parsing (`rvtools_parser.py`, `rvtools/`)**: Keeps root import compatibility while focused package modules load worksheets, correlate RVTools tabs, and build normalized VM records.
4. **Assessments and Sizing (`assessments.py`, `sizing.py`)**: Evaluates readiness, profile matching, storage tiering, baseline cost, and savings.
5. **Terraform Rendering (`terraform_renderer.py`)**: Outputs HCL in a modular format including networking, storage, and VSI modules.
6. **Preflight Validation (`preflight.py`)**: Blocks unsafe package builds and reports warnings for unresolved planning decisions.
7. **Migration Handoff (`handoff/`)**: Exports source-to-target mapping files, preflight reports, and pricing diagnostics that connect generated Terraform to image import, replication, and cutover workflows.

`logic_engine.py` remains as a compatibility facade for existing tests and callers while the implementation lives in the focused modules above.

## Development Testing
Install dependencies, then run the pytest suite from the repository root:

```bash
python -m pytest
```

Targeted checks can run by file, for example:

```bash
python -m pytest tests/test_catalog_pricing.py
python -m pytest tests/test_disk_mapping.py
```

The pytest configuration collects tests only from `tests/`; old API research under `experiments/` is not part of the supported suite. Snapshot expectations live under `tests/snapshots/` and should be reviewed when generated Terraform, CSV, or manifest outputs intentionally change. See `docs/testing.md` for the fixture and snapshot workflow.

For release-style validation, also run the Streamlit browser checklist in `docs/testing.md`: upload a representative RVTools workbook, review each workbench tab, build the Terraform bundle, inspect the ZIP contents, and run `python scripts/validate_terraform_package.py` or `terraform fmt -check -recursive` against an extracted bundle.

## Data Requirements
Successful execution requires a standard RVTools XLSX export containing the following worksheets:
* **vInfo**: Primary inventory, power states, and network assignments.
* **vNetwork**: Networking metadata and IPv4 addressing.
* **vPort / dvPort / vSwitch / dvSwitch**: Optional source switch and port context for network readiness review.
* **vCPU**: Detailed performance telemetry (MHz, Ready %, Limits).
* **vMemory**: Memory telemetry for active, consumed, swapped, ballooned, reservation, limit, and hot-add data.
* **vHost / vCluster**: Physical infrastructure specifications and aggregate capacity.
* **vDisk**: Storage capacity and disk inventory.
* **vPartition**: Optional partition-level capacity, consumed, and free-space details for storage planning review.
* **vSnapshot / vTools / vCD / vUSB / vHealth**: Optional migration readiness signals for snapshots, guest tools, attached media, USB devices, and health warnings.

## Business Case and Mapping Output
The dashboard is organized as an assessment workbench with Overview, Readiness, Remediation Backlog, VM Review, Wave Planning, Image Import Planning, Migration Ops, Networks, Storage, and Export tabs. It exports an enriched business case CSV with per-VM data including:
* RVTools worksheet coverage and assessment confidence summary
* Baseline cost estimate
* Estimated monthly savings
* Subnet mapping for Terraform
* Security group mapping for Terraform (if enabled)
* User override fields for Profile and Storage Tier to influence generated Terraform
* Source metadata including IP address, guest OS, host, cluster, datacenter, and disk count for migration handoff planning
* Image readiness status, readiness reasons, firmware, boot disk size, and guest customization requirement
* Migration readiness status, readiness reasons, snapshot count/size, VMware Tools status, mounted media, USB device count, and health warning count
* Network readiness status, readiness reasons, and source switch/port backing context
* Memory readiness status, pressure indicators, reservation/limit data, and sizing memory basis
* Pricing source, confidence, last-updated timestamp, and profile hourly value
* Per-disk boot/data role, capacity, source controller metadata, and target volume attachment mapping
* Per-partition source capacity, consumed, free-space, and disk correlation context
* Per-NIC source network, IP, MAC, adapter, connected state, switch/port context, target subnet, and security group mapping
* **Migration planning fields** (wave, cutover group, owner, application, priority, dependency group) for organizing large-scale migrations
* **Decision audit trail** tracking profile/storage/network/exclusion overrides and their pricing impact
* **Remediation tracker** with owner, status, due date, notes, and CSV export/import for blocking issues
* **Image import planning** with per-image status, estimated time, bulk update capabilities, and CSV reload support
* **Migration Ops readiness** combining wave planning, blockers, remediation status, and image import status for cutover review

## Streamlit Override Controls
The Streamlit dashboard exposes editable override fields for `Override Profile` and `Override Storage Tier`. When set, these user-specified values are honored by the Terraform generator, allowing human-directed tuning of VSI sizing without changing the underlying migration logic.

### Example
If the auto-generated profile is `bx2-2x8` but you want the instance to use `cx2-2x4`, set `Override Profile` to `cx2-2x4` for that row before clicking **Build Terraform Project**. The generated VSI resource will then use the override profile.

If you want a lower-cost disk tier than the default recommendation, change `Override Storage Tier` from `5iops-tier` to `3iops-tier` for that row; the generated volume resource will then use the override tier.

### Override Columns
The Streamlit data table uses the following override columns:
* `Override Profile` — choose an alternate IBM Cloud VSI profile
* `Override Storage Tier` — choose an alternate storage IOPS tier
* `Subnet` — displays the generated subnet mapping for the selected network
* `Security Group` — displays the generated security group mapping when enabled

### Terraform Overrides & Deployment Targets
The `Terraform Overrides` expander exposes additional infrastructure configuration controls:
* **VPC Name** — name the target IBM Cloud VPC resource
* **Address Prefix Strategy** — choose `manual` to preserve generated CIDR prefixes, or `auto` to use provider-managed allocation
* **Custom CIDR per Subnet** — override the generated subnet CIDR for each discovered network
* **Deployment Target** — choose `Plain CLI` for local Terraform execution, or `IBM Schematics` for Schematics-managed deployment
* **SSH Source CIDR** — optionally add inbound SSH rules from a specific management CIDR; leave blank to omit SSH access from generated security groups

When `Plain CLI` is selected, the generated root `main.tf` uses a local Terraform backend configuration. For `IBM Schematics`, the bundle omits the backend block so Schematics can manage state.

![Streamlit override controls example](docs/images/streamlit_override_example.png)

> Best practice: only set override values when you have validated that the target IBM Cloud profile and tier are supported for the workload and its storage requirements.

## Terraform Output Structure
The exported ZIP bundle now produces a modular Terraform layout:
* `main.tf`, `variables.tf`, `outputs.tf` at the root
* `modules/networking/main.tf`, `variables.tf`, `outputs.tf`
* `modules/storage/main.tf`, `variables.tf`, `outputs.tf`
* `modules/vsi/main.tf`, `variables.tf`, `outputs.tf`

## Migration Handoff Package
Each ZIP bundle also includes a migration handoff package that bridges generated Terraform with image migration and cutover activities:
The Export tab includes a Bundle Contents Preview so users can see the major files and owners before building the ZIP.
* `README.md` — Terraform operator instructions for local CLI or IBM Schematics execution
* `migration-manifest.json` — tool-neutral source-to-target mapping for each VM including wave planning metadata and decision audit summary
* `vm-mapping.csv` — spreadsheet-friendly view for migration planning and customer review
* `nic-mapping.csv` — per-NIC primary/secondary network interface mapping
* `disk-mapping.csv` — per-disk boot/data mapping for volume creation and attachment review
* `partition-mapping.csv` — per-partition storage planning detail from RVTools `vPartition`
* `memory-readiness.csv` — VM-level memory pressure, constraint, and sizing review
* `readiness-findings.csv` — row-level migration readiness findings and remediation actions
* `assessment-quality.json` / `assessment-quality.csv` — RVTools worksheet coverage and confidence report
* `preflight-report.json` / `preflight-report.csv` — package safety blockers and warnings with fix categories for source data, app planning, exclusion, or operator review
* `pricing-diagnostics.json` / `pricing-diagnostics.csv` — pricing source, mapped dimensions, fallback components, and unmapped catalog metrics
* `decision-audit.csv` — profile/storage/network/exclusion overrides with pricing impact analysis
* `remediation-backlog.csv` — tracking blockers with owner, status, due date, and notes for cross-team remediation workflows
* `image-import-plan.csv` — image import planning with source image, target catalog ID, import status, and estimated time per VM
* `cutover-readiness.csv` — wave and cutover-group readiness view across planning, remediation, and image import status
* `planning-state.json` — reloadable planning state for VM decisions, wave metadata, remediation tracking, and image import status; Export includes session-safety guidance for what it does and does not restore
* `image-import-variables.tfvars.example` — Terraform varfile template for IBM Cloud VPC custom image IDs after image import
* `migration-runbook.md` — operational runbook for image staging, Terraform apply, validation, and cutover

The handoff files include image readiness, migration readiness, memory readiness, network readiness, NIC mapping, disk mapping, and migration planning fields so migration teams can resolve boot image, snapshot, mounted media, guest tools, memory pressure, reservations, limits, switch/port backing, network, data disk, firmware, OS, guest customization concerns, and wave/cutover coordination before import. They are intentionally tool-neutral and can be reviewed by migration teams, adapted for RackWare or other migration tooling, or used as input for a migration factory workflow.

Generated resources include standardized naming and tags for project and management metadata, and the networking module exports reusable `subnet_id` and `security_group_id` outputs for the VSI module. Imported image IDs are supplied through the `custom_image_ids` Terraform map, using the VM keys emitted in `image-import-variables.tfvars.example`.

![Terraform module layout example](docs/images/terraform_output_layout.png)

## Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Launch the utility: `streamlit run app.py`
3. Upload the RVTools .xlsx file.
4. Review the Overview and Readiness tabs, using Guided Migration Assistant for a first-run checklist and safe planning defaults.
5. Use VM Review, Networks, and Storage to confirm overrides and placement.
6. Use Wave Planning to organize VMs into migration waves, specify owners and cutover groups, track dependencies, prioritize workloads, and exchange wave-planning CSVs with project teams.
7. Use Decision Audit and Remediation Backlog for override tracking and issue resolution workflows; use planning-state JSON for full app resume and CSV exports for external team workflows.
8. Use Image Import Planning to sequence custom image import stages, track status, and include image status in planning-state JSON.
9. Use Migration Ops to confirm cutover readiness by wave and cutover group.
10. Use Export to review package settings, subnet CIDRs, package summary metrics, bundle contents preview, build readiness checklist, planning downloads, preflight findings, Terraform validation guidance, and Terraform Bundle ZIP build/download controls for IBM Cloud CLI or IBM Cloud Schematics.
11. Review the included migration handoff files (including wave metadata and remediation tracking) before image import, replication, or cutover planning.

## User Manual
For a complete searchable guide to installation, RVTools inputs, web interface fields, dashboard metrics, readiness statuses, generated Terraform, ZIP contents, handoff files, troubleshooting, and glossary terms, see `docs/user-manual.md`.

## Deployment
The application can be used through a browser when Streamlit is running locally or as a hosted container. It is not a static HTML app because workbook parsing, readiness logic, Terraform rendering, and ZIP generation run in Python. For local Docker, IBM Cloud Code Engine, private hosting, and RVTools data-handling guidance, see `docs/deployment.md`.

## Further Reading
Start with `docs/user-manual.md` for end-user operation. For sample workbook practice findings, see `docs/sample-findings-walkthrough.md`. For container and hosted deployment guidance, see `docs/deployment.md`. For the experimental enterprise UI direction, see `docs/carbon-react-ui-strategy.md`. For migration wave planning, decision audit tracking, remediation backlog, and image import planning, see `docs/PRIORITY2_MIGRATION_PLANNING.md`. For detailed Terraform override behavior and deployment target guidance, see `docs/terraform-overrides.md`. For migration handoff package details, see `docs/migration-handoff-package.md`. For demo recording guidance, see `docs/demo-video-guide.md`. For image readiness guidance, see `docs/image-readiness-assessment.md`. For broader migration readiness guidance, see `docs/migration-readiness-assessment.md`. For memory readiness and sizing guidance, see `docs/memory-readiness-sizing.md`. For network readiness guidance, see `docs/network-readiness-assessment.md`. For catalog pricing behavior, see `docs/ibm-catalog-pricing.md`. For internal model architecture, see `docs/normalized-vm-data-model.md`.

## Release Notes
- **Deployment Docs Hardening** — Clarified local, hosted, private Code Engine, static HTML, and RVTools data-security deployment guidance.
- **Deployment Readiness** — Added Docker and Streamlit configuration plus deployment guidance for local containers, IBM Cloud Code Engine, and sensitive RVTools data handling.
- **Migration Ops Readiness** — Added a Migration Ops tab and `cutover-readiness.csv` handoff export that combines wave planning, readiness blockers, remediation status, and image import status for cutover review.
- **Priority 2: Migration Planning Workflow** — Added Wave Planning tab for organizing migrations into waves with owner, cutover group, priority, application, and dependency tracking. Added Decision Audit export for tracking profile/storage/network overrides and pricing impact. Added Remediation Backlog tab for managing blocking issues with owner, status, due date, and notes. Added Image Import Planning tab for sequencing custom image imports with status tracking. All Priority 2 features integrated into migration manifest and ZIP handoff exports.
- Added a potential savings metric to the Streamlit dashboard.
- Added per-VM baseline and savings values in the exported business case CSV.
- Added subnet and security group mapping fields to the business case export to support Terraform wiring.
- Added Terraform override controls for VPC naming, prefix strategy, custom CIDRs, and deployment target selection.
- Added migration handoff files for source-to-target mapping, image import placeholders, and cutover runbook support.
- Added image readiness assessment fields for IBM Cloud VPC custom image planning.
- Added per-disk data volume generation, VSI volume attachments, and `disk-mapping.csv`.
- Added advisory `vPartition` storage planning context, including `partition-mapping.csv`.
- Added multi-NIC network mapping, secondary VSI network interfaces, and `nic-mapping.csv`.
- Added migration readiness assessment from RVTools snapshot, tools, CD, USB, and health tabs, including `readiness-findings.csv`.
- Added assessment quality reporting for RVTools worksheet coverage and confidence, including `assessment-quality.json` and `assessment-quality.csv`.
- Added a comprehensive searchable user manual in `docs/user-manual.md`.
- Added memory readiness and conservative RAM sizing using RVTools `vMemory`, including `memory-readiness.csv`.
- Added advisory network readiness using optional RVTools switch and port tabs.
- Added IBM catalog pricing modes with static, cached, and live profile discovery paths plus pricing confidence metadata.
- Added package preflight validation, Terraform package validation harness, pricing diagnostics exports, and profile/region support warnings.
- Added a normalized VM dataclass model and moved old pricing/template experiments under `experiments/`.
- Split the monolithic Streamlit and logic engine code into parser, assessment, sizing, renderer, handoff, and focused Streamlit helper modules while preserving output contracts.
- Reframed the Streamlit interface as a tabbed assessment workbench with focused Overview, Readiness, Remediation Backlog, VM Review, Wave Planning, Image Import Planning, Migration Ops, Networks, Storage, and Export views.

---
**Author**: Michael Vincent Jones
**Version**: 2.0.0
