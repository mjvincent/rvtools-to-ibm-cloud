import re

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


def _vm_network_findings(vm):
    vm = _as_vm(vm)
    findings = vm.network_status.findings or vm.network_readiness_findings
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


