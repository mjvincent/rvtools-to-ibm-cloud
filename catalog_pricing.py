import json
import os
from datetime import datetime, timezone
from pathlib import Path


STATIC_IBM_VPC_CATALOG = [
    {"name": "cx2-2x4", "cpu": 2, "ram": 4, "hourly": 0.063},
    {"name": "bx2-2x8", "cpu": 2, "ram": 8, "hourly": 0.114},
    {"name": "mx2-2x16", "cpu": 2, "ram": 16, "hourly": 0.158},
    {"name": "cx2-4x8", "cpu": 4, "ram": 8, "hourly": 0.126},
    {"name": "bx2-4x16", "cpu": 4, "ram": 16, "hourly": 0.228},
    {"name": "mx2-4x32", "cpu": 4, "ram": 32, "hourly": 0.316},
    {"name": "cx2-8x16", "cpu": 8, "ram": 16, "hourly": 0.252},
    {"name": "bx2-8x32", "cpu": 8, "ram": 32, "hourly": 0.456},
]

DEFAULT_STORAGE_TIER_RATES = {
    "3iops-tier": 0.10,
    "5iops-tier": 0.13,
    "10iops-tier": 0.17,
}

DEFAULT_CACHE_PATH = Path("data/ibm_vpc_pricing_cache.json")


def _now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _static_profile_index():
    return {profile["name"]: profile for profile in STATIC_IBM_VPC_CATALOG}


def _normalize_profile(profile, fallback_price=None):
    name = profile.get("name", "")
    cpu = profile.get("cpu", profile.get("vcpus", 0))
    ram = profile.get("ram", profile.get("memory", 0))
    hourly = profile.get("hourly", profile.get("hourly_usd", fallback_price))
    return {
        "name": name,
        "cpu": int(cpu or 0),
        "ram": float(ram or 0),
        "hourly": float(hourly or 0),
        "pricing_source": profile.get("pricing_source", "unknown"),
        "pricing_confidence": profile.get("pricing_confidence", "unknown"),
        "family": profile.get("family", _infer_family(name)),
    }


def _infer_family(profile_name):
    return profile_name.split("-")[0] if profile_name else "unknown"


def _static_catalog(metadata=None):
    metadata = metadata or {}
    profiles = []
    for profile in STATIC_IBM_VPC_CATALOG:
        enriched = dict(profile)
        enriched["pricing_source"] = "static"
        enriched["pricing_confidence"] = "fallback-static"
        enriched["family"] = _infer_family(profile["name"])
        profiles.append(enriched)
    return {
        "profiles": profiles,
        "storage_tier_rates": dict(DEFAULT_STORAGE_TIER_RATES),
        "metadata": {
            "mode": metadata.get("mode", "static"),
            "source": metadata.get("source", "static"),
            "confidence": metadata.get("confidence", "fallback-static"),
            "status": metadata.get("status", "Using bundled fallback pricing"),
            "region": metadata.get("region", ""),
            "last_updated": metadata.get("last_updated", ""),
        },
    }


def load_cached_catalog(cache_path=DEFAULT_CACHE_PATH):
    path = Path(cache_path)
    if not path.exists():
        return _static_catalog({
            "mode": "cached",
            "source": "static",
            "confidence": "fallback-static",
            "status": f"Cache not found at {path}; using static fallback",
        })
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _static_catalog({
            "mode": "cached",
            "source": "static",
            "confidence": "fallback-static",
            "status": f"Cache load failed: {exc}; using static fallback",
        })

    profiles = [
        _normalize_profile(profile)
        for profile in data.get("profiles", [])
        if profile.get("name")
    ]
    if not profiles:
        return _static_catalog({
            "mode": "cached",
            "source": "static",
            "confidence": "fallback-static",
            "status": "Cache contained no profiles; using static fallback",
        })

    return {
        "profiles": profiles,
        "storage_tier_rates": data.get(
            "storage_tier_rates", dict(DEFAULT_STORAGE_TIER_RATES)
        ),
        "metadata": {
            "mode": "cached",
            "source": data.get("source", "cached"),
            "confidence": data.get("confidence", "cached"),
            "status": data.get("status", "Using cached profile pricing"),
            "region": data.get("region", ""),
            "last_updated": data.get("last_updated", ""),
        },
    }


def discover_live_catalog(region, api_key=None):
    api_key = api_key or os.getenv("IBMCLOUD_API_KEY")
    if not api_key:
        return _static_catalog({
            "mode": "live",
            "source": "static",
            "confidence": "fallback-static",
            "region": region,
            "status": "IBMCLOUD_API_KEY not set; using static fallback",
        })

    try:
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        from ibm_vpc import VpcV1
    except ImportError as exc:
        return _static_catalog({
            "mode": "live",
            "source": "static",
            "confidence": "fallback-static",
            "region": region,
            "status": f"IBM SDK not installed: {exc}; using static fallback",
        })

    try:
        auth = IAMAuthenticator(api_key)
        service = VpcV1(authenticator=auth)
        service.set_service_url(f"https://{region}.iaas.cloud.ibm.com/v1")
        result = service.list_instance_profiles().get_result()
    except Exception as exc:
        return _static_catalog({
            "mode": "live",
            "source": "static",
            "confidence": "fallback-static",
            "region": region,
            "status": f"VPC profile discovery failed: {exc}; using static fallback",
        })

    static_index = _static_profile_index()
    profiles = []
    for profile in result.get("profiles", []):
        name = profile.get("name", "")
        static_profile = static_index.get(name, {})
        vcpu_count = profile.get("vcpu_count", {})
        memory = profile.get("memory", {})
        profiles.append({
            "name": name,
            "cpu": vcpu_count.get("value", static_profile.get("cpu", 0)),
            "ram": memory.get("value", static_profile.get("ram", 0)),
            "hourly": static_profile.get("hourly", 0),
            "pricing_source": (
                "live-profile-static-price"
                if static_profile else "live-profile-unpriced"
            ),
            "pricing_confidence": (
                "profile-live-price-static"
                if static_profile else "profile-live-price-missing"
            ),
            "family": _infer_family(name),
        })

    priced_profiles = [profile for profile in profiles if profile["hourly"] > 0]
    if not priced_profiles:
        return _static_catalog({
            "mode": "live",
            "source": "static",
            "confidence": "fallback-static",
            "region": region,
            "status": "Live profiles found, but no prices mapped; using static fallback",
        })

    return {
        "profiles": priced_profiles,
        "storage_tier_rates": dict(DEFAULT_STORAGE_TIER_RATES),
        "metadata": {
            "mode": "live",
            "source": "ibm-vpc-profile-api",
            "confidence": "profile-live-price-static",
            "region": region,
            "last_updated": _now_utc(),
            "status": (
                "Live IBM profile discovery succeeded; exact profile pricing "
                "uses mapped static fallback where available"
            ),
        },
    }


def write_catalog_cache(catalog, cache_path=DEFAULT_CACHE_PATH):
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profiles": catalog.get("profiles", []),
        "storage_tier_rates": catalog.get(
            "storage_tier_rates", DEFAULT_STORAGE_TIER_RATES
        ),
        **catalog.get("metadata", {}),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def get_pricing_catalog(mode="static", region="us-south",
                        cache_path=DEFAULT_CACHE_PATH, api_key=None):
    mode = (mode or "static").lower()
    if mode == "cached":
        catalog = load_cached_catalog(cache_path)
    elif mode == "live":
        catalog = discover_live_catalog(region, api_key=api_key)
    else:
        catalog = _static_catalog({"mode": "static", "region": region})

    catalog["profiles"] = [
        _normalize_profile(profile) for profile in catalog.get("profiles", [])
    ]
    return catalog


def pricing_status_summary(catalog):
    metadata = catalog.get("metadata", {})
    parts = [
        f"mode={metadata.get('mode', 'unknown')}",
        f"source={metadata.get('source', 'unknown')}",
        f"confidence={metadata.get('confidence', 'unknown')}",
    ]
    if metadata.get("last_updated"):
        parts.append(f"updated={metadata['last_updated']}")
    return " | ".join(parts)
