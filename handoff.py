import csv
import io
import json
import re

from assessments import IMAGE_MAX_GB, IMAGE_MIN_GB
from models import MigrationVm, as_bool, clean_value


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


def _migration_vm_record(vm, image_import_status=None):
    vm_name = _safe_vm_key(vm.get('VM Name'))
    effective_profile = _effective_profile(vm)
    effective_storage_tier = _effective_storage_tier(vm)
    data_status = _clean_value(vm.get('Data Status'), 'Unknown')
    
    # Derive source image from original specs or VM name
    source_image = _clean_value(vm.get('Original Specs')) or vm_name
    
    # Resolve image import status from mapping
    image_import_status = image_import_status or {}
    image_status_entry = image_import_status.get(source_image, {})
    target_catalog_id = image_status_entry.get('target_catalog_id', '')
    import_status = image_status_entry.get('import_status', '')

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
            "image": source_image,
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
            "source_image": source_image,
            "target_catalog_id": target_catalog_id,
            "image_import_status": import_status,
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
            "wave": _clean_value(vm.get('wave'), 'wave-01'),
            "cutover_group": _clean_value(vm.get('cutover_group'), 'unassigned'),
            "owner": _clean_value(vm.get('owner')),
            "application": _clean_value(vm.get('application')),
            "priority": _clean_value(vm.get('priority'), 'medium'),
            "dependency_group": _clean_value(vm.get('dependency_group')),
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
                "status": _clean_value(vm.get('Pricing Status')),
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
        "network_readiness": {
            "status": _clean_value(vm.get('Network Readiness'), 'Review'),
            "reasons": _clean_value(vm.get('Network Readiness Reasons')),
            "findings": _vm_network_findings(vm),
        },
        "wave_metadata": {
            "wave": _clean_value(vm.get('wave'), 'wave-01'),
            "cutover_group": _clean_value(vm.get('cutover_group'), 'unassigned'),
            "owner": _clean_value(vm.get('owner')),
            "application": _clean_value(vm.get('application')),
            "priority": _clean_value(vm.get('priority'), 'medium'),
            "dependency_group": _clean_value(vm.get('dependency_group')),
        },
    }


def _calculate_decision_audit_summary(final_vms, pricing_catalog=None):
    """Calculate decision audit summary with pricing impact from overrides.
    
    Summarizes profile, storage, and exclusion decisions with their pricing impact.
    """
    total_pricing_impact = 0.0
    profile_override_count = 0
    storage_override_count = 0
    
    for vm in final_vms:
        # Count profile overrides
        if _clean_value(vm.get('Override Profile')):
            profile_override_count += 1
        
        # Count storage tier overrides
        if _clean_value(vm.get('Override Storage Tier')):
            storage_override_count += 1
        
        # Calculate pricing impact (difference between baseline and estimated)
        baseline = _clean_number(vm.get('Baseline Cost (Mo)'), 0)
        estimated = _clean_number(vm.get('Monthly Cost'), 0)
        if baseline > 0:
            total_pricing_impact += (estimated - baseline)
    
    return {
        "total_pricing_impact": round(total_pricing_impact, 2),
        "profile_override_count": profile_override_count,
        "storage_override_count": storage_override_count,
    }


def _calculate_remediation_tracker_summary(remediation_tracker=None):
    """Calculate remediation tracker summary with blocker counts by status.
    
    Summarizes blocker status distribution and overdue items.
    """
    if not remediation_tracker:
        return {
            "blocker_counts_by_status": {},
            "total_blockers": 0,
            "overdue_count": 0,
        }
    
    blocker_counts_by_status = {}
    total_blockers = 0
    overdue_count = 0
    
    from datetime import datetime
    today = datetime.now().date()
    
    for blocker_id, blocker_info in remediation_tracker.items():
        status = _clean_value(blocker_info.get('status'), 'open')
        blocker_counts_by_status[status] = blocker_counts_by_status.get(status, 0) + 1
        total_blockers += 1
        
        # Check if overdue
        due_date_str = _clean_value(blocker_info.get('due_date'))
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if due_date < today and status != 'closed':
                    overdue_count += 1
            except (ValueError, TypeError):
                pass
    
    return {
        "blocker_counts_by_status": blocker_counts_by_status,
        "total_blockers": total_blockers,
        "overdue_count": overdue_count,
    }


def _calculate_image_import_summary(final_vms, image_import_status=None):
    """Calculate image import summary with import status breakdown.
    
    Summarizes image readiness and import status distribution.
    """
    image_import_status = image_import_status or {}
    total_images = 0
    total_vms_pending_import = 0
    import_status_breakdown = {}
    
    seen_images = set()
    
    for vm in final_vms:
        # Get source image
        source_image = _clean_value(vm.get('Original Specs')) or _safe_vm_key(vm.get('VM Name'))
        
        # Count unique images
        if source_image not in seen_images:
            seen_images.add(source_image)
            total_images += 1
        
        # Get import status
        image_status_entry = image_import_status.get(source_image, {})
        status = image_status_entry.get('import_status', 'pending')
        
        if status == 'pending':
            total_vms_pending_import += 1
        
        # Count by status
        import_status_breakdown[status] = import_status_breakdown.get(status, 0) + 1
    
    return {
        "total_images": total_images,
        "total_vms_pending_import": total_vms_pending_import,
        "import_status_breakdown": import_status_breakdown,
    }


def generate_migration_manifest(final_vms, context, image_import_status=None, pricing_catalog=None, remediation_tracker=None):
    """Create the tool-neutral migration handoff manifest with wave metadata and audit information.
    
    This manifest serves as the primary handoff document containing VM mappings, assessment
    results, and decision audit information for the migration team.
    
    Args:
        final_vms: List of VM records or MigrationVm objects to be migrated
        context: Dict with project, pricing, and configuration metadata
                 Keys: project_name, target_region, target_zone, vpc_name, 
                       address_prefix_strategy, deployment_target, generate_security_groups,
                       pricing_mode, pricing_source, pricing_confidence, pricing_status,
                       pricing_last_updated, assessment_quality
        image_import_status: Optional dict mapping source image names to import status
                            with keys: target_catalog_id, import_status, etc.
        pricing_catalog: Optional pricing catalog dict for calculating pricing impact
                        Used to compute total pricing delta for decision audit summary
        remediation_tracker: Optional dict mapping blocker_id to blocker_info dicts
                            with keys: status, due_date, notes, owner, blocker_type, etc.
                            Used to populate remediation tracker summary with status counts
    
    Returns:
        JSON string containing the migration manifest
        
    Manifest schema v1.0 includes:
        - project: deployment metadata, pricing configuration
        - virtual_machines[]: VM mappings with per-VM metadata including:
            * wave: migration wave identifier (e.g., "wave-01")
            * cutover_group: grouped cutover coordination identifier
            * owner: migration workload owner
            * application: application or service name
            * priority: migration priority (high/medium/low)
            * dependency_group: dependency coordination identifier
            * source_image: source VM image name for image import
            * target_catalog_id: target IBM Cloud image catalog ID
            * import_status: image import status (pending/importing/completed/failed)
        - decision_audit_summary:
            * total_pricing_impact: total monthly cost delta from baseline
            * profile_override_count: count of VMs with profile overrides
            * storage_override_count: count of VMs with storage tier overrides
        - remediation_tracker_summary:
            * blocker_counts_by_status: count of blockers by status
            * total_blockers: total blocker count
            * overdue_count: count of overdue blockers
        - image_import_summary:
            * total_images: count of unique source images
            * total_vms_pending_import: count of VMs pending image import
            * import_status_breakdown: count of images by import status
        - handoff_files: references to supporting CSV/JSON/markdown files
    """
    final_vms = _normalize_vms(final_vms)
    image_import_status = image_import_status or {}
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
                "status": _clean_value(context.get('pricing_status')),
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
            "preflight_report_json": "preflight-report.json",
            "preflight_report_csv": "preflight-report.csv",
            "pricing_diagnostics_json": "pricing-diagnostics.json",
            "pricing_diagnostics_csv": "pricing-diagnostics.csv",
            "runbook": "migration-runbook.md",
            "image_import_tfvars_example": "image-import-variables.tfvars.example",
        },
        "assessment_quality": context.get("assessment_quality", {}),
        "virtual_machines": [
            _migration_vm_record(vm, image_import_status) for vm in final_vms
        ],
    }
    
    # Calculate decision audit summary
    manifest["decision_audit_summary"] = _calculate_decision_audit_summary(
        final_vms, pricing_catalog
    )
    
    # Calculate remediation tracker summary
    manifest["remediation_tracker_summary"] = _calculate_remediation_tracker_summary(
        remediation_tracker
    )
    
    # Calculate image import summary
    manifest["image_import_summary"] = _calculate_image_import_summary(
        final_vms, image_import_status
    )
    
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


def _catalog_deployment(catalog):
    metadata = catalog.get("metadata", {}) if catalog else {}
    metrics = catalog.get("catalog_metrics", []) if catalog else []
    first_metric = metrics[0] if metrics else {}
    return {
        "deployment_id": _clean_value(
            metadata.get("deployment_id") or first_metric.get("deployment_id")
        ),
        "deployment_location": _clean_value(
            metadata.get("deployment_location")
            or first_metric.get("deployment_location")
        ),
        "deployment_region": _clean_value(
            metadata.get("deployment_region") or first_metric.get("deployment_region")
            or metadata.get("region")
        ),
    }


def generate_pricing_diagnostics_json(catalog, final_vms):
    """Create an auditable pricing diagnostics export for the package."""
    final_vms = _normalize_vms(final_vms)
    catalog = catalog or {}
    metadata = catalog.get("metadata", {})
    diagnostics = {
        "schema_version": "1.0",
        "metadata": {
            "mode": _clean_value(metadata.get("mode")),
            "source": _clean_value(metadata.get("source")),
            "confidence": _clean_value(metadata.get("confidence")),
            "pricing_status": _clean_value(metadata.get("pricing_status")),
            "region": _clean_value(metadata.get("region")),
            "country": _clean_value(metadata.get("country")),
            "currency": _clean_value(metadata.get("currency")),
            "last_updated": _clean_value(metadata.get("last_updated")),
            **_catalog_deployment(catalog),
        },
        "billing_dimension_rates": catalog.get("billing_dimension_rates", {}),
        "unmapped_catalog_metrics": catalog.get("unmapped_catalog_metrics", []),
        "vm_pricing": [
            {
                "vm_name": _safe_vm_key(vm.get("VM Name")),
                "effective_profile": _effective_profile(vm),
                "effective_storage_tier": _effective_storage_tier(vm),
                "pricing_source": _clean_value(vm.get("Pricing Source")),
                "pricing_confidence": _clean_value(vm.get("Pricing Confidence")),
                "pricing_status": _clean_value(vm.get("Pricing Status")),
                "profile_hourly": _clean_value(vm.get("Profile Hourly"), 0),
                "compute_monthly": _clean_value(vm.get("Compute (Mo)"), 0),
                "storage_monthly": _clean_value(vm.get("Storage (Mo)"), 0),
                "estimated_monthly_cost": _clean_value(vm.get("Monthly Cost"), 0),
            }
            for vm in final_vms
        ],
    }
    return json.dumps(diagnostics, indent=2, sort_keys=True)


def decision_audit_export(vms: list[MigrationVm], pricing_catalog) -> str:
    """Generate a CSV capturing profile/storage/network/exclusion decisions and pricing impact.

    Columns:
    VM Key, VM Name, Owner, Application, Wave,
    Original Profile, Chosen Profile, Profile Override Reason,
    Original Storage Tier, Chosen Storage Tier, Storage Tier Override Reason,
    Network Mode, Include/Exclude, Exclusion Reason,
    vCPU Cost Delta, Storage Cost Delta, Total Pricing Impact
    """
    final_vms = _normalize_vms(vms)
    catalog = pricing_catalog or {}
    output = io.StringIO()
    fieldnames = [
        "VM Key", "VM Name", "Owner", "Application", "Wave",
        "Original Profile", "Chosen Profile", "Profile Override Reason",
        "Original Storage Tier", "Chosen Storage Tier", "Storage Tier Override Reason",
        "Network Mode", "Include/Exclude", "Exclusion Reason",
        "vCPU Cost Delta", "Storage Cost Delta", "Total Pricing Impact",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    def profile_monthly_for(profile):
        if not profile:
            return 0.0
        # try structured catalog: catalog['profiles'][profile]['hourly'] or ['monthly']
        profiles = catalog.get('profiles', {}) if isinstance(catalog, dict) else {}
        prof = profiles.get(profile, {}) if isinstance(profiles, dict) else {}
        hourly = None
        if isinstance(prof, dict):
            hourly = prof.get('hourly') or prof.get('profile_hourly')
        if hourly is None:
            try:
                hourly = catalog.get('profile_hourly', {}).get(profile)
            except Exception:
                hourly = None
        if hourly:
            try:
                return float(hourly) * 24 * 30
            except Exception:
                pass
        monthly = None
        if isinstance(prof, dict):
            monthly = prof.get('monthly') or prof.get('monthly_cost')
        if monthly:
            try:
                return float(monthly)
            except Exception:
                pass
        return 0.0

    def storage_monthly_for(tier, gb):
        if not tier or not gb:
            return 0.0
        tiers = catalog.get('storage_tiers', {}) if isinstance(catalog, dict) else {}
        t = tiers.get(tier, {}) if isinstance(tiers, dict) else {}
        per_gb = None
        if isinstance(t, dict):
            per_gb = t.get('monthly_per_gb') or t.get('per_gb_monthly') or t.get('rate_per_gb')
        if per_gb is None:
            try:
                per_gb = catalog.get('storage_rate_per_gb', {}).get(tier)
            except Exception:
                per_gb = None
        if per_gb:
            try:
                return float(per_gb) * float(gb)
            except Exception:
                pass
        return 0.0

    total_impact = 0.0
    for vm in final_vms:
        vm_key = _clean_value(vm.get('VM Key')) or _clean_value(vm.get('vm_key'))
        vm_name = _safe_vm_key(vm.get('VM Name'))
        owner = _clean_value(vm.get('owner'))
        application = _clean_value(vm.get('application'))
        wave = _clean_value(vm.get('wave'))
        original_profile = _clean_value(vm.get('IBM Profile'))
        chosen_profile = _effective_profile(vm)
        profile_reason = _clean_value(vm.get('Override Profile Reason')) or _clean_value(vm.get('override_profile_reason'))
        original_storage = _clean_value(vm.get('Storage Tier'))
        chosen_storage = _effective_storage_tier(vm)
        storage_reason = _clean_value(vm.get('Override Storage Tier Reason')) or _clean_value(vm.get('override_storage_tier_reason'))
        network_mode = _clean_value(vm.get('Network')) or _clean_value(vm.get('network'))
        include_exclude = "Exclude" if as_bool(vm.get('Exclude?')) or as_bool(vm.get('exclude')) else "Include"
        exclusion_reason = _clean_value(vm.get('Exclusion Reason')) or _clean_value(vm.get('exclusion_reason'))

        total_gb = _clean_number(vm.get('Total Storage GB'), 0)

        orig_profile_monthly = profile_monthly_for(original_profile)
        chosen_profile_monthly = profile_monthly_for(chosen_profile)
        vcpu_delta = round(chosen_profile_monthly - orig_profile_monthly, 2)

        orig_storage_monthly = storage_monthly_for(original_storage, total_gb)
        chosen_storage_monthly = storage_monthly_for(chosen_storage, total_gb)
        storage_delta = round(chosen_storage_monthly - orig_storage_monthly, 2)

        total = round(vcpu_delta + storage_delta, 2)
        total_impact += total

        writer.writerow({
            "VM Key": vm_key,
            "VM Name": vm_name,
            "Owner": owner,
            "Application": application,
            "Wave": wave,
            "Original Profile": original_profile,
            "Chosen Profile": chosen_profile,
            "Profile Override Reason": profile_reason,
            "Original Storage Tier": original_storage,
            "Chosen Storage Tier": chosen_storage,
            "Storage Tier Override Reason": storage_reason,
            "Network Mode": network_mode,
            "Include/Exclude": include_exclude,
            "Exclusion Reason": exclusion_reason,
            "vCPU Cost Delta": vcpu_delta,
            "Storage Cost Delta": storage_delta,
            "Total Pricing Impact": total,
        })

    # summary row
    writer.writerow({
        "VM Key": "",
        "VM Name": "TOTAL",
        "Owner": "",
        "Application": "",
        "Wave": "",
        "Original Profile": "",
        "Chosen Profile": "",
        "Profile Override Reason": "",
        "Original Storage Tier": "",
        "Chosen Storage Tier": "",
        "Storage Tier Override Reason": "",
        "Network Mode": "",
        "Include/Exclude": "",
        "Exclusion Reason": "",
        "vCPU Cost Delta": "",
        "Storage Cost Delta": "",
        "Total Pricing Impact": round(total_impact, 2),
    })

    return output.getvalue()



def generate_pricing_diagnostics_csv(catalog, final_vms):
    """Create a VM-level CSV view of pricing source and fallback behavior."""
    final_vms = _normalize_vms(final_vms)
    catalog = catalog or {}
    metadata = catalog.get("metadata", {})
    deployment = _catalog_deployment(catalog)
    output = io.StringIO()
    fieldnames = [
        "VM Name", "Effective Profile", "Effective Storage Tier",
        "Pricing Source", "Pricing Confidence", "Pricing Status",
        "Profile Hourly", "Compute Monthly", "Storage Monthly",
        "Estimated Monthly Cost", "Catalog Mode", "Catalog Region",
        "Catalog Country", "Catalog Currency", "Catalog Last Updated",
        "Power VS Deployment ID", "Power VS Deployment Location",
        "Power VS Deployment Region", "Mapped Billing Dimensions",
        "Unmapped Catalog Metrics"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    mapped_dimensions = "; ".join(
        f"{key}={value}"
        for key, value in sorted(catalog.get("billing_dimension_rates", {}).items())
    )
    unmapped = "; ".join(
        f"{item.get('dimension')}: {item.get('reason')}"
        for item in catalog.get("unmapped_catalog_metrics", [])
    )
    for vm in final_vms:
        writer.writerow({
            "VM Name": _safe_vm_key(vm.get("VM Name")),
            "Effective Profile": _effective_profile(vm),
            "Effective Storage Tier": _effective_storage_tier(vm),
            "Pricing Source": _clean_value(vm.get("Pricing Source")),
            "Pricing Confidence": _clean_value(vm.get("Pricing Confidence")),
            "Pricing Status": _clean_value(vm.get("Pricing Status")),
            "Profile Hourly": _clean_value(vm.get("Profile Hourly"), 0),
            "Compute Monthly": _clean_value(vm.get("Compute (Mo)"), 0),
            "Storage Monthly": _clean_value(vm.get("Storage (Mo)"), 0),
            "Estimated Monthly Cost": _clean_value(vm.get("Monthly Cost"), 0),
            "Catalog Mode": _clean_value(metadata.get("mode")),
            "Catalog Region": _clean_value(metadata.get("region")),
            "Catalog Country": _clean_value(metadata.get("country")),
            "Catalog Currency": _clean_value(metadata.get("currency")),
            "Catalog Last Updated": _clean_value(metadata.get("last_updated")),
            "Power VS Deployment ID": deployment["deployment_id"],
            "Power VS Deployment Location": deployment["deployment_location"],
            "Power VS Deployment Region": deployment["deployment_region"],
            "Mapped Billing Dimensions": mapped_dimensions,
            "Unmapped Catalog Metrics": unmapped,
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


def generate_image_import_tfvars(final_vms):
    """Create an example tfvars map for imported IBM Cloud custom images."""
    final_vms = _normalize_vms(final_vms)
    lines = [
        "# Populate these values after VMware images are converted, uploaded,",
        "# and imported as IBM Cloud VPC custom images.",
        "# Copy this file, replace every placeholder, and pass it to Terraform",
        "# with -var-file when provisioning VSIs from the imported images.",
        "custom_image_ids = {",
    ]
    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        lines.append(f'  "{vm_name}" = "replace-with-imported-image-id"')
    lines.append("}")
    return "\n".join(lines) + "\n"


def image_import_export(vms: list[MigrationVm], image_import_status: dict = None) -> str:
    """Generate a CSV to plan image imports grouped by source image.

    Columns:
    Source Image, Count of VMs, Owners, Target Catalog ID,
    Import Status, Estimated Import Time, Notes

    image_import_status may be a mapping keyed by source image or VM key.
    """
    final_vms = _normalize_vms(vms)
    image_import_status = image_import_status or {}

    # Group VMs by inferred source image (fallback to VM name when missing)
    groups = {}
    total_vms = 0
    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        source_image = _clean_value(vm.get('Original Specs')) or vm_name
        entry = groups.setdefault(source_image, {"vms": [], "owners": set()})
        entry["vms"].append(vm)
        owner = _clean_value(vm.get('owner')) or _clean_value(vm.get('Owner'))
        if owner:
            entry["owners"].add(owner)

    output = io.StringIO()
    fieldnames = [
        "Source Image", "Count of VMs", "Owners",
        "Target Catalog ID", "Import Status", "Estimated Import Time", "Notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for source in sorted(groups.keys()):
        entry = groups[source]
        count = len(entry["vms"])
        total_vms += count
        owners = "; ".join(sorted(entry["owners"])) if entry["owners"] else ""

        # Resolve status info from image_import_status mapping.
        target_catalog_id = ""
        import_status = ""
        estimated_time = ""
        notes = ""

        if isinstance(image_import_status, dict):
            val = image_import_status.get(source)
            if val is None:
                # try per-VM keys
                for vm in entry["vms"]:
                    vm_key = _safe_vm_key(vm.get('VM Name'))
                    if vm_key in image_import_status:
                        val = image_import_status.get(vm_key)
                        break
            if isinstance(val, dict):
                target_catalog_id = _clean_value(val.get('target_catalog_id'))
                import_status = _clean_value(val.get('import_status')) or _clean_value(val.get('status'))
                estimated_time = _clean_value(val.get('estimated_import_time')) or _clean_value(val.get('estimated_time'))
                notes = _clean_value(val.get('notes'))
            elif val is not None:
                import_status = _clean_value(val)

        writer.writerow({
            "Source Image": source,
            "Count of VMs": count,
            "Owners": owners,
            "Target Catalog ID": target_catalog_id,
            "Import Status": import_status,
            "Estimated Import Time": estimated_time,
            "Notes": notes,
        })

    # summary row
    writer.writerow({
        "Source Image": "TOTAL",
        "Count of VMs": total_vms,
        "Owners": "",
        "Target Catalog ID": "",
        "Import Status": "",
        "Estimated Import Time": "",
        "Notes": "",
    })

    return output.getvalue()


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


def remediation_tracker_export(vms: list[MigrationVm], remediation_tracker: dict) -> str:
    """Generate a CSV capturing remediation blockers and their resolution tracking.
    
    Columns:
    VM Key, VM Name, Owner, Blocker Type, Blocker Description, Status, Due Date, Notes
    
    Summary section includes:
    - Counts by status
    - Counts by owner
    - Overdue items count
    
    remediation_tracker format: {blocker_id: {status, due_date, notes, owner}, ...}
    Each blocker_id should follow pattern: {vm_key}:{blocker_type}:{description_hash}
    """
    from datetime import datetime
    
    final_vms = _normalize_vms(vms)
    remediation_tracker = remediation_tracker or {}
    
    output = io.StringIO()
    fieldnames = [
        "VM Key", "VM Name", "Owner", "Blocker Type", "Blocker Description",
        "Status", "Due Date", "Notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Build a mapping of vm_key to vm for quick lookup
    vm_map = {}
    for vm in final_vms:
        vm_key = _clean_value(vm.get('vm_key')) or _clean_value(vm.get('VM Key'))
        if vm_key:
            vm_map[vm_key] = vm
    
    # Track summary stats
    status_counts = {}
    owner_counts = {}
    overdue_count = 0
    today = datetime.now().date()
    
    # Process each blocker
    rows_data = []
    for blocker_id, blocker_info in sorted(remediation_tracker.items()):
        if not isinstance(blocker_info, dict):
            continue
        
        # Parse blocker_id format: {vm_key}:{blocker_type}:{description_hash}
        # or just store as-is if it doesn't follow pattern
        parts = str(blocker_id).split(':', 1)
        vm_key = parts[0] if parts else ""
        
        # Get VM details
        vm = vm_map.get(vm_key, {})
        if not vm:
            # Still include blockers even if VM not found
            vm = {"vm_key": vm_key, "vm_name": ""}
        
        vm_key_out = _clean_value(vm.get('vm_key')) or _clean_value(vm.get('VM Key')) or vm_key
        vm_name = _safe_vm_key(vm.get('vm_name')) or _safe_vm_key(vm.get('VM Name'))
        
        # Get blocker-specific fields
        owner = _clean_value(blocker_info.get('owner'))
        blocker_type = _clean_value(blocker_info.get('blocker_type')) or _clean_value(blocker_info.get('type'))
        blocker_desc = _clean_value(blocker_info.get('blocker_description')) or _clean_value(blocker_info.get('description'))
        status = _clean_value(blocker_info.get('status'), 'Open')
        due_date = _clean_value(blocker_info.get('due_date'))
        notes = _clean_value(blocker_info.get('notes'))
        
        # Update summary stats
        status_counts[status] = status_counts.get(status, 0) + 1
        if owner:
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
        
        # Check if overdue
        if due_date:
            try:
                due = datetime.strptime(str(due_date), '%Y-%m-%d').date()
                if due < today and status.lower() not in ['closed', 'resolved', 'complete']:
                    overdue_count += 1
            except (ValueError, TypeError):
                pass
        
        rows_data.append({
            "VM Key": vm_key_out,
            "VM Name": vm_name,
            "Owner": owner,
            "Blocker Type": blocker_type,
            "Blocker Description": blocker_desc,
            "Status": status,
            "Due Date": due_date,
            "Notes": notes,
        })
    
    # Write all blocker rows
    for row in rows_data:
        writer.writerow(row)
    
    # Write summary section
    # Blank row
    writer.writerow({
        "VM Key": "", "VM Name": "", "Owner": "", "Blocker Type": "",
        "Blocker Description": "", "Status": "", "Due Date": "", "Notes": "",
    })
    
    # Summary header
    writer.writerow({
        "VM Key": "", "VM Name": "SUMMARY", "Owner": "", "Blocker Type": "",
        "Blocker Description": "", "Status": "", "Due Date": "", "Notes": "",
    })
    
    # Status counts
    for status in sorted(status_counts.keys()):
        writer.writerow({
            "VM Key": "", "VM Name": f"Status: {status}", "Owner": "",
            "Blocker Type": "", "Blocker Description": "",
            "Status": status_counts[status], "Due Date": "", "Notes": "",
        })
    
    # Owner counts
    for owner in sorted(owner_counts.keys()):
        writer.writerow({
            "VM Key": "", "VM Name": f"Owner: {owner}", "Owner": "",
            "Blocker Type": "", "Blocker Description": "",
            "Status": owner_counts[owner], "Due Date": "", "Notes": "",
        })
    
    # Overdue count
    writer.writerow({
        "VM Key": "", "VM Name": "Overdue Items", "Owner": "",
        "Blocker Type": "", "Blocker Description": "",
        "Status": overdue_count, "Due Date": "", "Notes": "",
    })
    
    # Total count
    total_blockers = len(rows_data)
    writer.writerow({
        "VM Key": "", "VM Name": "TOTAL BLOCKERS", "Owner": "",
        "Blocker Type": "", "Blocker Description": "",
        "Status": total_blockers, "Due Date": "", "Notes": "",
    })
    
    return output.getvalue()
