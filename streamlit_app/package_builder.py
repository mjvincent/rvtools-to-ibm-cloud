import io
import zipfile

from assessment_quality import (
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
)
from handoff import (
    decision_audit_export,
    generate_cutover_readiness_csv,
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_memory_readiness_csv,
    generate_migration_manifest,
    generate_migration_runbook,
    generate_nic_mapping_csv,
    generate_partition_mapping_csv,
    generate_planning_state_json,
    generate_pricing_diagnostics_csv,
    generate_pricing_diagnostics_json,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
    image_import_export,
    remediation_tracker_export,
)
from preflight import generate_preflight_report_csv, generate_preflight_report_json
from terraform_renderer import generate_tfvars, render_terraform_templates


def generate_terraform_operator_readme(context):
    """Generate root README instructions for Terraform package operators."""
    project = context.get("project_name") or "my-ibm-migration"
    region = context.get("target_region") or "us-south"
    zone = context.get("target_zone") or "us-south-1"
    vpc_name = context.get("vpc_name") or "migration-vpc"
    deployment_target = context.get("deployment_target") or "Plain CLI"

    if deployment_target == "IBM Schematics":
        target_notes = """## IBM Schematics Notes

This package was generated for IBM Schematics. The root `main.tf` omits a
local backend block so Schematics can manage Terraform state.

Before creating or updating a Schematics workspace:
- Upload the extracted Terraform project files.
- Provide IBM Cloud credentials through the approved Schematics mechanism.
- Add a populated custom image tfvars file after image import.
- Review the Schematics plan before applying.
"""
    else:
        target_notes = """## Local CLI Notes

This package was generated for local Terraform CLI usage. The root `main.tf`
includes a local backend block.
"""

    return f"""# Terraform Operator README

This package contains IBM Cloud VPC Terraform generated from RVTools planning
data for `{project}`.

## Package Context

- Project: `{project}`
- Region: `{region}`
- Zone: `{zone}`
- VPC name: `{vpc_name}`
- Deployment target: `{deployment_target}`

## Operator Workflow

1. Extract this ZIP into a clean working directory.
2. Review `preflight-report.csv` and resolve blockers before planning.
3. Review `vm-mapping.csv`, `nic-mapping.csv`, `disk-mapping.csv`, and
   `cutover-readiness.csv` with the migration team.
4. Copy `image-import-variables.tfvars.example` to a new tfvars file.
5. Replace every `replace-with-imported-image-id` placeholder with the IBM
   Cloud VPC custom image ID created after image import.
6. Confirm IBM Cloud credentials, region, zone, VPC, subnet, security group,
   quota, and profile availability outside this app.
7. Run:

```bash
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan -var-file=<populated-image-vars.tfvars>
```

8. Review the Terraform plan with infrastructure, security, application, and
   migration owners before apply.

## Validation Modes

- Package preflight runs inside the app before ZIP creation and blocks unsafe
  packages.
- Offline format validation checks generated Terraform without provider
  downloads:

```bash
python scripts/validate_terraform_package.py
terraform fmt -check -recursive
```

- Strict init validation is intended for CI, release checks, or connected
  operator review:

```bash
python scripts/validate_terraform_package.py --init-validate
```

- Local provider download tolerance is only for VPN, proxy, DNS, or offline
  environments where provider downloads fail:

```bash
python scripts/validate_terraform_package.py --init-validate --allow-provider-download-failure
```

Do not use the tolerant provider-download flag in CI.

{target_notes}

## Required Reviews Before `terraform plan`

- `preflight-report.csv`
- `image-import-variables.tfvars.example`
- `vm-mapping.csv`
- `nic-mapping.csv`
- `disk-mapping.csv`
- `cutover-readiness.csv`
- `migration-runbook.md`

## Manual Inputs Required

- IBM Cloud credentials and account context.
- Imported IBM Cloud VPC custom image IDs.
- Region and zone confirmation.
- VPC, subnet, address prefix, and security group review.
- Quota, profile, storage, and IP availability confirmation.

## Boundaries

This app generates Terraform and migration handoff files. It does not execute
Terraform, import images, upload images to IBM Cloud Object Storage, call
migration tooling, validate quota, or perform application cutover.
"""


def build_terraform_bundle(
    final_vms,
    unique_nets,
    target_region,
    target_zone,
    generate_security_groups,
    vpc_name,
    custom_cidrs,
    address_prefix_strategy,
    deployment_target,
    project_name,
    ssh_source_cidr,
    pricing_metadata,
    assessment_quality,
    pricing_catalog,
    preflight_findings,
    remediation_tracker,
    image_import_status,
):
    terraform_files = render_terraform_templates(
        final_vms,
        unique_nets,
        target_region,
        target_zone,
        generate_security_groups,
        vpc_name,
        custom_cidrs,
        address_prefix_strategy,
        deployment_target,
        project_name,
        ssh_source_cidr,
    )
    (
        vsi, root_main, stor, net, root_vars, root_out,
        net_vars, net_out, vsi_vars, vsi_out, stor_vars, stor_out,
    ) = terraform_files

    migration_context = {
        "project_name": project_name,
        "target_region": target_region,
        "target_zone": target_zone,
        "vpc_name": vpc_name,
        "address_prefix_strategy": address_prefix_strategy,
        "deployment_target": deployment_target,
        "generate_security_groups": generate_security_groups,
        "ssh_source_cidr": ssh_source_cidr,
        "pricing_mode": pricing_metadata.get("mode"),
        "pricing_source": pricing_metadata.get("source"),
        "pricing_confidence": pricing_metadata.get("confidence"),
        "pricing_status": pricing_metadata.get("pricing_status"),
        "pricing_last_updated": pricing_metadata.get("last_updated"),
        "assessment_quality": assessment_quality,
    }
    planning_state_metadata = {
        "project_name": project_name,
        "target_region": target_region,
        "target_zone": target_zone,
    }

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a") as zf:
        zf.writestr(
            "README.md",
            generate_terraform_operator_readme(migration_context),
        )
        zf.writestr("main.tf", root_main)
        zf.writestr("variables.tf", root_vars)
        zf.writestr("outputs.tf", root_out)
        zf.writestr(
            "terraform.tfvars",
            generate_tfvars(target_region, target_zone, project_name),
        )
        zf.writestr("modules/networking/main.tf", net)
        zf.writestr("modules/networking/variables.tf", net_vars)
        zf.writestr("modules/networking/outputs.tf", net_out)
        zf.writestr("modules/vsi/main.tf", vsi)
        zf.writestr("modules/vsi/variables.tf", vsi_vars)
        zf.writestr("modules/vsi/outputs.tf", vsi_out)
        zf.writestr("modules/storage/main.tf", stor)
        zf.writestr("modules/storage/variables.tf", stor_vars)
        zf.writestr("modules/storage/outputs.tf", stor_out)
        zf.writestr(
            "migration-manifest.json",
            generate_migration_manifest(
                final_vms,
                migration_context,
                image_import_status=image_import_status,
                pricing_catalog=pricing_catalog,
                remediation_tracker=remediation_tracker,
            ),
        )
        zf.writestr(
            "assessment-quality.json",
            generate_assessment_quality_json(assessment_quality),
        )
        zf.writestr(
            "assessment-quality.csv",
            generate_assessment_quality_csv(assessment_quality),
        )
        zf.writestr(
            "preflight-report.json",
            generate_preflight_report_json(preflight_findings),
        )
        zf.writestr(
            "preflight-report.csv",
            generate_preflight_report_csv(preflight_findings),
        )
        zf.writestr(
            "pricing-diagnostics.json",
            generate_pricing_diagnostics_json(pricing_catalog, final_vms),
        )
        zf.writestr(
            "pricing-diagnostics.csv",
            generate_pricing_diagnostics_csv(pricing_catalog, final_vms),
        )
        zf.writestr(
            "decision-audit.csv",
            decision_audit_export(final_vms, pricing_catalog),
        )
        zf.writestr(
            "remediation-backlog.csv",
            remediation_tracker_export(final_vms, remediation_tracker),
        )
        zf.writestr(
            "image-import-plan.csv",
            image_import_export(final_vms, image_import_status),
        )
        zf.writestr(
            "cutover-readiness.csv",
            generate_cutover_readiness_csv(
                final_vms,
                remediation_tracker=remediation_tracker,
                image_import_status=image_import_status,
            ),
        )
        zf.writestr(
            "planning-state.json",
            generate_planning_state_json(
                final_vms,
                remediation_tracker=remediation_tracker,
                image_import_status=image_import_status,
                metadata=planning_state_metadata,
            ),
        )
        zf.writestr("vm-mapping.csv", generate_vm_mapping_csv(final_vms))
        zf.writestr("disk-mapping.csv", generate_disk_mapping_csv(final_vms))
        zf.writestr(
            "partition-mapping.csv",
            generate_partition_mapping_csv(final_vms),
        )
        zf.writestr(
            "nic-mapping.csv",
            generate_nic_mapping_csv(final_vms, generate_security_groups),
        )
        zf.writestr(
            "memory-readiness.csv",
            generate_memory_readiness_csv(final_vms),
        )
        zf.writestr(
            "readiness-findings.csv",
            generate_readiness_findings_csv(final_vms),
        )
        zf.writestr(
            "image-import-variables.tfvars.example",
            generate_image_import_tfvars(final_vms),
        )
        zf.writestr(
            "migration-runbook.md",
            generate_migration_runbook(migration_context),
        )
    return zip_buffer.getvalue()
