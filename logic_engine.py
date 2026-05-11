import csv
import io
import json
import math
import re

IMAGE_MAX_GB = 250
IMAGE_MIN_GB = 10

# --- STRATEGY B: ECONOMIC OPTIMIZER CATALOG ---
IBM_VPC_CATALOG = [
    {"name": "cx2-2x4", "cpu": 2, "ram": 4, "hourly": 0.063},
    {"name": "bx2-2x8", "cpu": 2, "ram": 8, "hourly": 0.114},
    {"name": "mx2-2x16", "cpu": 2, "ram": 16, "hourly": 0.158},
    {"name": "cx2-4x8", "cpu": 4, "ram": 8, "hourly": 0.126},
    {"name": "bx2-4x16", "cpu": 4, "ram": 16, "hourly": 0.228},
    {"name": "mx2-4x32", "cpu": 4, "ram": 32, "hourly": 0.316},
    {"name": "cx2-8x16", "cpu": 8, "ram": 16, "hourly": 0.252},
    {"name": "bx2-8x32", "cpu": 8, "ram": 32, "hourly": 0.456},
]


def get_catalog_profiles():
    """Returns the list of supported IBM VPC profile names."""
    return [profile['name'] for profile in IBM_VPC_CATALOG]


def find_cheapest_fit(target_cpu, target_ram):
    """Finds the lowest-priced profile that fits requirements."""
    candidates = [
        p for p in IBM_VPC_CATALOG
        if p['cpu'] >= target_cpu and p['ram'] >= target_ram
    ]
    if not candidates:
        return {"name": "bx2-16x64", "cpu": 16, "ram": 64, "hourly": 0.912}
    optimized = sorted(candidates, key=lambda x: x['hourly'])
    return optimized[0]


def map_vmware_to_ibm_vpc(cpus, memory, usage, region,
                          threshold, storage_gb, tier):
    """Strategy B: Full Solution Cost (Compute + Storage)."""
    util_factor = threshold / 100
    needed_cpu = max(1, round(cpus * util_factor))
    needed_ram = max(2, round((memory / 1024) * 0.8))
    optimized = find_cheapest_fit(needed_cpu, needed_ram)

    tier_rates = {
        "3iops-tier": 0.10,
        "5iops-tier": 0.13,
        "10iops-tier": 0.17
    }

    compute_monthly = round(optimized['hourly'] * 730, 2)
    storage_monthly = round(storage_gb * tier_rates.get(tier, 0.10), 2)
    total_monthly = round(compute_monthly + storage_monthly, 2)

    return {
        "profile": optimized['name'],
        "compute_cost": compute_monthly,
        "storage_cost": storage_monthly,
        "monthly": total_monthly,
        "is_rightsized": optimized['cpu'] < cpus
    }


def _clean_text(value):
    return str(_clean_value(value)).strip()


def _clean_number(value, default=0):
    value = _clean_value(value, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def assess_image_readiness(guest_os, firmware, boot_disk_gb,
                           disk_count, power_state):
    """
    Assess whether VM metadata is ready for IBM Cloud VPC image planning.

    This is advisory only. It does not automate conversion, COS upload, image
    import, or Terraform provisioning from custom images.
    """
    reasons = []
    blockers = []
    guest_os_text = _clean_text(guest_os)
    firmware_text = _clean_text(firmware)
    power_text = _clean_text(power_state).lower()
    boot_gb = round(_clean_number(boot_disk_gb, 0), 2)
    disks = int(_clean_number(disk_count, 0))
    os_lower = guest_os_text.lower()

    if "windows" in os_lower:
        guest_customization = "cloudbase-init required"
    elif any(token in os_lower for token in [
        "linux", "ubuntu", "debian", "red hat", "rhel",
        "centos", "suse", "oracle"
    ]):
        guest_customization = "cloud-init required"
    elif guest_os_text:
        guest_customization = "validate guest initialization"
        reasons.append("Guest OS not recognized by rule; confirm IBM OS value")
    else:
        guest_customization = "unknown"
        reasons.append("Guest OS missing; confirm IBM OS value")

    if not firmware_text:
        reasons.append("Firmware missing; confirm BIOS or EFI boot mode")

    if boot_gb <= 0:
        reasons.append("Boot disk size missing; confirm image size")
    elif boot_gb > IMAGE_MAX_GB:
        blockers.append("Boot disk exceeds IBM Cloud custom image 250 GB limit")
    elif boot_gb < IMAGE_MIN_GB:
        reasons.append("Boot disk below 10 GB minimum; IBM rounds up to 10 GB")

    if disks > 1:
        reasons.append("Multiple disks detected; map data disks separately")

    if power_text == "poweredoff":
        reasons.append("VM is powered off; validate source state before export")

    if blockers:
        status = "Blocked"
    elif reasons:
        status = "Review"
    else:
        status = "Ready"
        reasons.append(
            "No metadata blockers found; convert to qcow2/vhd and stage in COS"
        )

    return {
        "status": status,
        "reasons": "; ".join(blockers + reasons),
        "firmware": firmware_text,
        "boot_disk_gb": boot_gb,
        "guest_customization": guest_customization,
        "required_image_format": "qcow2 or vhd",
        "requires_cos_staging": True,
        "max_custom_image_gb": IMAGE_MAX_GB,
        "min_custom_image_gb": IMAGE_MIN_GB,
    }


def _clean_value(value, default=""):
    """Return JSON/CSV friendly values from pandas and Streamlit records."""
    if value is None:
        return default
    try:
        if value != value:
            return default
    except TypeError:
        pass
    if isinstance(value, str):
        stripped = value.strip()
        return default if stripped.lower() == "nan" else stripped
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return default
    return value


def _safe_vm_key(value):
    """Create a stable key for manifests and tfvars examples."""
    cleaned = str(_clean_value(value, "unknown-vm"))
    return cleaned.replace('"', '').replace("'", "")


def _safe_resource_name(value):
    cleaned = str(_clean_value(value, "unknown")).lower()
    cleaned = re.sub(r"[^0-9a-zA-Z_]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    if not cleaned:
        cleaned = "unknown"
    if cleaned[0].isdigit():
        cleaned = f"r_{cleaned}"
    return cleaned


def _vm_disks(vm):
    disks = vm.get('Disk Details') or []
    return disks if isinstance(disks, list) else []


def _vm_data_disks(vm):
    return [disk for disk in _vm_disks(vm) if not disk.get('is_boot')]


def _vm_nics(vm):
    nics = vm.get('Network Details') or []
    return nics if isinstance(nics, list) else []


def _connected_nics(vm):
    return [
        nic for nic in _vm_nics(vm)
        if str(nic.get('connected', True)).lower() == "true"
    ]


def _status_contains(vm, token):
    return token.lower() in str(vm.get('Data Status', '')).lower()


def _effective_profile(vm):
    return _clean_value(vm.get('Override Profile')) or _clean_value(
        vm.get('IBM Profile'), 'bx2-2x8'
    )


def _effective_storage_tier(vm):
    return _clean_value(vm.get('Override Storage Tier')) or _clean_value(
        vm.get('Storage Tier'), '3iops-tier'
    )


def _migration_vm_record(vm):
    vm_name = _safe_vm_key(vm.get('VM Name'))
    effective_profile = _effective_profile(vm)
    effective_storage_tier = _effective_storage_tier(vm)
    data_status = _clean_value(vm.get('Data Status'), 'Unknown')

    return {
        "vm_name": vm_name,
        "source": {
            "power_state": _clean_value(vm.get('Power State')),
            "datacenter": _clean_value(vm.get('Datacenter')),
            "cluster": _clean_value(vm.get('Cluster')),
            "host": _clean_value(vm.get('Host')),
            "network": _clean_value(vm.get('Network'), 'unknown-net'),
            "ip_address": _clean_value(vm.get('Source IP')),
            "guest_os": _clean_value(vm.get('Guest OS')),
            "nic_count": _clean_value(vm.get('NIC Count'), 0),
            "networks": _vm_nics(vm),
            "disk_count": _clean_value(vm.get('Disk Count'), 0),
            "total_disk_gb": _clean_value(vm.get('Total Storage GB'), 0),
            "original_specs": _clean_value(vm.get('Original Specs')),
            "disks": _vm_disks(vm),
        },
        "target": {
            "recommended_profile": _clean_value(vm.get('IBM Profile')),
            "override_profile": _clean_value(vm.get('Override Profile')),
            "effective_profile": effective_profile,
            "subnet": _clean_value(vm.get('Subnet')),
            "security_group": _clean_value(vm.get('Security Group')),
            "recommended_storage_tier": _clean_value(vm.get('Storage Tier')),
            "override_storage_tier": _clean_value(
                vm.get('Override Storage Tier')
            ),
            "effective_storage_tier": effective_storage_tier,
            "custom_image_id": "replace-with-imported-image-id",
            "custom_image_name": f"{vm_name}-custom-image",
            "data_volumes": [
                {
                    "source_disk": _clean_value(disk.get('disk')),
                    "capacity_gb": _clean_value(disk.get('capacity_gb'), 0),
                    "storage_tier": effective_storage_tier,
                    "attachment": "generated"
                }
                for disk in _vm_data_disks(vm)
            ],
        },
        "migration": {
            "wave": "wave-01",
            "cutover_group": "unassigned",
            "priority": "medium",
            "status": "planned",
            "method": "image-import-or-replication-tool",
            "requires_ip_preservation": bool(_clean_value(vm.get('Source IP'))),
        },
        "assessment": {
            "data_status": data_status,
            "right_sized": _clean_value(vm.get('Right-Sized')),
            "high_contention": _status_contains(vm, 'High Contention'),
            "cpu_throttled": _status_contains(vm, 'CPU Throttled'),
            "underutilized": _status_contains(vm, 'Zombie VM'),
            "ready_pct": _clean_value(vm.get('Ready_Pct'), 0),
            "overall_mhz": _clean_value(vm.get('Overall_MHz'), 0),
            "baseline_monthly_cost": _clean_value(
                vm.get('Baseline Cost (Mo)'), 0
            ),
            "estimated_monthly_cost": _clean_value(vm.get('Monthly Cost'), 0),
            "estimated_monthly_savings": _clean_value(
                vm.get('Savings (Mo)'), 0
            ),
        },
        "image_readiness": {
            "status": _clean_value(vm.get('Image Readiness'), 'Review'),
            "reasons": _clean_value(vm.get('Readiness Reasons')),
            "firmware": _clean_value(vm.get('Firmware')),
            "boot_disk_gb": _clean_value(vm.get('Boot Disk GB'), 0),
            "guest_customization": _clean_value(vm.get('Guest Customization')),
            "required_image_format": "qcow2 or vhd",
            "requires_cos_staging": True,
            "max_custom_image_gb": IMAGE_MAX_GB,
            "min_custom_image_gb": IMAGE_MIN_GB,
        },
    }


def generate_migration_manifest(final_vms, context):
    """Create the tool-neutral migration handoff manifest."""
    manifest = {
        "schema_version": "1.0",
        "package_type": "rvtools-to-ibm-cloud-migration-handoff",
        "project": {
            "name": _clean_value(context.get('project_name')),
            "target_region": _clean_value(context.get('target_region')),
            "target_zone": _clean_value(context.get('target_zone')),
            "vpc_name": _clean_value(context.get('vpc_name')),
            "address_prefix_strategy": _clean_value(
                context.get('address_prefix_strategy'), 'manual'
            ),
            "deployment_target": _clean_value(
                context.get('deployment_target'), 'Plain CLI'
            ),
            "security_groups_enabled": bool(
                context.get('generate_security_groups', True)
            ),
        },
        "handoff_files": {
            "vm_mapping_csv": "vm-mapping.csv",
            "disk_mapping_csv": "disk-mapping.csv",
            "nic_mapping_csv": "nic-mapping.csv",
            "runbook": "migration-runbook.md",
            "image_import_tfvars_example": "image-import-variables.tfvars.example",
        },
        "virtual_machines": [
            _migration_vm_record(vm) for vm in final_vms
        ],
    }
    return json.dumps(manifest, indent=2, sort_keys=True)


def generate_vm_mapping_csv(final_vms):
    """Create a migration-team friendly source-to-target mapping CSV."""
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Power State", "Guest OS", "Source IP", "Source Network",
        "Datacenter", "Cluster", "Host", "Disk Count", "Total Storage GB",
        "Firmware", "Boot Disk GB", "Guest Customization",
        "Image Readiness", "Readiness Reasons",
        "Target Subnet", "Security Group", "Recommended Profile",
        "Override Profile", "Effective Profile", "Storage Tier",
        "Override Storage Tier", "Effective Storage Tier", "Custom Image ID",
        "Migration Wave", "Cutover Group", "Migration Status",
        "Data Status", "Monthly Cost", "Baseline Cost", "Savings"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        writer.writerow({
            "VM Name": _safe_vm_key(vm.get('VM Name')),
            "Power State": _clean_value(vm.get('Power State')),
            "Guest OS": _clean_value(vm.get('Guest OS')),
            "Source IP": _clean_value(vm.get('Source IP')),
            "Source Network": _clean_value(vm.get('Network'), 'unknown-net'),
            "Datacenter": _clean_value(vm.get('Datacenter')),
            "Cluster": _clean_value(vm.get('Cluster')),
            "Host": _clean_value(vm.get('Host')),
            "Disk Count": _clean_value(vm.get('Disk Count'), 0),
            "Total Storage GB": _clean_value(vm.get('Total Storage GB'), 0),
            "Firmware": _clean_value(vm.get('Firmware')),
            "Boot Disk GB": _clean_value(vm.get('Boot Disk GB'), 0),
            "Guest Customization": _clean_value(
                vm.get('Guest Customization')
            ),
            "Image Readiness": _clean_value(vm.get('Image Readiness')),
            "Readiness Reasons": _clean_value(vm.get('Readiness Reasons')),
            "Target Subnet": _clean_value(vm.get('Subnet')),
            "Security Group": _clean_value(vm.get('Security Group')),
            "Recommended Profile": _clean_value(vm.get('IBM Profile')),
            "Override Profile": _clean_value(vm.get('Override Profile')),
            "Effective Profile": _effective_profile(vm),
            "Storage Tier": _clean_value(vm.get('Storage Tier')),
            "Override Storage Tier": _clean_value(
                vm.get('Override Storage Tier')
            ),
            "Effective Storage Tier": _effective_storage_tier(vm),
            "Custom Image ID": "replace-with-imported-image-id",
            "Migration Wave": "wave-01",
            "Cutover Group": "unassigned",
            "Migration Status": "planned",
            "Data Status": _clean_value(vm.get('Data Status')),
            "Monthly Cost": _clean_value(vm.get('Monthly Cost'), 0),
            "Baseline Cost": _clean_value(vm.get('Baseline Cost (Mo)'), 0),
            "Savings": _clean_value(vm.get('Savings (Mo)'), 0),
        })
    return output.getvalue()


def _nic_target(nic, enable_security_groups=True):
    source_network = _clean_value(nic.get('network'), 'unknown-net')
    safe_network = _safe_resource_name(source_network)
    target = {
        "subnet": f"module.networking.{safe_network}_id",
        "security_group": "N/A",
    }
    if enable_security_groups:
        target["security_group"] = f"module.networking.{safe_network}_sg_id"
    return target


def generate_nic_mapping_csv(final_vms, enable_security_groups=True):
    """Create a per-NIC source-to-target mapping CSV."""
    output = io.StringIO()
    fieldnames = [
        "VM Name", "NIC Label", "Role", "Planned", "Connected",
        "Starts Connected", "Source Network", "Source IP", "IPv6 Address",
        "MAC Address", "Adapter", "Switch", "Type", "Target Subnet",
        "Target Security Group"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        connected_seen = 0
        for nic in _vm_nics(vm):
            connected = str(nic.get('connected', True)).lower() == "true"
            planned = connected
            role = "disconnected"
            if connected:
                role = "primary" if connected_seen == 0 else "secondary"
                connected_seen += 1
            target = _nic_target(nic, enable_security_groups)

            writer.writerow({
                "VM Name": vm_name,
                "NIC Label": _clean_value(nic.get('label')),
                "Role": role,
                "Planned": planned,
                "Connected": connected,
                "Starts Connected": _clean_value(nic.get('starts_connected')),
                "Source Network": _clean_value(nic.get('network')),
                "Source IP": _clean_value(nic.get('ipv4')),
                "IPv6 Address": _clean_value(nic.get('ipv6')),
                "MAC Address": _clean_value(nic.get('mac_address')),
                "Adapter": _clean_value(nic.get('adapter')),
                "Switch": _clean_value(nic.get('switch')),
                "Type": _clean_value(nic.get('type')),
                "Target Subnet": target["subnet"] if planned else "",
                "Target Security Group": (
                    target["security_group"] if planned else ""
                ),
            })
    return output.getvalue()


def generate_disk_mapping_csv(final_vms):
    """Create a per-disk source-to-target mapping CSV."""
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Disk", "Role", "Capacity GB", "Target Action",
        "Storage Tier", "Terraform Volume", "Attachment Resource",
        "Disk Key", "Disk Path", "Controller", "Label", "Unit Number",
        "SCSI Unit", "Disk Mode", "Thin", "Raw", "Shared Bus"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        safe_vm = _safe_resource_name(vm_name)
        storage_tier = _effective_storage_tier(vm)
        for index, disk in enumerate(_vm_disks(vm)):
            role = "boot" if disk.get('is_boot') else "data"
            safe_disk = _safe_resource_name(disk.get('disk') or f"disk_{index}")
            volume_name = ""
            attachment_name = ""
            target_action = "covered-by-custom-image"
            if role == "data":
                volume_name = f"{safe_vm}_{safe_disk}_vol"
                attachment_name = f"{safe_vm}_{safe_disk}_attach"
                target_action = "create-and-attach-volume"

            writer.writerow({
                "VM Name": vm_name,
                "Disk": _clean_value(disk.get('disk')),
                "Role": role,
                "Capacity GB": _clean_value(disk.get('capacity_gb'), 0),
                "Target Action": target_action,
                "Storage Tier": storage_tier,
                "Terraform Volume": volume_name,
                "Attachment Resource": attachment_name,
                "Disk Key": _clean_value(disk.get('disk_key')),
                "Disk Path": _clean_value(disk.get('disk_path')),
                "Controller": _clean_value(disk.get('controller')),
                "Label": _clean_value(disk.get('label')),
                "Unit Number": _clean_value(disk.get('unit_number')),
                "SCSI Unit": _clean_value(disk.get('scsi_unit')),
                "Disk Mode": _clean_value(disk.get('disk_mode')),
                "Thin": _clean_value(disk.get('thin')),
                "Raw": _clean_value(disk.get('raw')),
                "Shared Bus": _clean_value(disk.get('shared_bus')),
            })
    return output.getvalue()


def generate_image_import_tfvars(final_vms):
    """Create an example tfvars map for imported IBM Cloud custom images."""
    lines = [
        "# Populate these values after VMware images are converted, uploaded,",
        "# and imported as IBM Cloud VPC custom images.",
        "# This file is a handoff aid; wire the map into Terraform when you are",
        "# ready to provision VSIs directly from imported images.",
        "custom_image_ids = {",
    ]
    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        lines.append(f'  "{vm_name}" = "replace-with-imported-image-id"')
    lines.append("}")
    return "\n".join(lines) + "\n"


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
- `image-import-variables.tfvars.example`: Placeholder map for imported custom image IDs.
- `migration-runbook.md`: This operational guide.

## Recommended Workflow
1. Review `vm-mapping.csv` with the application, infrastructure, security, and migration teams.
2. Confirm migration waves, cutover groups, and business priority for each VM.
3. Review image readiness status, firmware, boot disk size, and guest customization requirement for each VM.
4. Resolve `Blocked` items before image import planning and assign owners for `Review` items.
5. Review `nic-mapping.csv` to confirm primary and secondary network interface placement.
6. Review `disk-mapping.csv` to confirm boot disks are covered by imported images and data disks are created as attached block volumes.
7. Validate source guest OS, firmware, disk layout, and IP requirements before export or replication.
8. Export, convert, replicate, or otherwise stage the VMware images using the approved migration method.
9. Upload converted images to IBM Cloud Object Storage when using custom image import.
10. Import each image as an IBM Cloud VPC custom image and capture the resulting image IDs.
11. Copy `image-import-variables.tfvars.example`, replace placeholders with real image IDs, and decide whether to wire those IDs into the VSI module.
12. Apply the generated Terraform using the selected deployment target.
13. Validate VSI boot, network placement, security group membership, disk attachment, monitoring, backup, and application health.
14. Execute DNS, IP, load balancer, or application cutover steps according to the migration wave plan.

## Notes
Terraform builds the target VPC foundation and VSI definitions. It does not move VMDK files or perform application cutover by itself. Use the manifest and CSV as the handoff layer for RackWare, custom scripts, IBM Cloud image import, or a migration factory workflow.
"""


def render_networking_templates(networks_data, vpc_name="migration-vpc", enable_security_groups=True, custom_cidrs=None, address_prefix_strategy="manual", project_name="my-ibm-migration"):
    """
    Renders the networking module main.tf content.
    """
    vpc_safe = vpc_name.replace("-", "_")
    address_preference = (
        "manual" if address_prefix_strategy == "manual"
        else "automatic"
    )

    hcl = f"""
resource "ibm_is_vpc" "{vpc_safe}" {{
  name = "{vpc_name}"
  address_preference = "{address_preference}"
  tags = ["project:{project_name}", "managed-by:rvtools-converter"]
}}
"""

    for i, net in enumerate(networks_data):
        raw_name = net.get('name', 'unknown-net')
        vlan_id = net.get('vlan')
        cidr_key = net.get('cidr_key', net.get('name'))
        cidr = custom_cidrs.get(cidr_key, net.get('cidr', f"10.0.{i+1}.0/24")) if custom_cidrs else net.get('cidr', f"10.0.{i+1}.0/24")

        safe_res = raw_name.lower().replace(" ", "_").replace("-", "_")
        if vlan_id and str(vlan_id).strip():
            safe_res += f"_vlan_{vlan_id}"

        hcl += f"""
resource "ibm_is_vpc_address_prefix" "prefix_{safe_res}" {{
  name = "prefix-{safe_res.replace('_', '-') }"
  zone = var.zone
  vpc  = ibm_is_vpc.{vpc_safe}.id
  cidr = "{cidr}"
}}

resource "ibm_is_subnet" "{safe_res}" {{
  name            = "{safe_res.replace('_', '-')}-subnet"
  vpc             = ibm_is_vpc.{vpc_safe}.id
  zone            = var.zone
  ipv4_cidr_block = "{cidr}"
  depends_on      = [ibm_is_vpc_address_prefix.prefix_{safe_res}]
  tags            = ["project:{project_name}", "network:{safe_res}", "managed-by:rvtools-converter"]
}}
"""

        if enable_security_groups:
            hcl += f"""
resource "ibm_is_security_group" "sg_{safe_res}" {{
  name = "sg-{safe_res.replace('_', '-') }"
  vpc  = ibm_is_vpc.{vpc_safe}.id
  tags = ["project:{project_name}", "network:{safe_res}", "managed-by:rvtools-converter"]
}}

resource "ibm_is_security_group_rule" "ssh_{safe_res}" {{
  security_group = ibm_is_security_group.sg_{safe_res}.id
  direction      = "inbound"
  ip_version     = "ipv4"
  protocol       = "tcp"
  port_min       = 22
  port_max       = 22
  remote         = "0.0.0.0/0"
}}

resource "ibm_is_security_group_rule" "internal_{safe_res}" {{
  security_group = ibm_is_security_group.sg_{safe_res}.id
  direction      = "inbound"
  ip_version     = "ipv4"
  protocol       = "all"
  remote         = "{cidr}"
}}
"""

        hcl += f"""
output "{safe_res}_id" {{
  value = ibm_is_subnet.{safe_res}.id
}}
"""

        if enable_security_groups:
            hcl += f"""
output "{safe_res}_sg_id" {{
  value = ibm_is_security_group.sg_{safe_res}.id
}}
"""
    return hcl


def render_networking_variables():
    return """variable \"zone\" { type = string }
variable \"project\" { type = string }
"""


def render_networking_outputs(networks_data, enable_security_groups=True):
    outputs = ""
    for i, net in enumerate(networks_data):
        raw_name = net.get('name', 'unknown-net')
        vlan_id = net.get('vlan')
        safe_res = raw_name.lower().replace(" ", "_").replace("-", "_")
        if vlan_id and str(vlan_id).strip():
            safe_res += f"_vlan_{vlan_id}"

        outputs += f"""
output \"{safe_res}_id\" {{
  value = ibm_is_subnet.{safe_res}.id
}}
"""
        if enable_security_groups:
            outputs += f"""
output \"{safe_res}_sg_id\" {{
  value = ibm_is_security_group.sg_{safe_res}.id
}}
"""
    return outputs


def render_storage_variables():
    return """variable \"zone\" { type = string }
variable \"project\" { type = string }
"""


def render_storage_outputs():
    return """output \"volume_ids\" {
  value = [for v in ibm_is_volume : v.id]
}

output \"data_volume_ids\" {
  value = local.data_volume_ids
}
"""


def render_storage_templates(final_vms, project_name="my-ibm-migration"):
    content = """# Storage module for VSI volumes\n"""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        tier = vm.get('Override Storage Tier') or vm.get('Storage Tier', '3iops-tier')
        for idx, disk in enumerate(_vm_data_disks(vm)):
            disk_name = disk.get('disk') or f"disk_{idx + 1}"
            safe_disk = _safe_resource_name(disk_name)
            capacity = math.ceil(_clean_number(disk.get('capacity_gb'), 10))
            capacity = max(10, capacity)

            content += f"""
resource "ibm_is_volume" "{safe_n}_{safe_disk}_vol" {{
  name     = "{safe_n}-{safe_disk}-vol"
  profile  = "{tier}"
  zone     = var.zone
  capacity = {capacity}
  tags     = ["project:{project_name}", "vm:{safe_n}", "disk:{safe_disk}", "managed-by:rvtools-converter"]
}}
"""
    volume_map = []
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        ids = []
        for idx, disk in enumerate(_vm_data_disks(vm)):
            disk_name = disk.get('disk') or f"disk_{idx + 1}"
            safe_disk = _safe_resource_name(disk_name)
            ids.append(f"ibm_is_volume.{safe_n}_{safe_disk}_vol.id")
        values = ", ".join(ids)
        volume_map.append(f'    "{safe_n}" = [{values}]')

    content += "\nlocals {\n  data_volume_ids = {\n"
    content += "\n".join(volume_map)
    content += "\n  }\n}\n"
    return content


def render_vsi_variables():
    return """variable "zone" { type = string }
variable "project" { type = string }
variable "data_volume_ids" {
  type    = map(list(string))
  default = {}
}
"""


def render_vsi_templates(final_vms, enable_security_groups=True, project_name="my-ibm-migration"):
    content = """# VSI module for instance definitions\n"""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        prof = vm.get('Override Profile') or vm.get('IBM Profile', 'bx2-2x8')
        r_net = vm.get('Network', 'unknown-net')
        connected_nics = _connected_nics(vm)
        if connected_nics:
            primary_nic = connected_nics[0]
            secondary_nics = connected_nics[1:]
            t_sub_res = _safe_resource_name(
                primary_nic.get('network') or r_net
            )
        else:
            primary_nic = {}
            secondary_nics = []
            t_sub_res = _safe_resource_name(r_net)

        content += f"""
resource "ibm_is_instance" "{safe_n}" {{
  name    = "{safe_n}-vsi"
  profile = "{prof}"
  zone    = var.zone
  primary_network_interface {{
    name   = "eth0"
    subnet = module.networking.{t_sub_res}_id
"""
        if enable_security_groups:
            content += f"""
    security_groups = [module.networking.{t_sub_res}_sg_id]
"""
        content += f"""
  }}
"""
        for idx, nic in enumerate(secondary_nics, start=1):
            nic_net = _safe_resource_name(nic.get('network') or r_net)
            content += f"""
  network_interfaces {{
    name   = "eth{idx}"
    subnet = module.networking.{nic_net}_id
"""
            if enable_security_groups:
                content += f"""
    security_groups = [module.networking.{nic_net}_sg_id]
"""
            content += """
  }
"""
        content += f"""
  tags = ["project:{project_name}", "vm:{safe_n}", "managed-by:rvtools-converter"]
}}
"""
        for idx, disk in enumerate(_vm_data_disks(vm)):
            disk_name = disk.get('disk') or f"disk_{idx + 1}"
            safe_disk = _safe_resource_name(disk_name)
            content += f"""
resource "ibm_is_instance_volume_attachment" "{safe_n}_{safe_disk}_attach" {{
  instance = ibm_is_instance.{safe_n}.id
  volume   = var.data_volume_ids["{safe_n}"][{idx}]
  name     = "{safe_n}-{safe_disk}-attachment"
}}
"""
    return content


def render_vsi_outputs(final_vms):
    outputs = ""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        outputs += f"""
output "{safe_n}_id" {{
  value = ibm_is_instance.{safe_n}.id
}}
"""
    return outputs


def render_root_main(deployment_target="Plain CLI"):
    hcl = """terraform {
  required_providers {
    ibm = {
      source  = "IBM-Cloud/ibm"
      version = ">= 1.70.0"
    }
  }
"""
    if deployment_target == "Plain CLI":
        hcl += """
  backend "local" {
    path = "terraform.tfstate"
  }
"""
    else:
        hcl += """
  # IBM Schematics manages state for this deployment target.
"""
    hcl += """
}

provider "ibm" {
  region = var.region
}
"""
    hcl += """
module "networking" {
  source  = "./modules/networking"
  zone    = var.zone
  project = var.project
}

module "storage" {
  source  = "./modules/storage"
  zone    = var.zone
  project = var.project
}

module "vsi" {
  source          = "./modules/vsi"
  zone            = var.zone
  project         = var.project
  data_volume_ids = module.storage.data_volume_ids
  depends_on      = [module.storage, module.networking]
}
"""
    return hcl


def render_root_variables():
    return """variable "ibmcloud_api_key" { sensitive = true }
variable "region" { type = string }
variable "zone" { type = string }
variable "project" { type = string }
"""


def render_root_outputs():
    return """output "project" {
  value = var.project
}
output "region" {
  value = var.region
}
output "zone" {
  value = var.zone
}
"""


def render_terraform_templates(final_vms, unique_nets, region, zone, enable_security_groups=True, vpc_name="migration-vpc", custom_cidrs=None, address_prefix_strategy="manual", deployment_target="Plain CLI", project_name="my-ibm-migration"):
    """Renders the Root main.tf and module contents."""

    root_main = render_root_main(deployment_target)
    root_vars = render_root_variables()
    root_out = render_root_outputs()
    net_hcl = render_networking_templates(unique_nets, vpc_name=vpc_name, enable_security_groups=enable_security_groups, custom_cidrs=custom_cidrs, address_prefix_strategy=address_prefix_strategy, project_name=project_name)
    net_vars = render_networking_variables()
    net_out = render_networking_outputs(unique_nets, enable_security_groups=enable_security_groups)
    storage_main = render_storage_templates(final_vms, project_name=project_name)
    storage_vars = render_storage_variables()
    storage_out = render_storage_outputs()
    vsi_main = render_vsi_templates(final_vms, enable_security_groups=enable_security_groups, project_name=project_name)
    vsi_vars = render_vsi_variables()
    vsi_out = render_vsi_outputs(final_vms)

    return (
        vsi_main,
        root_main,
        storage_main,
        net_hcl,
        root_vars,
        root_out,
        net_vars,
        net_out,
        vsi_vars,
        vsi_out,
        storage_vars,
        storage_out
    )


def generate_variables_hcl():
    """Returns root variables definition."""
    return """variable "ibmcloud_api_key" { sensitive = true }
variable "region" { type = string }
variable "zone" { type = string }
variable "project" { type = string }
"""


def generate_tfvars(region, zone, project):
    """Outputs values chosen in Streamlit."""
    return f"""region  = "{region}"
zone    = "{zone}"
project = "{project}"
"""
