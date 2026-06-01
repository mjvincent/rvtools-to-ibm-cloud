import csv
import io
import json

from models import MigrationVm, as_bool

from .utils import (
    _clean_number,
    _clean_value,
    _effective_profile,
    _effective_storage_tier,
    _normalize_vms,
    _safe_vm_key,
)


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


