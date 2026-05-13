# Migration Handoff Package

## Purpose
The migration handoff package extends the Terraform ZIP bundle with planning files that connect the generated IBM Cloud VPC infrastructure to the image migration and cutover workflow.

Terraform remains responsible for the target VPC foundation, modules, and infrastructure definitions. The handoff files help customers, migration teams, or partner tooling understand which VMware workload maps to which target IBM Cloud resource.

## Generated Files
### `migration-manifest.json`
A tool-neutral JSON document containing project-level target settings and per-VM source, target, migration, and assessment fields.

Use this file when integrating with scripts, RackWare-style workflows, migration factory tooling, or future adapters.

Each VM now includes an `image_readiness` object with readiness status, reason text, firmware, boot disk size, expected guest customization, required image format, and Cloud Object Storage staging expectation.

Each VM also includes a `migration_readiness` object with readiness status, reason text, snapshot count and size, VMware Tools status, mounted media, USB device count, health warning count, and detailed findings when available.

Each VM assessment also includes a `memory_readiness` object with readiness status, reason text, configured, active, consumed, ballooned, swapped, reservation, limit, hot-add, sizing memory, and sizing basis fields.

Each VM also includes a `network_readiness` object with advisory readiness status, reason text, and findings based on source NIC metadata and optional switch/port evidence.

The manifest also includes an additive `assessment_quality` object with RVTools worksheet coverage, required and optional tab counts, and confidence values for inventory, storage, network, memory, migration readiness, and overall planning.

The manifest also preserves source disk detail from `vDisk`. Boot disks are marked as image-covered storage, and additional disks are listed as target data volumes for IBM Cloud block storage creation and attachment. Optional `vPartition` rows are included as advisory partition context when available.

The manifest preserves source NIC detail from `vNetwork`. Connected NICs are mapped to primary or secondary VPC network interfaces, while disconnected NICs remain visible for migration review. Optional `vPort`, `dvPort`, `vSwitch`, and `dvSwitch` data adds switch type, port group, VLAN/segment, port key, source tab, and match confidence evidence when available.

### `vm-mapping.csv`
A spreadsheet-friendly view of the same source-to-target mapping. This is intended for customer workshops, wave planning, and migration team review.

The CSV includes image, migration, memory, and network readiness columns so application and migration teams can filter `Blocked` items before image import planning, replication, export, or cutover scheduling and assign owners for `Review` items.

### `nic-mapping.csv`
A per-NIC mapping file showing primary, secondary, and disconnected source adapters. It includes source network, IP, MAC address, adapter type, switch, optional switch/port backing context, target subnet, and target security group.

### `disk-mapping.csv`
A per-disk mapping file that separates boot disks from data disks. Boot disks are marked as covered by the imported custom image. Data disks include target Terraform volume and attachment resource names. Partition summary columns are included when `vPartition` data is available.

### `partition-mapping.csv`
A row-level partition planning file showing partition label/path, capacity, consumed space, free space, free percentage, source disk key, and whether the row matched a `vDisk` record.

### `memory-readiness.csv`
A VM-level memory readiness file showing memory pressure, reservations, limits, hot-add status, sizing memory, sizing basis, and effective profile context.

### `readiness-findings.csv`
A row-level migration readiness file showing each detected finding, severity, source RVTools tab, evidence, and recommended action. This is the most direct remediation worklist for migration planning workshops.

### `assessment-quality.json`
A structured workbook-level quality report showing RVTools worksheet coverage, row counts, confidence, and planning impact. Use it to understand whether sizing, readiness, storage, and network planning signals are based on complete workbook data or fallback metadata.

### `assessment-quality.csv`
A spreadsheet-friendly version of the worksheet coverage report for customer review and planning workshops.

### `image-import-variables.tfvars.example`
A Terraform varfile template for custom image IDs. Populate these values after VMware images have been converted, uploaded, and imported as IBM Cloud VPC custom images.

The generated VSI module consumes the `custom_image_ids` map. Copy this example, replace each placeholder with the imported image ID for the matching VM key, and pass the populated file to Terraform with `-var-file`.

### `migration-runbook.md`
A generated operational runbook that explains the recommended sequence: review mappings, validate readiness, stage or import images, update image IDs, apply Terraform, validate the target environment, and execute cutover.

## Recommended Workflow
1. Upload the RVTools export and review the generated business case.
2. Adjust profile, storage, subnet, and security group overrides as needed.
3. Build and download the Terraform ZIP bundle.
4. Review `vm-mapping.csv` with application and migration stakeholders.
5. Use `migration-manifest.json` as the structured handoff for automation or migration tooling.
6. Resolve image readiness `Blocked` items and review firmware, boot disk, OS, and guest customization concerns.
7. Review `memory-readiness.csv` to validate profile sizing, memory pressure, reservations, limits, and hot-add dependencies.
8. Review `readiness-findings.csv` to remediate snapshots, mounted media, USB dependencies, VMware Tools concerns, and RVTools health findings.
9. Review `assessment-quality.csv` to confirm workbook coverage and confidence before finalizing migration waves.
10. Review `nic-mapping.csv` to confirm primary and secondary network interface placement and source switch/port context.
11. Review `disk-mapping.csv` to confirm data disk volume creation and attachment plans.
12. Review `partition-mapping.csv` for partition free-space context and unmatched partition rows.
13. Import or replicate VMware images using the approved migration approach.
14. Record resulting IBM Cloud custom image IDs in a copy of `image-import-variables.tfvars.example` and pass the populated file to Terraform with `-var-file`.
15. Apply Terraform using Plain CLI or IBM Schematics.
16. Validate boot, network, storage, monitoring, backup, and application health before cutover.

## Current Scope
This release creates the handoff package, custom image ID varfile template, per-disk volume mapping, advisory partition mapping, multi-NIC mapping, network readiness, memory readiness sizing, advisory migration readiness findings, and advisory assessment quality reporting. It does not yet automate VMDK conversion, Cloud Object Storage upload, image import, RackWare API integration, or cutover orchestration.

Those are intentionally left as later adapters so the handoff format can remain stable and tool-neutral.
