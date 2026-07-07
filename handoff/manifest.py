import json

from assessments import IMAGE_MAX_GB, IMAGE_MIN_GB

from .utils import (
    _clean_number,
    _clean_value,
    _effective_profile,
    _effective_storage_tier,
    _normalize_vms,
    _safe_vm_key,
    _status_contains,
    _vm_data_disks,
    _vm_disks,
    _vm_findings,
    _vm_network_findings,
    _vm_nics,
    _vm_partitions,
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
                if due_date < today and status.strip().lower() not in {
                    'closed',
                    'complete',
                    'completed',
                    'deferred',
                    'resolved',
                }:
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
    total_vms_pending_import = 0
    import_status_breakdown = {}
    images = {}
    
    for vm in final_vms:
        source_image = _clean_value(vm.get('Original Specs')) or _safe_vm_key(vm.get('VM Name'))
        image_entry = images.setdefault(source_image, {"vm_count": 0, "status": "pending"})
        image_entry["vm_count"] += 1
        status_entry = image_import_status.get(source_image, {})
        image_entry["status"] = _clean_value(status_entry.get('import_status'), 'pending')

    for image_entry in images.values():
        status = image_entry["status"]
        if status.lower() == 'pending':
            total_vms_pending_import += image_entry["vm_count"]
        import_status_breakdown[status] = import_status_breakdown.get(status, 0) + 1
    
    return {
        "total_images": len(images),
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
            "decision_audit_csv": "decision-audit.csv",
            "remediation_backlog_csv": "remediation-backlog.csv",
            "image_import_plan_csv": "image-import-plan.csv",
            "cutover_readiness_csv": "cutover-readiness.csv",
            "planning_state_json": "planning-state.json",
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
