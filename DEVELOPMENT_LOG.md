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
