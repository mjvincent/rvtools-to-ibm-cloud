# Development Log: Multi-Tab Contention & Network Schema Discovery

## Overview
Evolution from a single-tab compute calculator to a multi-tab correlation model and automated Landing Zone generator.

## Technical Goals
- [x] **Compute Phase**: Parse `vCPU` for performance metrics (Ready %, Co-Stop).
- [x] **Resilience Phase**: Parse `vHost` and `vCluster` for physical headroom (pCores, Total MHz).
- [x] **Network Phase**: Implement Dynamic Schema Discovery from `vNetwork` and `vNIC`.
- [x] **Logic Implementation**:
    - **Starving VM Detection**: If Ready % > 5%, override right-sizing for performance safety.
    - **Zombie VM Detection**: If Usage < 5% and Usage MHz < 100, flag for decommissioning.
    - **N+1 Cluster Resilience**: (Total Cluster MHz - Largest Host MHz) - Total Demand.
    - **VPC IP Mirroring**: Automated generation of Address Prefixes and Subnets using `manual` preference.
- [x] **Modular Architecture**: Transition to modular HCL output (Networking, Storage, VSI).

## Data Schema Correlation
- **vInfo**: Anchor (VM inventory, Powerstate, Network assignments).
- **vNetwork**: Networking metadata (VLAN IDs, IPv4 Gateways, Port Groups).
- **vCPU**: Performance telemetry (Contention, MHz demand, Limits).
- **vHost**: Infrastructure capacity (Physical Cores, Host Speed).
- **vDisk**: Storage inventory (Capacity, Aggregate VM disk demand).

## Milestones
### May 5, 2026: Dynamic Networking & Modular HCL
- Resolved `KeyError` issues via dynamic column discovery for non-standard RVTools exports.
- Implemented automated CIDR extraction from `vNetwork` IPv4 column.
- Developed modular Terraform bundle generator (ZIP) for tiered storage and networking.
- Finalized PEP 8 compliance across `app.py` and `logic_engine.py`.

### May 6, 2026: Business Case Enhancements
- Added Streamlit dashboard savings metric and monthly savings aggregation.
- Exposed subnet/security group mapping values in the UI.
- Included mapping fields and baseline cost data in the business-case CSV export.
- Added user override support for IBM Profile and Storage Tier in the Streamlit data editor, with values honored during Terraform generation.
- Added Terraform override controls for VPC name, address prefix strategy, custom CIDRs, and deployment target selection.
- Added conditional backend behavior for Plain CLI vs IBM Schematics deployments.


### May 11, 2026: Migration Handoff Package
- Added a generated `migration-manifest.json` file to the Terraform ZIP bundle for tool-neutral source-to-target mapping.
- Added `vm-mapping.csv` for migration team review and customer workshop planning.
- Added `image-import-variables.tfvars.example` to capture IBM Cloud VPC custom image IDs after image import.
- Added `migration-runbook.md` to guide image staging, Terraform apply, validation, and cutover activities.
- Enriched per-VM processing with source IP, guest OS, disk count, host, cluster, datacenter, and power state metadata.
- Documented the handoff package in the README, dedicated user guide, and ADR-004.

### May 11, 2026: Image Readiness Assessment
- Added advisory `Ready`, `Review`, and `Blocked` image readiness statuses for IBM Cloud VPC custom image planning.
- Added firmware, boot disk size, guest customization, and readiness reason fields to the Streamlit table.
- Added dashboard metrics for image-ready, image-review, and image-blocked VM counts.
- Extended `migration-manifest.json`, `vm-mapping.csv`, and `migration-runbook.md` with image readiness data.
- Documented the assessment in the README, migration handoff guide, image readiness guide, and ADR-005.

### May 11, 2026: Per-Disk Volume Mapping
- Added RVTools `vDisk` detail preservation for boot/data disk planning.
- Changed generated storage from one aggregate volume per VM to one IBM Cloud block volume per non-boot data disk.
- Added VSI volume attachment generation using storage module outputs passed into the VSI module.
- Added `disk-mapping.csv` to the Terraform ZIP for source disk to target volume/attachment review.
- Extended the migration manifest with source disk metadata and target data volume planning fields.
- Documented the disk mapping behavior in the README, migration handoff guide, Terraform override notes, and ADR-006.

### May 11, 2026: Multi-NIC Network Mapping
- Added RVTools `vNetwork` detail preservation for per-VM NIC planning.
- Changed VSI Terraform generation to render the first connected NIC as primary and additional connected NICs as secondary network interfaces.
- Added `nic-mapping.csv` to the Terraform ZIP for primary, secondary, and disconnected NIC review.
- Extended the migration manifest with per-NIC source network, IP, MAC, adapter, switch, and connected-state metadata.
- Documented multi-NIC behavior in the README, migration handoff guide, Terraform override notes, and ADR-007.

### May 11, 2026: Migration Readiness Expansion
- Added advisory `Ready`, `Review`, and `Blocked` migration readiness statuses using RVTools `vSnapshot`, `vTools`, `vCD`, `vUSB`, and `vHealth` data when present.
- Added dashboard metrics and table fields for migration readiness, snapshot count/size, VMware Tools status, mounted media, USB device count, and health warning count.
- Added `readiness-findings.csv` to the Terraform ZIP for row-level remediation planning.
- Extended `migration-manifest.json`, `vm-mapping.csv`, and `migration-runbook.md` with migration readiness findings.
- Documented the assessment in the README, migration handoff guide, Terraform override notes, dedicated migration readiness guide, and ADR-008.

### May 11, 2026: Memory Readiness and Sizing
- Added RVTools `vMemory` parsing for active, consumed, ballooned, swapped, reservation, limit, and hot-add telemetry.
- Added advisory `Ready`, `Review`, and `Blocked` memory readiness statuses.
- Updated IBM Cloud profile sizing to use conservative memory guidance while preserving configured memory under pressure, reservations, or limits.
- Added dashboard metrics and disabled table fields for memory readiness and sizing basis.
- Added `memory-readiness.csv` to the Terraform ZIP and extended `migration-manifest.json`, `vm-mapping.csv`, and `migration-runbook.md`.
- Documented the feature in the README, user manual, right-sizing logic, migration handoff guide, Terraform override notes, memory readiness guide, and ADR-009.

### May 12, 2026: IBM Catalog Pricing Modes
- Added `catalog_pricing.py` to separate static, cached, and live IBM Cloud profile/pricing behavior.
- Added Pricing Mode controls to the Streamlit sidebar.
- Added pricing source, confidence, last-updated timestamp, and profile hourly fields to the table, manifest, and VM mapping CSV.
- Preserved offline/static fallback behavior so demos and local assessment work do not require IBM credentials.
- Added tests for static fallback, cached pricing, and live-mode fallback without an API key.
- Documented the design in the README, user manual, right-sizing logic, pricing guide, and ADR-010.

### May 12, 2026: Normalized VM Data Model
- Expanded `models.py` into the canonical internal VM dataclass model with nested source, target, pricing, image, memory, migration, disk, NIC, and readiness finding records.
- Updated the Streamlit processing path to build `MigrationVm` objects before converting to table rows at the UI boundary.
- Preserved current CSV, manifest, Terraform ZIP, and UI table contracts through `from_record()` and `to_record()` compatibility adapters.
- Moved old pricing API and Jinja template experiments into `experiments/` so production root files and smoke tests stay focused.
- Documented the model in `docs/normalized-vm-data-model.md` and ADR-011.

### May 13, 2026: Task 1 Module Split
- Split the Streamlit application and logic engine into focused parser, assessment, sizing, Terraform renderer, handoff, and UI helper modules.
- Kept `logic_engine.py` as a compatibility facade so existing tests and callers continue to use the same public imports.
- Preserved current Streamlit columns, CSV headers, manifest structure, Terraform ZIP layout, and generated file names.
- Added ADR-012 to document the module split and no-new-dependency decision.

### May 13, 2026: Assessment Workbench UI
- Reframed the Streamlit UI around focused Overview, Readiness, VM Review, Networks, Storage, and Export tabs.
- Reduced the default VM table to decision-oriented columns while keeping advanced generated fields available for audit.
- Moved readiness guidance next to the readiness triage view and moved package controls into the Export workflow.

### May 13, 2026: Assessment Quality Report
- Added RVTools worksheet coverage and confidence reporting for required and optional assessment tabs.

### June 2, 2026: Streamlit App Helper Split
- Extracted page header rendering, sidebar settings, and remediation backlog rendering into focused `streamlit_app/` modules while keeping `app.py` as the Streamlit entrypoint.
- Added focused tests for remediation backlog row generation and edit persistence.
- Updated CI actions to Node 24-compatible action versions and retained pytest log artifacts only for failed runs.

### June 2, 2026: Wave Planning Helper Split
- Extracted Wave Planning rendering and helper logic into `streamlit_app/wave_planning.py`.
- Added focused tests for active VM filtering, bulk wave assignment, editor persistence, conflict detection, and completion counts.
- Updated README and planning/user documentation to reflect the current Wave Planning tab and focused Streamlit helper layout.
- Added Overview tab quality metrics and worksheet coverage detail.
- Added `assessment-quality.json` and `assessment-quality.csv` to the Terraform ZIP and migration manifest.
- Documented the advisory quality model in the README, user manual, migration handoff guide, and ADR-013.

### May 13, 2026: vPartition Storage Planning
- Added advisory RVTools `vPartition` parsing and disk-key correlation.
- Preserved matched partition details on disk records and unmatched rows at VM level for review.
- Added Storage tab partition coverage signals and `partition-mapping.csv`.
- Extended disk mapping and manifest outputs with additive partition context without changing Terraform volume sizing.
- Documented the advisory partition model in the README, user manual, storage logic, handoff guide, and ADR-014.

### May 13, 2026: Network Readiness From Switch and Port Context
- Added optional RVTools `vPort`, `dvPort`, `vSwitch`, and `dvSwitch` parsing for advisory network readiness.
- Enriched per-NIC records with switch type, port group, VLAN/segment, port key, backing source tab, and match confidence.
- Added Network readiness to the Streamlit readiness triage, Network Planning view, VM mapping CSV, NIC mapping CSV, and migration manifest.
- Preserved Terraform primary/secondary/disconnected NIC behavior; switch and port context does not alter generated resources.
- Documented the advisory network readiness model in the README, user manual, handoff guide, normalized model guide, dedicated network readiness guide, and ADR-015.
