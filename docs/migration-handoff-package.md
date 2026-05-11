# Migration Handoff Package

## Purpose
The migration handoff package extends the Terraform ZIP bundle with planning files that connect the generated IBM Cloud VPC infrastructure to the image migration and cutover workflow.

Terraform remains responsible for the target VPC foundation, modules, and infrastructure definitions. The handoff files help customers, migration teams, or partner tooling understand which VMware workload maps to which target IBM Cloud resource.

## Generated Files
### `migration-manifest.json`
A tool-neutral JSON document containing project-level target settings and per-VM source, target, migration, and assessment fields.

Use this file when integrating with scripts, RackWare-style workflows, migration factory tooling, or future adapters.

### `vm-mapping.csv`
A spreadsheet-friendly view of the same source-to-target mapping. This is intended for customer workshops, wave planning, and migration team review.

### `image-import-variables.tfvars.example`
A placeholder Terraform variables file for custom image IDs. Populate these values after VMware images have been converted, uploaded, and imported as IBM Cloud VPC custom images.

The file is intentionally an example in this release. It gives teams a stable place to record image IDs before the VSI module is wired to provision directly from imported images.

### `migration-runbook.md`
A generated operational runbook that explains the recommended sequence: review mappings, validate readiness, stage or import images, update image IDs, apply Terraform, validate the target environment, and execute cutover.

## Recommended Workflow
1. Upload the RVTools export and review the generated business case.
2. Adjust profile, storage, subnet, and security group overrides as needed.
3. Build and download the Terraform ZIP bundle.
4. Review `vm-mapping.csv` with application and migration stakeholders.
5. Use `migration-manifest.json` as the structured handoff for automation or migration tooling.
6. Import or replicate VMware images using the approved migration approach.
7. Record resulting IBM Cloud custom image IDs in a copy of `image-import-variables.tfvars.example`.
8. Apply Terraform using Plain CLI or IBM Schematics.
9. Validate boot, network, storage, monitoring, backup, and application health before cutover.

## Current Scope
This release creates the handoff package and image ID placeholders. It does not yet automate VMDK conversion, Cloud Object Storage upload, image import, RackWare API integration, or cutover orchestration.

Those are intentionally left as later adapters so the handoff format can remain stable and tool-neutral.
