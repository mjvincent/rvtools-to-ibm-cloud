# Terraform Overrides Reference

## Purpose
This document explains the new Terraform override controls available in the Streamlit app. These controls let users customize generated IBM Cloud VPC infrastructure before exporting the Terraform bundle.

## Available Overrides
### VPC Name
The `VPC Name` field defines the name of the generated `ibm_is_vpc` resource.

### Address Prefix Strategy
Choose between:
* `manual` — preserves discovered or user-entered CIDR ranges for VPC address prefixes and subnets.
* `auto` — allows the provider to assign address prefixes automatically.

The default value is `manual`.

### Custom CIDR per Subnet
For each discovered network, the app creates a custom CIDR text input.

If a user enters a value in this field, that CIDR is used for the generated `ibm_is_vpc_address_prefix` and `ibm_is_subnet` resources for that network.

### Deployment Target
You can choose one of the following deployment targets:
* `Plain CLI` — generates Terraform with a local backend block (`terraform.tfstate`) for local CLI execution.
* `IBM Schematics` — omits the backend block so IBM Schematics can manage Terraform state itself.

This selection does not change the generated resources, only the state management configuration in the root `main.tf`.

## Generated Terraform Behavior
The generated ZIP bundle includes:
* Root module files: `main.tf`, `variables.tf`, `outputs.tf`
* `modules/networking`: VPC, address prefixes, subnets, and security groups
* `modules/storage`: IBM Cloud data disk volumes
* `modules/vsi`: VSI instances, primary/secondary network interfaces, and data volume attachments

When overrides are used:
* The selected `VPC Name` is applied to the VPC resource
* Custom CIDRs are applied to each subnet and address prefix
* The chosen address prefix strategy is applied via `address_preference`
* The chosen deployment target controls whether the root module includes a backend block

## Notes
* `manual` mode is ideal for migrations that need IP parity with on-premises networks.
* `auto` mode is useful for exploratory or greenfield deployments where explicit CIDR mapping is not required.
* If a custom CIDR is missing, the app falls back to a generated deterministic CIDR based on the discovered network index.

## Recommended Usage
1. Upload the RVTools XLSX file in the Streamlit app.
2. Expand `Terraform Overrides`.
3. Enter a meaningful VPC name and project name.
4. Confirm or override the CIDRs for each subnet.
5. Select the appropriate deployment target.
6. Build the Terraform project and download the ZIP bundle.


## Relationship to Migration Handoff Files
The Terraform override values are also reflected in the generated migration handoff files. If a user overrides a VSI profile, storage tier, subnet, or security group mapping before building the ZIP bundle, the manifest and CSV show both the recommended value and the effective value used for migration planning.

The `image-import-variables.tfvars.example` file is provided as a placeholder for custom image IDs after VMware image conversion or replication. In this release, it is a handoff aid and is not automatically consumed by the generated VSI module.

Image readiness fields are advisory. `Ready`, `Review`, or `Blocked` values do not change Terraform generation, profile overrides, storage tier overrides, subnet CIDRs, backend selection, or module output. They are included to guide image migration planning before custom image import or replication workflows.

Migration readiness fields are also advisory. Snapshot, VMware Tools, mounted media, USB, and health findings do not alter Terraform output. They are included in the dashboard and handoff files so teams can remediate source-side risks before export, replication, image import, or cutover.

Storage tier overrides apply to every generated data disk volume for that VM. The boot disk is not generated as an IBM Cloud block volume because it is expected to be covered by the imported custom image workflow.

Custom CIDR overrides apply to every discovered source network from `vNetwork`, not only the primary VM network. Connected secondary NICs use the subnet and security group generated for their own source network. Disconnected NICs remain in `nic-mapping.csv` and the manifest but do not create Terraform network interfaces.
