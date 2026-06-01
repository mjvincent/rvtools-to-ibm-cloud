import csv
import io

from models import as_bool

from .utils import (
    _clean_number,
    _clean_value,
    _disk_partitions,
    _effective_profile,
    _effective_storage_tier,
    _normalize_vms,
    _safe_resource_name,
    _safe_vm_key,
    _vm_disks,
    _vm_findings,
    _vm_nics,
    _vm_partitions,
)


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
        "Network Readiness", "Network Readiness Reasons",
        "Configured Memory MiB", "Active Memory MiB",
        "Consumed Memory MiB", "Ballooned Memory MiB",
        "Swapped Memory MiB", "Memory Reservation MiB", "Memory Limit MiB",
        "Memory Hot Add", "Sizing Memory MiB", "Memory Sizing Basis",
        "Pricing Source", "Pricing Confidence", "Pricing Last Updated", "Pricing Status",
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
            "Network Readiness": _clean_value(vm.get('Network Readiness')),
            "Network Readiness Reasons": _clean_value(
                vm.get('Network Readiness Reasons')
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
            "Pricing Status": _clean_value(vm.get('Pricing Status')),
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
        "MAC Address", "Adapter", "Switch", "Switch Type", "Port Group",
        "VLAN / Segment", "Port Key", "Port Status", "Backing Source Tab",
        "Match Confidence", "Network Readiness", "Type", "Target Subnet",
        "Target Security Group"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        connected_seen = 0
        for nic in _vm_nics(vm):
            connected = as_bool(nic.get('connected', True), True)
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
                "Switch Type": _clean_value(nic.get('switch_type')),
                "Port Group": _clean_value(nic.get('port_group')),
                "VLAN / Segment": _clean_value(nic.get('vlan')),
                "Port Key": _clean_value(nic.get('port_key')),
                "Port Status": _clean_value(nic.get('port_status')),
                "Backing Source Tab": _clean_value(
                    nic.get('backing_source_tab')
                ),
                "Match Confidence": _clean_value(nic.get('match_confidence')),
                "Network Readiness": _clean_value(
                    vm.get('Network Readiness'), 'Review'
                ),
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


