# Demo Video Narration Script

This script is intended for a 5 minute workshop-style screen recording demo for IBM internal reviewers, GitHub repo visitors, and customer demo audiences.

## Narration

This is the RVTools to IBM Cloud VPC migration planning tool. It takes a standard VMware RVTools workbook and turns it into a structured IBM Cloud VPC Terraform package, along with the handoff files that migration teams need before image import, Terraform plan, and cutover.

The goal is not to magically move workloads. The goal is to turn source inventory into reviewable infrastructure as code, readiness signals, and a clean operator package.

I will start with the included small sample workbook, rvtools-small-complete.xlsx. After upload, the app parses the RVTools tabs and builds an assessment workbench.

The Overview gives an estate summary, readiness counts, assessment quality, and the Guided Migration Assistant. This checklist helps a first-time user understand the sequence: review blockers, track remediation, complete wave planning, update image import status, review Migration Ops, and then build the Terraform bundle.

The assistant can apply safe defaults, such as setting blank image import statuses to Pending and creating open remediation tracker rows. It does not mark images imported, change profiles or subnets, build Terraform, or perform migration.

The Readiness tab groups image, migration, memory, and network findings so teams can deal with blocked items before packaging.

The Remediation Backlog turns those findings into trackable work items with status, owner, due date, and notes.

In VM Review, the user can decide what stays in scope and adjust target decisions, such as profile overrides, storage tier overrides, network placement, subnet, and security group mapping. These decisions are preserved in planning state so the work can be paused and resumed.

Wave Planning lets migration teams assign wave, cutover group, owner, application, priority, and dependency group.

Image Import Planning groups active VMs by source image and tracks the import lifecycle, including target catalog IDs after images are imported into IBM Cloud.

Migration Ops ties the planning pieces together. It shows which workloads are ready, which require review, and which remain blocked because of missing planning fields, unresolved remediation, or pending image import.

The Export tab is where the Terraform handoff is built. Package settings include the VPC name, deployment target, address prefix strategy, subnet CIDRs, and optional SSH source CIDR.

The app runs package preflight before building. If there are blockers, the build stops and tells the user what to fix or exclude.

Once the package is ready, the app downloads a ZIP containing the Terraform project, mapping CSVs, readiness exports, planning state, preflight reports, image import variables, a migration runbook, and a root README for the Terraform operator.

Inside the ZIP, the Terraform files are organized into root files and modules for networking, storage, and virtual server instances.

The handoff files help teams review VM mappings, NIC mappings, disk mappings, readiness findings, pricing diagnostics, remediation, image import status, and cutover readiness.

The root README gives the Terraform operator the next steps: review preflight, replace image ID placeholders, validate the package, run Terraform plan, and confirm all manual inputs such as IBM Cloud credentials, quota, profiles, network design, and custom image IDs.

That is the purpose of this tool: convert RVTools exports into an IBM Cloud VPC Terraform package with enough planning context that architects, migration teams, and Terraform operators can move forward with confidence.

The tool does not replace application validation or migration execution, but it gives the team a practical, auditable starting point for the IBM Cloud VPC migration workflow.
