# Migration Handoff Package

## Purpose
The migration handoff package extends the Terraform ZIP bundle with planning files that connect the generated IBM Cloud VPC infrastructure to the image migration and cutover workflow.

Terraform remains responsible for the target VPC foundation, modules, and infrastructure definitions. The handoff files help customers, migration teams, or partner tooling understand which VMware workload maps to which target IBM Cloud resource.

## Generated Files
The Export tab previews the major ZIP contents before build, including each file or folder's purpose and primary owner. The preview is informational and does not change the generated ZIP layout.

### `README.md`
Root Terraform operator instructions for the downloaded package. It lists the
recommended review order, image ID varfile workflow, local Terraform CLI
commands, IBM Schematics notes when selected, and clear boundaries for what the
app does not automate.

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

### `cutover-readiness.csv`
A Migration Ops readiness file showing VM, wave, cutover group, owner, application, cutover status, blocker category, blocker reason, and recommended next action.

Use this file in migration command center reviews to confirm that each VM has complete wave planning fields, resolved remediation, and imported source images before scheduling cutover.

### `planning-state.json`
A reloadable planning-state bundle containing VM decision fields, wave planning fields, remediation tracker data, image import status, and project metadata.

Use this file to resume planning in a later app session after uploading the same RVTools workbook. The app reports how many VM decisions, wave rows, remediation items, and image groups were restored, plus any skipped rows.

### `assessment-quality.json`
A structured workbook-level quality report showing RVTools worksheet coverage, row counts, confidence, and planning impact. Use it to understand whether sizing, readiness, storage, and network planning signals are based on complete workbook data or fallback metadata.

### `assessment-quality.csv`
A spreadsheet-friendly version of the worksheet coverage report for customer review and planning workshops.

### `preflight-report.json` and `preflight-report.csv`
Package safety reports generated before ZIP creation. Blocker findings stop package generation; warning findings are exported for review.

These reports cover blocked readiness, empty in-scope packages, unresolved custom image placeholders, invalid or overlapping CIDRs, duplicate Terraform resource names, missing subnet/security group mappings, unsupported storage tiers, and profile/region support warnings.

Each finding includes a `Fix Category` to route work to source RVTools/vSphere remediation, app planning updates, VM exclusion from the package, or Terraform operator review.

### `pricing-diagnostics.json` and `pricing-diagnostics.csv`
Pricing audit files showing catalog mode, pricing status, mapped billing dimensions, selected Power VS deployment metadata when available, unmapped catalog metrics and reasons, and per-VM pricing source/status.

### `image-import-variables.tfvars.example`
A Terraform varfile template for custom image IDs. Populate these values after VMware images have been converted, uploaded, and imported as IBM Cloud VPC custom images.

The generated VSI module consumes the `custom_image_ids` map. Copy this example, replace each placeholder with the imported image ID for the matching VM key, and pass the populated file to Terraform with `-var-file`.

### `migration-runbook.md`
A generated operational runbook that explains the recommended sequence: review mappings, validate readiness, stage or import images, update image IDs, apply Terraform, validate the target environment, and execute cutover.

## Recommended Workflow
1. Upload the RVTools export and review the generated business case.
2. Adjust profile, storage, subnet, and security group overrides as needed.
3. Build the Terraform ZIP bundle and resolve any preflight blockers.
4. Download the Terraform ZIP bundle.
5. Review `preflight-report.csv` and `pricing-diagnostics.csv` for package safety and pricing confidence.
6. Review `vm-mapping.csv` with application and migration stakeholders.
7. Use `migration-manifest.json` as the structured handoff for automation or migration tooling.
8. Resolve image readiness `Blocked` items and review firmware, boot disk, OS, and guest customization concerns.
9. Review `memory-readiness.csv` to validate profile sizing, memory pressure, reservations, limits, and hot-add dependencies.
10. Review `readiness-findings.csv` to remediate snapshots, mounted media, USB dependencies, VMware Tools concerns, and RVTools health findings.
11. Review `assessment-quality.csv` to confirm workbook coverage and confidence before finalizing migration waves.
12. Review `nic-mapping.csv` to confirm primary and secondary network interface placement and source switch/port context.
13. Review `disk-mapping.csv` to confirm data disk volume creation and attachment plans.
14. Review `partition-mapping.csv` for partition free-space context and unmatched partition rows.
15. Review `cutover-readiness.csv` by wave and cutover group before scheduling execution.
16. Save `planning-state.json` if planning will resume across sessions or teams.
17. Import or replicate VMware images using the approved migration approach.
18. Record resulting IBM Cloud custom image IDs in a copy of `image-import-variables.tfvars.example` and pass the populated file to Terraform with `-var-file`.
19. Apply Terraform using Plain CLI or IBM Schematics.
20. Validate boot, network, storage, monitoring, backup, and application health before cutover.

## Current Scope
This release creates the handoff package, package preflight reports, pricing diagnostics, custom image ID varfile template, reloadable planning state, cutover readiness export, per-disk volume mapping, advisory partition mapping, multi-NIC mapping, network readiness, memory readiness sizing, migration readiness findings, and assessment quality reporting. It does not yet automate VMDK conversion, Cloud Object Storage upload, image import, RackWare API integration, Terraform execution, or cutover orchestration.

Those are intentionally left as later adapters so the handoff format can remain stable and tool-neutral.
