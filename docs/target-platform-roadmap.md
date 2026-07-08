# Target Platform Roadmap

The current application targets IBM Cloud Virtual Servers for VPC. Carbon should
make that migration path clearer before the project adds additional target
platforms.

## Current Target

The production target is:

- IBM Cloud VPC
- virtual server instances
- VPC subnets and security groups
- block storage volumes
- optional custom image IDs
- Terraform package generation
- operational handoff files for image import, remediation, wave planning, and
  cutover readiness

This target should remain the default until Carbon is promoted or deliberately
re-scoped.

## Repository Strategy

Do not fork the repository for target platforms. Keep one shared migration
engine and add target-specific planners/renderers behind explicit target
selection when a new platform is mature enough.

Recommended structure:

- shared RVTools parsing and normalized VM model
- shared readiness and assessment quality logic
- shared pricing and decision-audit concepts where applicable
- target-specific validation
- target-specific package renderers
- target-specific handoff/runbook sections

This keeps source workbook interpretation consistent while allowing different
deployment targets to produce different outputs.

## Carbon Migration-Facilitation Opportunities

Carbon can help the VMware-to-IBM Cloud VPC process by becoming a migration
workbench, not only an export screen.

High-value additions:

- app/wave/cutover readiness dashboard
- next-action queues for network assignment, image import, remediation,
  profile overrides, and cutover blockers
- dependency-aware wave sequencing
- image import lifecycle tracking from source image to final custom image ID
- per-wave migration runbook generation
- package preflight autofill suggestions for low-risk findings
- owner-focused views for remediation and cutover readiness
- final migration factory handoff view with owners, blockers, image status,
  Terraform files, and runbook links

## OpenShift Virtualization / ROVS

Red Hat OpenShift Virtualization can make sense as a future target option, but
it should not be added as a simple toggle on the existing VPC VSI Terraform
path.

Treat it as a separate target-platform track because it needs different
planning outputs and validation rules.

Potential future target labels:

- IBM Cloud VPC VSI
- IBM Cloud VPC VSI with custom image import
- Red Hat OpenShift Virtualization
- Red Hat OpenShift Virtualization Service, if that becomes the selected
  product packaging for the deployment environment

An OpenShift Virtualization target would likely need:

- namespace or project mapping
- VM manifest generation instead of VSI Terraform resources
- storage class mapping instead of IBM Cloud block volume tiers
- network attachment definitions
- OpenShift cluster capacity checks
- MTV or equivalent migration-tool handoff assumptions
- different readiness rules for guest OS, disk, network, and firmware
- separate runbook sections for cluster preparation and VM validation

## Recommended Sequence

1. Finish Carbon promotion hardening for IBM Cloud VPC.
2. Add more real-workbook edge fixtures and browser/accessibility coverage.
3. Introduce a target-platform abstraction only after the VPC path is stable.
4. Prototype OpenShift Virtualization output as a non-default experimental
   renderer.
5. Add promotion gates for that target before exposing it to users.

## Non-Goals For The Current VPC Track

The current tool should not yet:

- execute Terraform
- move VMDK files
- call image migration APIs
- orchestrate application cutover
- generate OpenShift VM manifests from the VPC renderer
- replace specialized migration tools such as MTV, RackWare, or partner
  migration factory tooling

The near-term goal is reliable assessment, planning, Terraform generation, and
handoff package quality for IBM Cloud VPC.
