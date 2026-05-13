from catalog_pricing import DEFAULT_STORAGE_TIER_RATES, STATIC_IBM_VPC_CATALOG

IBM_VPC_CATALOG = STATIC_IBM_VPC_CATALOG
STORAGE_TIERS = ["3iops-tier", "5iops-tier", "10iops-tier"]


def get_catalog_profiles(catalog=None):
    """Returns the list of supported IBM VPC profile names."""
    active_catalog = catalog or IBM_VPC_CATALOG
    return [profile['name'] for profile in active_catalog]


def find_cheapest_fit(target_cpu, target_ram, catalog=None):
    """Finds the lowest-priced profile that fits requirements."""
    active_catalog = catalog or IBM_VPC_CATALOG
    candidates = [
        p for p in active_catalog
        if p['cpu'] >= target_cpu and p['ram'] >= target_ram
        and p.get('hourly', 0) > 0
    ]
    if not candidates:
        return {
            "name": "bx2-16x64",
            "cpu": 16,
            "ram": 64,
            "hourly": 0.912,
            "pricing_source": "static-fallback",
            "pricing_confidence": "fallback-static",
        }
    optimized = sorted(candidates, key=lambda x: x['hourly'])
    return optimized[0]


def map_vmware_to_ibm_vpc(cpus, memory, usage, region,
                          threshold, storage_gb, tier,
                          memory_is_sizing=False, catalog=None,
                          storage_tier_rates=None, pricing_metadata=None):
    """Strategy B: Full Solution Cost (Compute + Storage)."""
    util_factor = threshold / 100
    needed_cpu = max(1, round(cpus * util_factor))
    if memory_is_sizing:
        needed_ram = max(2, round(memory / 1024))
    else:
        needed_ram = max(2, round((memory / 1024) * 0.8))
    optimized = find_cheapest_fit(needed_cpu, needed_ram, catalog=catalog)
    tier_rates = storage_tier_rates or DEFAULT_STORAGE_TIER_RATES
    pricing_metadata = pricing_metadata or {}

    compute_monthly = round(optimized['hourly'] * 730, 2)
    storage_monthly = round(storage_gb * tier_rates.get(tier, 0.10), 2)
    total_monthly = round(compute_monthly + storage_monthly, 2)

    return {
        "profile": optimized['name'],
        "compute_cost": compute_monthly,
        "storage_cost": storage_monthly,
        "monthly": total_monthly,
        "is_rightsized": optimized['cpu'] < cpus,
        "pricing_source": optimized.get(
            'pricing_source', pricing_metadata.get('source', 'static')
        ),
        "pricing_confidence": optimized.get(
            'pricing_confidence',
            pricing_metadata.get('confidence', 'fallback-static')
        ),
        "pricing_last_updated": pricing_metadata.get('last_updated', ''),
        "profile_hourly": optimized.get('hourly', 0),
    }


def recommend_storage_tier(vm_name, usage):
    """Return the default IBM Cloud block storage tier for a workload."""
    is_db = any(token in str(vm_name).upper() for token in ["SQL", "DB", "PROD", "SAP"])
    if is_db:
        return "10iops-tier"
    return "5iops-tier" if usage and usage > 70 else "3iops-tier"
