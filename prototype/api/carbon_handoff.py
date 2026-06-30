"""Carbon network-plan to migration handoff helpers."""

from __future__ import annotations

from typing import Any

from handoff import decision_audit_export
from models.network_planning import NetworkPlanningState, VmNetworkAssignment


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

        records.append({
            "VM Key": assignment.vm_key,
            "VM Name": assignment.vm_name,
            "owner": _row_value(row, "owner", "Owner") or _clean(_assignment_attr(assignment, "owner")),
            "application": _row_value(row, "application", "Application") or _clean(_assignment_attr(assignment, "application")),
            "wave": _row_value(row, "wave", "Wave") or _wave_name_for(plan, assignment.wave_id),
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
            "Exclude?": assignment.excluded or _row_bool(row, "excluded", "Exclude?"),
            "Exclusion Reason": assignment.exclusion_reason or _row_value(row, "exclusionReason", "Exclusion Reason"),
            "Total Storage GB": _row_value(row, "totalStorageGb", "Total Storage GB"),
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
