from .utils import _clean_value


def generate_migration_runbook(context):
    """Create a customer-facing runbook for the generated handoff package."""
    project = _clean_value(context.get('project_name'), 'my-ibm-migration')
    region = _clean_value(context.get('target_region'), 'us-south')
    zone = _clean_value(context.get('target_zone'), 'us-south-1')
    vpc_name = _clean_value(context.get('vpc_name'), 'migration-vpc')
    deployment_target = _clean_value(
        context.get('deployment_target'), 'Plain CLI'
    )

    return f"""# Migration Handoff Runbook

## Scope
This runbook accompanies the Terraform bundle for `{project}`. It bridges the gap between the generated IBM Cloud VPC infrastructure and the separate image migration or replication process used to bring VMware workloads into IBM Cloud Virtual Servers for VPC.

## Target Environment
- IBM Cloud region: `{region}`
- IBM Cloud zone: `{zone}`
- VPC name: `{vpc_name}`
- Deployment target: `{deployment_target}`

## Generated Handoff Files
- `migration-manifest.json`: Tool-neutral source-to-target mapping for each VM.
- `vm-mapping.csv`: Spreadsheet-friendly migration planning view.
- `nic-mapping.csv`: Per-NIC source-to-target network mapping view.
- `disk-mapping.csv`: Per-disk boot/data volume mapping view.
- `memory-readiness.csv`: Memory pressure, reservation, limit, and sizing review.
- `readiness-findings.csv`: Row-level migration readiness findings and remediation actions.
- `image-import-variables.tfvars.example`: Terraform varfile template for imported custom image IDs.
- `migration-runbook.md`: This operational guide.

## Recommended Workflow
1. Review `vm-mapping.csv` with the application, infrastructure, security, and migration teams.
2. Confirm migration waves, cutover groups, and business priority for each VM.
3. Review image readiness status, firmware, boot disk size, and guest customization requirement for each VM.
4. Review memory readiness status and validate any VM with swapping, ballooning, reservations, limits, or hot-add dependencies.
5. Review migration readiness status and resolve `Blocked` findings in `readiness-findings.csv` before scheduling replication or image export.
6. Assign owners for `Review` findings such as VMware Tools status, minor snapshots, powered-off validation, or RVTools health warnings.
7. Review `nic-mapping.csv` to confirm primary and secondary network interface placement.
8. Review `disk-mapping.csv` to confirm boot disks are covered by imported images and data disks are created as attached block volumes.
9. Validate source guest OS, firmware, disk layout, and IP requirements before export or replication.
10. Export, convert, replicate, or otherwise stage the VMware images using the approved migration method.
11. Upload converted images to IBM Cloud Object Storage when using custom image import.
12. Import each image as an IBM Cloud VPC custom image and capture the resulting image IDs.
13. Copy `image-import-variables.tfvars.example`, replace placeholders with real image IDs, and pass the populated file to Terraform with `-var-file`.
14. Apply the generated Terraform using the selected deployment target.
15. Validate VSI boot, network placement, security group membership, disk attachment, monitoring, backup, and application health.
16. Execute DNS, IP, load balancer, or application cutover steps according to the migration wave plan.

## Notes
Terraform builds the target VPC foundation and VSI definitions. It does not move VMDK files or perform application cutover by itself. Use the manifest and CSV as the handoff layer for RackWare, custom scripts, IBM Cloud image import, or a migration factory workflow.
"""


