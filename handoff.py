import csv
import io
import json
import re

from assessments import IMAGE_MAX_GB, IMAGE_MIN_GB
from models import MigrationVm, clean_value


def _clean_value(value, default=""):
    """Return JSON/CSV friendly values from pandas and Streamlit records."""
    return clean_value(value, default)


def _clean_number(value, default=0):
    value = _clean_value(value, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_vm(value):
    if isinstance(value, MigrationVm):
        return value
    return MigrationVm.from_record(value)


def _as_record(value):
    if hasattr(value, "to_record"):
        return value.to_record()
    return value


def _normalize_vms(final_vms):
    return [_as_vm(vm) for vm in final_vms]


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
    vm = _as_vm(vm)
    disks = vm.source.disks or vm.disks
    disks = [_as_record(disk) for disk in disks]
    return disks if isinstance(disks, list) else []


def _disk_partitions(disk):
    partitions = disk.get('partitions', [])
    partitions = [_as_record(partition) for partition in partitions]
    return partitions if isinstance(partitions, list) else []


def _vm_unmatched_partitions(vm):
    vm = _as_vm(vm)
    partitions = vm.source.partitions or vm.partitions
    partitions = [_as_record(partition) for partition in partitions]
    return partitions if isinstance(partitions, list) else []


def _vm_partitions(vm):
    partitions = []
    for disk in _vm_disks(vm):
        for partition in _disk_partitions(disk):
            record = partition.copy()
            record.setdefault("source_disk", disk.get('disk'))
            record.setdefault("source_disk_key", disk.get('disk_key'))
            record["matched"] = True
            partitions.append(record)
    for partition in _vm_unmatched_partitions(vm):
        record = partition.copy()
        record.setdefault("source_disk", "")
        record.setdefault("source_disk_key", record.get('disk_key', ""))
        record["matched"] = False
        partitions.append(record)
    return partitions


def _vm_data_disks(vm):
    return [disk for disk in _vm_disks(vm) if not disk.get('is_boot')]


def _vm_nics(vm):
    vm = _as_vm(vm)
    nics = vm.source.nics or vm.nics
    nics = [_as_record(nic) for nic in nics]
    return nics if isinstance(nics, list) else []


def _vm_findings(vm):
    vm = _as_vm(vm)
    findings = vm.migration.findings or vm.readiness_findings
    findings = [_as_record(finding) for finding in findings]
    return findings if isinstance(findings, list) else []


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
            "partitions": _vm_partitions(vm),
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
            "pricing": {
                "source": _clean_value(vm.get('Pricing Source')),
                "confidence": _clean_value(vm.get('Pricing Confidence')),
                "last_updated": _clean_value(vm.get('Pricing Last Updated')),
                "profile_hourly": _clean_value(vm.get('Profile Hourly'), 0),
            },
            "memory_readiness": {
                "status": _clean_value(vm.get('Memory Readiness'), 'Review'),
                "reasons": _clean_value(vm.get('Memory Readiness Reasons')),
                "configured_mib": _clean_value(
                    vm.get('Configured Memory MiB'), 0
                ),
                "active_mib": _clean_value(vm.get('Active Memory MiB'), 0),
                "consumed_mib": _clean_value(
                    vm.get('Consumed Memory MiB'), 0
                ),
                "ballooned_mib": _clean_value(
                    vm.get('Ballooned Memory MiB'), 0
                ),
                "swapped_mib": _clean_value(vm.get('Swapped Memory MiB'), 0),
                "reservation_mib": _clean_value(
                    vm.get('Memory Reservation MiB'), 0
                ),
                "limit_mib": _clean_value(vm.get('Memory Limit MiB'), 0),
                "hot_add": _clean_value(vm.get('Memory Hot Add')),
                "sizing_memory_mib": _clean_value(
                    vm.get('Sizing Memory MiB'), 0
                ),
                "sizing_basis": _clean_value(vm.get('Memory Sizing Basis')),
            },
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
        "migration_readiness": {
            "status": _clean_value(vm.get('Migration Readiness'), 'Review'),
            "reasons": _clean_value(vm.get('Migration Readiness Reasons')),
            "snapshot_count": _clean_value(vm.get('Snapshot Count'), 0),
            "snapshot_size_mib": _clean_value(
                vm.get('Snapshot Size MiB'), 0
            ),
            "vmware_tools_status": _clean_value(
                vm.get('VMware Tools Status')
            ),
            "mounted_media": _clean_value(vm.get('Mounted Media')),
            "usb_devices": _clean_value(vm.get('USB Devices'), 0),
            "health_warnings": _clean_value(vm.get('Health Warnings'), 0),
            "findings": _vm_findings(vm),
        },
    }


def generate_migration_manifest(final_vms, context):
    """Create the tool-neutral migration handoff manifest."""
    final_vms = _normalize_vms(final_vms)
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
            "pricing": {
                "mode": _clean_value(context.get('pricing_mode')),
                "source": _clean_value(context.get('pricing_source')),
                "confidence": _clean_value(context.get('pricing_confidence')),
                "last_updated": _clean_value(
                    context.get('pricing_last_updated')
                ),
            },
        },
        "handoff_files": {
            "vm_mapping_csv": "vm-mapping.csv",
            "disk_mapping_csv": "disk-mapping.csv",
            "nic_mapping_csv": "nic-mapping.csv",
            "partition_mapping_csv": "partition-mapping.csv",
            "memory_readiness_csv": "memory-readiness.csv",
            "readiness_findings_csv": "readiness-findings.csv",
            "assessment_quality_json": "assessment-quality.json",
            "assessment_quality_csv": "assessment-quality.csv",
            "runbook": "migration-runbook.md",
            "image_import_tfvars_example": "image-import-variables.tfvars.example",
        },
        "assessment_quality": context.get("assessment_quality", {}),
        "virtual_machines": [
            _migration_vm_record(vm) for vm in final_vms
        ],
    }
    return json.dumps(manifest, indent=2, sort_keys=True)


def generate_vm_mapping_csv(final_vms):
    """Create a migration-team friendly source-to-target mapping CSV."""
    final_vms = _normalize_vms(final_vms)
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Power State", "Guest OS", "Source IP", "Source Network",
        "Datacenter", "Cluster", "Host", "Disk Count", "Total Storage GB",
        "Firmware", "Boot Disk GB", "Guest Customization",
        "Image Readiness", "Readiness Reasons",
        "Migration Readiness", "Migration Readiness Reasons",
        "Snapshot Count", "Snapshot Size MiB", "VMware Tools Status",
        "Mounted Media", "USB Devices", "Health Warnings",
        "Memory Readiness", "Memory Readiness Reasons",
        "Configured Memory MiB", "Active Memory MiB",
        "Consumed Memory MiB", "Ballooned Memory MiB",
        "Swapped Memory MiB", "Memory Reservation MiB", "Memory Limit MiB",
        "Memory Hot Add", "Sizing Memory MiB", "Memory Sizing Basis",
        "Pricing Source", "Pricing Confidence", "Pricing Last Updated",
        "Profile Hourly",
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
            "Migration Readiness": _clean_value(
                vm.get('Migration Readiness')
            ),
            "Migration Readiness Reasons": _clean_value(
                vm.get('Migration Readiness Reasons')
            ),
            "Snapshot Count": _clean_value(vm.get('Snapshot Count'), 0),
            "Snapshot Size MiB": _clean_value(
                vm.get('Snapshot Size MiB'), 0
            ),
            "VMware Tools Status": _clean_value(
                vm.get('VMware Tools Status')
            ),
            "Mounted Media": _clean_value(vm.get('Mounted Media')),
            "USB Devices": _clean_value(vm.get('USB Devices'), 0),
            "Health Warnings": _clean_value(vm.get('Health Warnings'), 0),
            "Memory Readiness": _clean_value(vm.get('Memory Readiness')),
            "Memory Readiness Reasons": _clean_value(
                vm.get('Memory Readiness Reasons')
            ),
            "Configured Memory MiB": _clean_value(
                vm.get('Configured Memory MiB'), 0
            ),
            "Active Memory MiB": _clean_value(
                vm.get('Active Memory MiB'), 0
            ),
            "Consumed Memory MiB": _clean_value(
                vm.get('Consumed Memory MiB'), 0
            ),
            "Ballooned Memory MiB": _clean_value(
                vm.get('Ballooned Memory MiB'), 0
            ),
            "Swapped Memory MiB": _clean_value(
                vm.get('Swapped Memory MiB'), 0
            ),
            "Memory Reservation MiB": _clean_value(
                vm.get('Memory Reservation MiB'), 0
            ),
            "Memory Limit MiB": _clean_value(
                vm.get('Memory Limit MiB'), 0
            ),
            "Memory Hot Add": _clean_value(vm.get('Memory Hot Add')),
            "Sizing Memory MiB": _clean_value(
                vm.get('Sizing Memory MiB'), 0
            ),
            "Memory Sizing Basis": _clean_value(
                vm.get('Memory Sizing Basis')
            ),
            "Pricing Source": _clean_value(vm.get('Pricing Source')),
            "Pricing Confidence": _clean_value(vm.get('Pricing Confidence')),
            "Pricing Last Updated": _clean_value(
                vm.get('Pricing Last Updated')
            ),
            "Profile Hourly": _clean_value(vm.get('Profile Hourly'), 0),
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


def generate_readiness_findings_csv(final_vms):
    """Create a row-per-finding migration readiness CSV."""
    final_vms = _normalize_vms(final_vms)
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Migration Readiness", "Severity", "Finding Type",
        "Source Tab", "Evidence", "Recommended Action"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        findings = _vm_findings(vm)
        if not findings:
            writer.writerow({
                "VM Name": vm_name,
                "Migration Readiness": _clean_value(
                    vm.get('Migration Readiness'), 'Ready'
                ),
                "Severity": "Ready",
                "Finding Type": "No findings",
                "Source Tab": "",
                "Evidence": "No migration readiness blockers found",
                "Recommended Action": "Proceed with migration planning",
            })
            continue

        for finding in findings:
            writer.writerow({
                "VM Name": vm_name,
                "Migration Readiness": _clean_value(
                    vm.get('Migration Readiness'), 'Review'
                ),
                "Severity": _clean_value(finding.get('severity'), 'Review'),
                "Finding Type": _clean_value(finding.get('finding_type')),
                "Source Tab": _clean_value(finding.get('source_tab')),
                "Evidence": _clean_value(finding.get('evidence')),
                "Recommended Action": _clean_value(
                    finding.get('recommended_action')
                ),
            })
    return output.getvalue()


def generate_memory_readiness_csv(final_vms):
    """Create a VM-level memory readiness and sizing CSV."""
    final_vms = _normalize_vms(final_vms)
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Memory Readiness", "Memory Readiness Reasons",
        "Configured Memory MiB", "Active Memory MiB", "Consumed Memory MiB",
        "Ballooned Memory MiB", "Swapped Memory MiB",
        "Memory Reservation MiB", "Memory Limit MiB", "Memory Hot Add",
        "Sizing Memory MiB", "Memory Sizing Basis", "Recommended Profile",
        "Override Profile", "Effective Profile"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        writer.writerow({
            "VM Name": _safe_vm_key(vm.get('VM Name')),
            "Memory Readiness": _clean_value(vm.get('Memory Readiness')),
            "Memory Readiness Reasons": _clean_value(
                vm.get('Memory Readiness Reasons')
            ),
            "Configured Memory MiB": _clean_value(
                vm.get('Configured Memory MiB'), 0
            ),
            "Active Memory MiB": _clean_value(
                vm.get('Active Memory MiB'), 0
            ),
            "Consumed Memory MiB": _clean_value(
                vm.get('Consumed Memory MiB'), 0
            ),
            "Ballooned Memory MiB": _clean_value(
                vm.get('Ballooned Memory MiB'), 0
            ),
            "Swapped Memory MiB": _clean_value(
                vm.get('Swapped Memory MiB'), 0
            ),
            "Memory Reservation MiB": _clean_value(
                vm.get('Memory Reservation MiB'), 0
            ),
            "Memory Limit MiB": _clean_value(
                vm.get('Memory Limit MiB'), 0
            ),
            "Memory Hot Add": _clean_value(vm.get('Memory Hot Add')),
            "Sizing Memory MiB": _clean_value(
                vm.get('Sizing Memory MiB'), 0
            ),
            "Memory Sizing Basis": _clean_value(
                vm.get('Memory Sizing Basis')
            ),
            "Recommended Profile": _clean_value(vm.get('IBM Profile')),
            "Override Profile": _clean_value(vm.get('Override Profile')),
            "Effective Profile": _effective_profile(vm),
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
    final_vms = _normalize_vms(final_vms)
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
    final_vms = _normalize_vms(final_vms)
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Disk", "Role", "Capacity GB", "Target Action",
        "Storage Tier", "Terraform Volume", "Attachment Resource",
        "Partition Count", "Partition Labels", "Partition Capacity MiB",
        "Partition Consumed MiB", "Partition Free MiB", "Partition Free %",
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
            partitions = _disk_partitions(disk)
            partition_capacity = sum(
                _clean_number(partition.get('capacity_mib'), 0)
                for partition in partitions
            )
            partition_consumed = sum(
                _clean_number(partition.get('consumed_mib'), 0)
                for partition in partitions
            )
            partition_free = sum(
                _clean_number(partition.get('free_mib'), 0)
                for partition in partitions
            )
            partition_free_pct = ""
            if partition_capacity:
                partition_free_pct = round(
                    (partition_free / partition_capacity) * 100,
                    2
                )
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
                "Partition Count": len(partitions),
                "Partition Labels": ", ".join([
                    _clean_value(partition.get('disk'))
                    for partition in partitions
                    if _clean_value(partition.get('disk'))
                ]),
                "Partition Capacity MiB": partition_capacity,
                "Partition Consumed MiB": partition_consumed,
                "Partition Free MiB": partition_free,
                "Partition Free %": partition_free_pct,
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


def generate_partition_mapping_csv(final_vms):
    """Create a row-per-partition storage planning CSV."""
    final_vms = _normalize_vms(final_vms)
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Disk", "Disk Key", "Matched To Disk", "Partition",
        "Capacity MiB", "Consumed MiB", "Free MiB", "Free %"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        for partition in _vm_partitions(vm):
            writer.writerow({
                "VM Name": vm_name,
                "Disk": _clean_value(partition.get('source_disk')),
                "Disk Key": _clean_value(
                    partition.get('source_disk_key') or partition.get('disk_key')
                ),
                "Matched To Disk": bool(partition.get('matched')),
                "Partition": _clean_value(partition.get('disk')),
                "Capacity MiB": _clean_value(partition.get('capacity_mib'), 0),
                "Consumed MiB": _clean_value(partition.get('consumed_mib'), 0),
                "Free MiB": _clean_value(partition.get('free_mib'), 0),
                "Free %": _clean_value(partition.get('free_pct'), 0),
            })
    return output.getvalue()


def generate_image_import_tfvars(final_vms):
    """Create an example tfvars map for imported IBM Cloud custom images."""
    final_vms = _normalize_vms(final_vms)
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
- `memory-readiness.csv`: Memory pressure, reservation, limit, and sizing review.
- `readiness-findings.csv`: Row-level migration readiness findings and remediation actions.
- `image-import-variables.tfvars.example`: Placeholder map for imported custom image IDs.
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
13. Copy `image-import-variables.tfvars.example`, replace placeholders with real image IDs, and decide whether to wire those IDs into the VSI module.
14. Apply the generated Terraform using the selected deployment target.
15. Validate VSI boot, network placement, security group membership, disk attachment, monitoring, backup, and application health.
16. Execute DNS, IP, load balancer, or application cutover steps according to the migration wave plan.

## Notes
Terraform builds the target VPC foundation and VSI definitions. It does not move VMDK files or perform application cutover by itself. Use the manifest and CSV as the handoff layer for RackWare, custom scripts, IBM Cloud image import, or a migration factory workflow.
"""
