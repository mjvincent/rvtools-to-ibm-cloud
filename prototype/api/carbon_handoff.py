"""Carbon network-plan to migration handoff helpers."""

from __future__ import annotations

from typing import Any

from assessment_quality import (
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
)
from handoff import (
    decision_audit_export,
    generate_disk_mapping_csv,
    generate_cutover_readiness_csv,
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
from models.network_planning import NetworkPlanningState, VmNetworkAssignment
from preflight import generate_preflight_report_csv, generate_preflight_report_json, run_package_preflight


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _row_value(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return _clean(value)
    return ""


def _row_bool(row: dict[str, Any], *keys: str) -> bool:
    for key in keys:
        value = row.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        return str(value).strip().lower() in {"true", "yes", "1"}
    return False


def _row_raw(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _assignment_attr(assignment: VmNetworkAssignment, name: str) -> Any:
    return getattr(assignment, name, None)


def _storage_tier_for(plan: NetworkPlanningState, storage_profile_id: str | None) -> str:
    if not storage_profile_id:
        return ""
    for profile in plan.storage_profiles:
        if profile.id == storage_profile_id:
            return profile.tier
    return storage_profile_id


def _wave_name_for(plan: NetworkPlanningState, wave_id: str | None) -> str:
    if not wave_id:
        return ""
    for wave in plan.waves:
        if wave.id == wave_id:
            return wave.name
    return wave_id


def _subnet_name_for(plan: NetworkPlanningState, subnet_id: str | None) -> str:
    if not subnet_id:
        return ""
    for subnet in plan.subnets:
        if subnet.id == subnet_id:
            return subnet.name
    return subnet_id


def _security_group_name_for(plan: NetworkPlanningState, security_group_id: str | None) -> str:
    if not security_group_id:
        return ""
    for group in plan.security_groups:
        if group.id == security_group_id:
            return group.name
    return security_group_id


def _source_image_for_row(row: dict[str, Any], assignment: VmNetworkAssignment) -> str:
    return (
        _row_value(row, "imageReasons", "Original Specs")
        or assignment.ibm_profile
        or assignment.vm_name
    )


def _carbon_rows_by_key(planning_state_json: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = planning_state_json.get("carbon_assignment_rows") or []
    if not isinstance(rows, list):
        return {}
    keyed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        vm_key = _row_value(row, "id", "VM Key", "vm_key")
        vm_name = _row_value(row, "name", "VM Name", "vm_name")
        if vm_key:
            keyed[vm_key] = row
        if vm_name:
            keyed.setdefault(vm_name, row)
    return keyed


def normalize_pricing_catalog_for_decision_audit(
    pricing_catalog: dict[str, Any] | None,
) -> dict[str, Any]:
    """Shape app pricing catalog into the structure decision_audit_export reads."""
    catalog = dict(pricing_catalog or {})
    profiles = catalog.get("profiles")
    if isinstance(profiles, list):
        catalog["profiles"] = {
            _clean(profile.get("name")): profile
            for profile in profiles
            if isinstance(profile, dict) and profile.get("name")
        }
    storage_tiers = catalog.get("storage_tiers")
    storage_rates = catalog.get("storage_tier_rates")
    if not isinstance(storage_tiers, dict) and isinstance(storage_rates, dict):
        catalog["storage_tiers"] = {
            _clean(tier): {"monthly_per_gb": rate}
            for tier, rate in storage_rates.items()
        }
    return catalog


def carbon_decision_audit_records(
    plan: NetworkPlanningState,
    planning_state_json: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return Streamlit-compatible VM records for Carbon decision audit export."""
    planning_state_json = planning_state_json or {}
    carbon_rows = _carbon_rows_by_key(planning_state_json)
    records: list[dict[str, Any]] = []

    for assignment in plan.vm_assignments:
        row = carbon_rows.get(assignment.vm_key) or carbon_rows.get(assignment.vm_name) or {}
        original_storage = _row_value(row, "storageTier", "Storage Tier")
        chosen_storage = _row_value(row, "overrideStorageTier", "Override Storage Tier")
        if not chosen_storage:
            assignment_override_storage = _assignment_attr(assignment, "override_storage_tier")
            chosen_storage = _clean(assignment_override_storage)
        if not original_storage:
            original_storage = _clean(_assignment_attr(assignment, "storage_tier"))
        if not chosen_storage and assignment.storage_profile_id:
            selected_tier = _storage_tier_for(plan, assignment.storage_profile_id)
            if selected_tier != original_storage:
                chosen_storage = selected_tier

        owner = _row_value(row, "owner", "Owner") or _clean(_assignment_attr(assignment, "owner"))
        application = _row_value(row, "application", "Application") or _clean(_assignment_attr(assignment, "application"))
        wave = _row_value(row, "wave", "Wave") or _wave_name_for(plan, assignment.wave_id)
        records.append({
            "VM Key": assignment.vm_key,
            "VM Name": assignment.vm_name,
            "Power State": _row_value(row, "power", "Power State"),
            "Guest OS": _row_value(row, "guestOs", "Guest OS") or _clean(assignment.guest_os),
            "Source IP": _row_value(row, "sourceIp", "Source IP"),
            "Datacenter": _row_value(row, "datacenter", "Datacenter"),
            "Cluster": _row_value(row, "cluster", "Cluster"),
            "Host": _row_value(row, "host", "Host"),
            "Disk Count": _row_value(row, "diskCount", "Disk Count") or "0",
            "Data Disk Count": _row_value(row, "dataDiskCount", "Data Disk Count") or "0",
            "Total Storage GB": _row_value(row, "totalStorageGb", "Total Storage GB"),
            "Firmware": _row_value(row, "firmware", "Firmware"),
            "Boot Disk GB": _row_value(row, "bootDiskGb", "Boot Disk GB") or _clean(assignment.boot_disk_gb),
            "Configured Memory MiB": _row_value(row, "configuredMemoryMib", "Configured Memory MiB"),
            "Active Memory MiB": _row_value(row, "activeMemoryMib", "Active Memory MiB"),
            "Consumed Memory MiB": _row_value(row, "consumedMemoryMib", "Consumed Memory MiB"),
            "Ballooned Memory MiB": _row_value(row, "balloonedMemoryMib", "Ballooned Memory MiB"),
            "Swapped Memory MiB": _row_value(row, "swappedMemoryMib", "Swapped Memory MiB"),
            "Memory Reservation MiB": _row_value(row, "memoryReservationMib", "Memory Reservation MiB"),
            "Memory Limit MiB": _row_value(row, "memoryLimitMib", "Memory Limit MiB"),
            "Memory Hot Add": _row_value(row, "memoryHotAdd", "Memory Hot Add"),
            "Sizing Memory MiB": _row_value(row, "sizingMemoryMib", "Sizing Memory MiB"),
            "Memory Sizing Basis": _row_value(row, "memorySizingBasis", "Memory Sizing Basis"),
            "Compute (Mo)": _row_value(row, "computeMonthly", "Compute (Mo)"),
            "Storage (Mo)": _row_value(row, "storageMonthly", "Storage (Mo)"),
            "Monthly Cost": _row_value(row, "monthlyCost", "Monthly Cost"),
            "Baseline Cost (Mo)": _row_value(row, "baselineCostMonthly", "Baseline Cost (Mo)"),
            "Savings (Mo)": _row_value(row, "savingsMonthly", "Savings (Mo)"),
            "Pricing Source": _row_value(row, "pricingSource", "Pricing Source"),
            "Pricing Confidence": _row_value(row, "pricingConfidence", "Pricing Confidence"),
            "Pricing Last Updated": _row_value(row, "pricingLastUpdated", "Pricing Last Updated"),
            "Pricing Status": _row_value(row, "pricingStatus", "Pricing Status"),
            "Profile Hourly": _row_value(row, "profileHourly", "Profile Hourly"),
            "Disk Details": _row_raw(row, "diskDetails", "Disk Details", default=[]),
            "Partition Details": _row_raw(row, "partitionDetails", "Partition Details", default=[]),
            "Partition Count": _row_value(row, "partitionCount", "Partition Count"),
            "Unmatched Partition Count": _row_value(row, "unmatchedPartitionCount", "Unmatched Partition Count"),
            "Network Details": _row_raw(row, "networkDetails", "Network Details", default=[]),
            "Readiness Findings": _row_raw(row, "readinessFindings", "Readiness Findings", default=[]),
            "Network Readiness Findings": _row_raw(row, "networkReadinessFindings", "Network Readiness Findings", default=[]),
            "Owner": owner,
            "owner": owner,
            "Application": application,
            "application": application,
            "Wave": wave,
            "wave": wave,
            "Cutover Group": _row_value(row, "cutoverGroup", "Cutover Group"),
            "Priority": _row_value(row, "priority", "Priority"),
            "Dependency Group": _row_value(row, "dependencyGroup", "Dependency Group"),
            "Image Readiness": _row_value(row, "image", "Image Readiness") or "Review",
            "Readiness Reasons": _row_value(row, "imageReasons", "Readiness Reasons"),
            "Migration Readiness": _row_value(row, "migration", "Migration Readiness") or "Review",
            "Migration Readiness Reasons": _row_value(row, "migrationReasons", "Migration Readiness Reasons"),
            "Memory Readiness": _row_value(row, "memory", "Memory Readiness") or "Review",
            "Memory Readiness Reasons": _row_value(row, "memoryReasons", "Memory Readiness Reasons"),
            "Network Readiness": _row_value(row, "networkReadiness", "Network Readiness") or "Review",
            "Network Readiness Reasons": _row_value(row, "networkReasons", "Network Readiness Reasons"),
            "Original Specs": _source_image_for_row(row, assignment),
            "IBM Profile": assignment.ibm_profile or _row_value(row, "profile", "IBM Profile"),
            "Override Profile": assignment.override_profile or _row_value(row, "overrideProfile", "Override Profile"),
            "Override Profile Reason": (
                assignment.override_profile_reason
                or _row_value(row, "overrideProfileReason", "Override Profile Reason")
            ),
            "Storage Tier": original_storage,
            "Override Storage Tier": chosen_storage,
            "Override Storage Tier Reason": (
                _clean(_assignment_attr(assignment, "override_storage_tier_reason"))
                or _row_value(row, "overrideStorageTierReason", "Override Storage Tier Reason")
            ),
            "Network": _row_value(row, "network", "Network") or _clean(_assignment_attr(assignment, "network")),
            "Subnet": _row_value(row, "subnet", "Subnet") or _subnet_name_for(plan, assignment.primary_subnet_id),
            "Security Group": (
                _row_value(row, "securityGroup", "Security Group")
                or _security_group_name_for(plan, assignment.primary_security_group_id)
            ),
            "Exclude?": assignment.excluded or _row_bool(row, "excluded", "Exclude?"),
            "Exclusion Reason": assignment.exclusion_reason or _row_value(row, "exclusionReason", "Exclusion Reason"),
            "Custom Image ID": assignment.custom_image_id or _row_value(row, "customImageId", "Custom Image ID"),
        })
    return records


def carbon_decision_audit_csv(
    plan: NetworkPlanningState,
    planning_state_json: dict[str, Any] | None,
    pricing_catalog: dict[str, Any] | None,
) -> str:
    """Generate Streamlit-compatible decision-audit.csv for a Carbon plan."""
    return decision_audit_export(
        carbon_decision_audit_records(plan, planning_state_json),
        normalize_pricing_catalog_for_decision_audit(pricing_catalog),
    )


def carbon_remediation_tracker(
    planning_state_json: dict[str, Any] | None,
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Normalize Carbon remediation tracker state for handoff CSV generation."""
    planning_state_json = planning_state_json or {}
    raw_tracker = (
        planning_state_json.get("carbon_remediation_tracker")
        or planning_state_json.get("remediation_tracker")
        or {}
    )
    if not isinstance(raw_tracker, dict):
        return {}

    record_by_key = {_row_value(record, "VM Key", "vm_key"): record for record in records}
    readiness_fields = {
        "image": ("Image", "Readiness Reasons"),
        "migration": ("Migration", "Migration Readiness Reasons"),
        "memory": ("Memory", "Memory Readiness Reasons"),
        "network": ("Network", "Network Readiness Reasons"),
    }
    normalized: dict[str, dict[str, Any]] = {}
    for blocker_id, item in raw_tracker.items():
        if not isinstance(item, dict):
            continue
        vm_key = _clean(item.get("vm_key")) or str(blocker_id).split("::", 1)[0].split(":", 1)[0]
        blocker_key = str(blocker_id).split("::", 1)[1].lower() if "::" in str(blocker_id) else ""
        blocker_type, reason_field = readiness_fields.get(blocker_key, ("Remediation", ""))
        record = record_by_key.get(vm_key, {})
        normalized[str(blocker_id)] = {
            "vm_key": vm_key,
            "owner": _clean(item.get("owner")) or _row_value(record, "Owner", "owner"),
            "status": _clean(item.get("status")) or "Open",
            "due_date": _clean(item.get("due_date")) or _clean(item.get("dueDate")),
            "notes": _clean(item.get("notes")),
            "blocker_type": _clean(item.get("blocker_type")) or blocker_type,
            "blocker_description": (
                _clean(item.get("blocker_description"))
                or _clean(item.get("description"))
                or _row_value(record, reason_field)
            ),
        }
    return normalized


def carbon_image_import_status(
    planning_state_json: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Normalize Carbon image import state to handoff snake_case keys."""
    planning_state_json = planning_state_json or {}
    raw_status = (
        planning_state_json.get("carbon_image_import_status")
        or planning_state_json.get("image_import_status")
        or {}
    )
    if not isinstance(raw_status, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for source_image, item in raw_status.items():
        if isinstance(item, dict):
            normalized[str(source_image)] = {
                "target_catalog_id": _clean(item.get("target_catalog_id")) or _clean(item.get("targetCatalogId")),
                "import_status": _clean(item.get("import_status")) or _clean(item.get("importStatus")),
                "estimated_import_time": (
                    _clean(item.get("estimated_import_time"))
                    or _clean(item.get("estimatedImportTime"))
                ),
                "notes": _clean(item.get("notes")),
            }
        else:
            normalized[str(source_image)] = {"import_status": _clean(item)}
    return normalized


def carbon_state_native_handoff_files(
    plan: NetworkPlanningState,
    planning_state_json: dict[str, Any] | None,
) -> dict[str, str]:
    """Generate Carbon ZIP files that only need saved UI planning state."""
    planning_state_json = planning_state_json or {}
    records = carbon_decision_audit_records(plan, planning_state_json)
    remediation_tracker = carbon_remediation_tracker(planning_state_json, records)
    image_status = carbon_image_import_status(planning_state_json)
    metadata = {
        "project_name": plan.metadata.project_name,
        "target_region": plan.metadata.target_region,
        "target_zone": plan.metadata.target_zone,
    }
    return {
        "remediation-backlog.csv": remediation_tracker_export(records, remediation_tracker),
        "image-import-plan.csv": image_import_export(records, image_status),
        "cutover-readiness.csv": generate_cutover_readiness_csv(
            records,
            remediation_tracker=remediation_tracker,
            image_import_status=image_status,
        ),
        "planning-state.json": generate_planning_state_json(
            records,
            remediation_tracker=remediation_tracker,
            image_import_status=image_status,
            metadata=metadata,
        ),
    }


def carbon_migration_context(
    plan: NetworkPlanningState,
    pricing_catalog: dict[str, Any] | None = None,
    assessment_quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the manifest/runbook context for Carbon handoff files."""
    pricing_catalog = pricing_catalog or {}
    metadata = pricing_catalog.get("metadata", {}) if isinstance(pricing_catalog, dict) else {}
    vpc = plan.vpcs[0] if plan.vpcs else None
    return {
        "project_name": plan.metadata.project_name,
        "target_region": plan.metadata.target_region,
        "target_zone": plan.metadata.target_zone,
        "vpc_name": vpc.name if vpc else "migration-vpc",
        "address_prefix_strategy": vpc.address_prefix_mode if vpc else "manual",
        "deployment_target": plan.metadata.deployment_target,
        "generate_security_groups": True,
        "pricing_mode": metadata.get("mode"),
        "pricing_source": metadata.get("source"),
        "pricing_confidence": metadata.get("confidence"),
        "pricing_status": metadata.get("pricing_status"),
        "pricing_last_updated": metadata.get("last_updated"),
        "assessment_quality": assessment_quality or {},
    }


def carbon_preflight_findings(
    plan: NetworkPlanningState,
    records: list[dict[str, Any]],
    pricing_catalog: dict[str, Any] | None,
) -> list[Any]:
    """Run package preflight with Carbon network-plan resources."""
    networks = [
        {
            "name": subnet.name,
            "vlan": subnet.source_network or subnet.purpose or "",
            "cidr": subnet.cidr,
        }
        for subnet in plan.subnets
    ]
    custom_cidrs = {
        subnet.name: subnet.cidr
        for subnet in plan.subnets
        if subnet.cidr
    }
    profiles = []
    if isinstance(pricing_catalog, dict):
        raw_profiles = pricing_catalog.get("profiles", [])
        profiles = (
            list(raw_profiles.values())
            if isinstance(raw_profiles, dict)
            else list(raw_profiles or [])
        )
    return run_package_preflight(
        records,
        networks,
        plan.metadata.target_region,
        custom_cidrs=custom_cidrs,
        enable_security_groups=True,
        catalog_profiles=profiles,
        ssh_source_cidr="",
    )


def carbon_full_handoff_files(
    plan: NetworkPlanningState,
    planning_state_json: dict[str, Any] | None,
    pricing_catalog: dict[str, Any] | None,
) -> dict[str, str]:
    """Generate remaining Streamlit-style handoff artifacts for a Carbon plan."""
    planning_state_json = planning_state_json or {}
    records = carbon_decision_audit_records(plan, planning_state_json)
    normalized_pricing = normalize_pricing_catalog_for_decision_audit(pricing_catalog)
    remediation_tracker = carbon_remediation_tracker(planning_state_json, records)
    image_status = carbon_image_import_status(planning_state_json)
    summary = planning_state_json.get("carbon_summary") or {}
    assessment_quality = summary.get("assessment_quality") if isinstance(summary, dict) else {}
    context = carbon_migration_context(plan, pricing_catalog, assessment_quality)
    preflight_findings = carbon_preflight_findings(plan, records, pricing_catalog)
    return {
        "migration-manifest.json": generate_migration_manifest(
            records,
            context,
            image_import_status=image_status,
            pricing_catalog=normalized_pricing,
            remediation_tracker=remediation_tracker,
        ),
        "assessment-quality.json": generate_assessment_quality_json(assessment_quality or {}),
        "assessment-quality.csv": generate_assessment_quality_csv(assessment_quality or {}),
        "preflight-report.json": generate_preflight_report_json(preflight_findings),
        "preflight-report.csv": generate_preflight_report_csv(preflight_findings),
        "pricing-diagnostics.json": generate_pricing_diagnostics_json(normalized_pricing, records),
        "pricing-diagnostics.csv": generate_pricing_diagnostics_csv(normalized_pricing, records),
        "vm-mapping.csv": generate_vm_mapping_csv(records),
        "disk-mapping.csv": generate_disk_mapping_csv(records),
        "partition-mapping.csv": generate_partition_mapping_csv(records),
        "nic-mapping.csv": generate_nic_mapping_csv(records, True),
        "memory-readiness.csv": generate_memory_readiness_csv(records),
        "readiness-findings.csv": generate_readiness_findings_csv(records),
        "image-import-variables.tfvars.example": generate_image_import_tfvars(records),
        "migration-runbook.md": generate_migration_runbook(context),
    }
