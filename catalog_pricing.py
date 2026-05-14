import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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
GLOBAL_CATALOG_BASE_URL = "https://globalcatalog.cloud.ibm.com/api/v1"
POWER_VIRTUAL_SERVER_SERVICE_ID = "abd259f0-9990-11e8-acc8-b9f54a8f1661"
POWER_VIRTUAL_SERVER_PLAN_NAME = "power-virtual-server-project"
TRUSTED_PRICING_CACHE_SCHEMA_VERSION = 2
HOURS_PER_MONTH = 730
POWER_REGION_DEPLOYMENT_LOCATIONS = {
    "au-syd": ("syd04", "syd05"),
    "br-sao": ("sao01", "sao04"),
    "ca-tor": ("tor01",),
    "eu-de": ("eu-de-1", "eu-de-2"),
    "eu-es": ("mad02", "mad04"),
    "eu-gb": ("lon04", "lon06"),
    "jp-osa": ("osa21",),
    "jp-tok": ("tok04",),
    "us-east": ("wdc06", "wdc07"),
    "us-south": ("dal10", "dal12"),
}


@dataclass(frozen=True)
class CatalogPrice:
    price: float
    quantity_tier: float = 1


@dataclass(frozen=True)
class CatalogMetric:
    plan_id: str
    deployment_id: str
    deployment_location: str
    deployment_region: str
    metric_id: str
    part_ref: str
    resource_display_name: str
    charge_unit: str
    charge_unit_name: str
    charge_unit_display_name: str
    charge_unit_quantity: float
    tier_model: str
    country: str
    currency: str
    prices: tuple
    effective_from: str
    effective_until: str
    source_timestamp: str

    @property
    def unit_price(self):
        if not self.prices:
            return 0.0
        return float(self.prices[0].price)

    def to_dict(self):
        payload = asdict(self)
        payload["prices"] = [asdict(price) for price in self.prices]
        return payload


@dataclass(frozen=True)
class BillingDimensionMatch:
    dimension: str
    metric_id: str
    unit_price: float
    charge_unit_quantity: float
    source_status: str
    reason: str = ""

    def to_dict(self):
        return asdict(self)


def _now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_ibmcloud_api_key(env_file=".env"):
    """
    Resolve the IBM Cloud API key from environment or a local .env file.

    The key is never logged or returned in generated handoff files.
    """
    api_key = os.getenv("IBMCLOUD_API_KEY")
    if api_key:
        return api_key

    try:
        from dotenv import load_dotenv
    except ImportError:
        path = Path(env_file)
        if not path.exists():
            return ""
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "IBMCLOUD_API_KEY":
                return value.strip().strip('"').strip("'")
        return ""

    load_dotenv(env_file)
    return os.getenv("IBMCLOUD_API_KEY", "")


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
        "pricing_status": profile.get("pricing_status", "unmapped"),
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
        enriched["pricing_status"] = "static_fallback"
        enriched["family"] = _infer_family(profile["name"])
        profiles.append(enriched)
    return {
        "profiles": profiles,
        "storage_tier_rates": dict(DEFAULT_STORAGE_TIER_RATES),
        "billing_dimension_rates": {},
        "catalog_metrics": [],
        "unmapped_catalog_metrics": [],
        "metadata": {
            "mode": metadata.get("mode", "static"),
            "source": metadata.get("source", "static"),
            "confidence": metadata.get("confidence", "fallback-static"),
            "pricing_status": metadata.get("pricing_status", "static_fallback"),
            "status": metadata.get("status", "Using bundled fallback pricing"),
            "region": metadata.get("region", ""),
            "country": metadata.get("country", "USA"),
            "currency": metadata.get("currency", "USD"),
            "last_updated": metadata.get("last_updated", ""),
        },
    }


def _coerce_price(raw_price):
    if raw_price is None:
        return 0.0
    if isinstance(raw_price, dict):
        raw_price = raw_price.get("price", raw_price.get("Price", 0))
    try:
        return float(raw_price or 0)
    except (TypeError, ValueError):
        return 0.0


def _coerce_quantity(raw_value, default=1):
    try:
        return float(raw_value if raw_value not in (None, "") else default)
    except (TypeError, ValueError):
        return float(default)


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_effective(metric, now=None):
    now = now or datetime.now(timezone.utc)
    starts = _parse_datetime(metric.effective_from)
    ends = _parse_datetime(metric.effective_until)
    if starts and now < starts:
        return False
    if ends and now > ends:
        return False
    return True


def _select_amount(metric, country, currency):
    for amount in metric.get("amounts", []) or []:
        if amount.get("country") == country and amount.get("currency") == currency:
            return amount
    return None


def normalize_catalog_pricing(
    pricing_payload,
    *,
    plan_id="",
    deployment_id="",
    deployment_location="",
    deployment_region="",
    country="USA",
    currency="USD",
    source_timestamp=None,
):
    """Normalize IBM Global Catalog pricing metrics into auditable records."""
    source_timestamp = source_timestamp or _now_utc()
    records = []
    for metric in pricing_payload.get("metrics", []) or []:
        amount = _select_amount(metric, country, currency)
        if not amount:
            continue
        prices = tuple(
            CatalogPrice(
                price=_coerce_price(price),
                quantity_tier=_coerce_quantity(price.get("quantity_tier", 1)),
            )
            for price in amount.get("prices", []) or []
        )
        records.append(CatalogMetric(
            plan_id=plan_id,
            deployment_id=pricing_payload.get("deployment_id", deployment_id),
            deployment_location=pricing_payload.get(
                "deployment_location", deployment_location
            ),
            deployment_region=pricing_payload.get(
                "deployment_region", deployment_region
            ),
            metric_id=str(metric.get("metric_id", "")),
            part_ref=str(metric.get("part_ref", "")),
            resource_display_name=str(metric.get("resource_display_name", "")),
            charge_unit=str(metric.get("charge_unit", "")),
            charge_unit_name=str(metric.get("charge_unit_name", "")),
            charge_unit_display_name=str(metric.get("charge_unit_display_name", "")),
            charge_unit_quantity=_coerce_quantity(
                metric.get("charge_unit_quantity", 1)
            ),
            tier_model=str(metric.get("tier_model", "")),
            country=country,
            currency=currency,
            prices=prices,
            effective_from=str(metric.get("effective_from", "")),
            effective_until=str(metric.get("effective_until", "")),
            source_timestamp=source_timestamp,
        ))
    return sorted(
        records,
        key=lambda item: (
            item.deployment_region,
            item.resource_display_name,
            item.metric_id,
            item.charge_unit_name,
        ),
    )


def _normalize_text(*parts):
    return " ".join(str(part or "").lower() for part in parts)


def _is_linear(metric):
    return "linear" in metric.tier_model.lower()


def _price_per_charge_unit(metric):
    if not _is_effective(metric):
        return 0.0
    if not _is_linear(metric):
        return 0.0
    if metric.unit_price <= 0 or metric.charge_unit_quantity <= 0:
        return 0.0
    return metric.unit_price / metric.charge_unit_quantity


def _metric_matches_dimension(metric, dimension):
    text = _normalize_text(
        metric.metric_id,
        metric.resource_display_name,
        metric.charge_unit,
        metric.charge_unit_name,
        metric.charge_unit_display_name,
    )
    if dimension == "compute_core_hourly":
        return (
            any(token in text for token in ["core", "processor", "vcpu"])
            and any(token in text for token in ["hour", "hr"])
            and "memory" not in text
            and "storage" not in text
        )
    if dimension == "memory_gb_hourly":
        return (
            any(token in text for token in ["memory", "ram"])
            and any(token in text for token in ["gb", "gib", "gigabyte"])
            and any(token in text for token in ["hour", "hr"])
        )
    if dimension.startswith("storage_"):
        tier = dimension.removeprefix("storage_").removesuffix("_monthly")
        iops = tier.split("iops", 1)[0]
        return (
            "storage" in text
            and any(token in text for token in ["gb", "gib", "gigabyte"])
            and (iops in text or tier.replace("-", " ") in text)
        )
    return False


def _match_dimension(metrics, dimension):
    candidates = [metric for metric in metrics if _metric_matches_dimension(metric, dimension)]
    valid = [metric for metric in candidates if _price_per_charge_unit(metric) > 0]
    if len(valid) == 1:
        metric = valid[0]
        return BillingDimensionMatch(
            dimension=dimension,
            metric_id=metric.metric_id,
            unit_price=round(_price_per_charge_unit(metric), 8),
            charge_unit_quantity=metric.charge_unit_quantity,
            source_status="exact_catalog",
        )
    if not candidates:
        return BillingDimensionMatch(
            dimension=dimension,
            metric_id="",
            unit_price=0,
            charge_unit_quantity=0,
            source_status="unmapped",
            reason="no matching catalog metric",
        )
    if not valid:
        return BillingDimensionMatch(
            dimension=dimension,
            metric_id="",
            unit_price=0,
            charge_unit_quantity=0,
            source_status="unmapped",
            reason="matching metrics were expired, unpriced, or non-linear",
        )
    return BillingDimensionMatch(
        dimension=dimension,
        metric_id="",
        unit_price=0,
        charge_unit_quantity=0,
        source_status="unmapped",
        reason="multiple matching catalog metrics",
    )


def map_catalog_billing_dimensions(metrics, storage_tiers=None):
    """Map normalized catalog metrics to local billing dimensions conservatively."""
    storage_tiers = storage_tiers or DEFAULT_STORAGE_TIER_RATES.keys()
    dimensions = ["compute_core_hourly", "memory_gb_hourly"]
    dimensions.extend(f"storage_{tier}_monthly" for tier in storage_tiers)
    matches = [_match_dimension(metrics, dimension) for dimension in dimensions]
    exact_rates = {
        match.dimension: match.unit_price
        for match in matches
        if match.source_status == "exact_catalog"
    }
    unmapped = [match.to_dict() for match in matches if match.source_status != "exact_catalog"]
    return exact_rates, unmapped


def apply_catalog_rates_to_profiles(profiles, billing_dimension_rates):
    cpu_rate = billing_dimension_rates.get("compute_core_hourly", 0)
    memory_rate = billing_dimension_rates.get("memory_gb_hourly", 0)
    if cpu_rate <= 0 or memory_rate <= 0:
        return [dict(profile) for profile in profiles], False

    mapped = []
    for profile in profiles:
        enriched = dict(profile)
        hourly = (float(enriched.get("cpu", 0)) * cpu_rate) + (
            float(enriched.get("ram", 0)) * memory_rate
        )
        enriched["hourly"] = round(hourly, 6)
        enriched["pricing_source"] = "ibm-global-catalog"
        enriched["pricing_confidence"] = "exact_catalog"
        enriched["pricing_status"] = "exact_catalog"
        mapped.append(enriched)
    return mapped, True


def apply_catalog_rates_to_storage(billing_dimension_rates, fallback_rates=None):
    fallback_rates = fallback_rates or DEFAULT_STORAGE_TIER_RATES
    rates = dict(fallback_rates)
    exact = False
    for tier in fallback_rates:
        dimension = f"storage_{tier}_monthly"
        hourly = billing_dimension_rates.get(dimension, 0)
        if hourly > 0:
            rates[tier] = round(hourly * HOURS_PER_MONTH, 6)
            exact = True
    return rates, exact


def _static_catalog_with_catalog_rates(metadata, metrics, rates, unmapped):
    profiles, exact_profiles = apply_catalog_rates_to_profiles(
        STATIC_IBM_VPC_CATALOG, rates
    )
    storage_rates, exact_storage = apply_catalog_rates_to_storage(rates)
    required = {"compute_core_hourly", "memory_gb_hourly"}
    required.update(
        f"storage_{tier}_monthly" for tier in DEFAULT_STORAGE_TIER_RATES
    )
    if required.issubset(rates):
        pricing_status = "exact_catalog"
    elif exact_profiles or exact_storage:
        pricing_status = "cached_catalog"
    else:
        pricing_status = "unmapped"
    confidence = (
        "exact_catalog"
        if pricing_status == "exact_catalog"
        else pricing_status
    )
    if not exact_profiles:
        profiles = _static_catalog(metadata)["profiles"]
    return {
        "profiles": profiles,
        "storage_tier_rates": storage_rates,
        "billing_dimension_rates": dict(sorted(rates.items())),
        "catalog_metrics": [metric.to_dict() for metric in metrics],
        "unmapped_catalog_metrics": unmapped,
        "metadata": {
            **metadata,
            "confidence": confidence,
            "pricing_status": pricing_status,
        },
    }


def load_cached_catalog(cache_path=DEFAULT_CACHE_PATH):
    path = Path(cache_path)
    if not path.exists():
        return _static_catalog({
            "mode": "cached",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
            "status": f"Cache not found at {path}; using static fallback",
        })
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _static_catalog({
            "mode": "cached",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
            "status": f"Cache load failed: {exc}; using static fallback",
        })

    profile_status = data.get("pricing_status", "cached_catalog")
    profiles = [
        _normalize_profile({"pricing_status": profile_status, **profile})
        for profile in data.get("profiles", [])
        if profile.get("name")
    ]
    if not profiles:
        return _static_catalog({
            "mode": "cached",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
            "status": "Cache contained no profiles; using static fallback",
        })

    return {
        "profiles": profiles,
        "storage_tier_rates": data.get(
            "storage_tier_rates", dict(DEFAULT_STORAGE_TIER_RATES)
        ),
        "billing_dimension_rates": data.get("billing_dimension_rates", {}),
        "catalog_metrics": data.get("catalog_metrics", []),
        "unmapped_catalog_metrics": data.get("unmapped_catalog_metrics", []),
        "metadata": {
            "mode": "cached",
            "source": data.get("source", "cached"),
            "confidence": data.get("confidence", "cached"),
            "pricing_status": data.get("pricing_status", "cached_catalog"),
            "status": data.get("status", "Using cached profile pricing"),
            "region": data.get("region", ""),
            "country": data.get("country", "USA"),
            "currency": data.get("currency", "USD"),
            "last_updated": data.get("last_updated", ""),
            "schema_version": data.get("schema_version", 1),
        },
    }


def discover_live_catalog(region, api_key=None):
    if api_key is None:
        api_key = get_ibmcloud_api_key()
    if not api_key:
        return _static_catalog({
            "mode": "live",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
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
            "pricing_status": "static_fallback",
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
            "pricing_status": "static_fallback",
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
            "pricing_status": "static_fallback" if static_profile else "unmapped",
            "family": _infer_family(name),
        })

    priced_profiles = [profile for profile in profiles if profile["hourly"] > 0]
    if not priced_profiles:
        return _static_catalog({
            "mode": "live",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
            "region": region,
            "status": "Live profiles found, but no prices mapped; using static fallback",
        })

    return {
        "profiles": priced_profiles,
        "storage_tier_rates": dict(DEFAULT_STORAGE_TIER_RATES),
        "billing_dimension_rates": {},
        "catalog_metrics": [],
        "unmapped_catalog_metrics": [],
        "metadata": {
            "mode": "live",
            "source": "ibm-vpc-profile-api",
            "confidence": "profile-live-price-static",
            "pricing_status": "static_fallback",
            "region": region,
            "country": "USA",
            "currency": "USD",
            "last_updated": _now_utc(),
            "status": (
                "Live IBM profile discovery succeeded; exact profile pricing "
                "uses mapped static fallback where available"
            ),
        },
    }


def _read_json_url(url, timeout=30, headers=None):
    request = Request(
        url,
        headers={
            "accept": "application/json",
            "user-agent": "rvtools-to-ibm-cloud-pricing-cache/1.0",
            **(headers or {}),
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _catalog_get(path, base_url=GLOBAL_CATALOG_BASE_URL, fetch_json=None,
                 headers=None):
    fetch_json = fetch_json or _read_json_url
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    try:
        if fetch_json is _read_json_url:
            return fetch_json(url, headers=headers)
        return fetch_json(url)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Global Catalog request failed for {path}: {exc}") from exc


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def _select_power_plan(plans_payload):
    resources = plans_payload.get("resources", []) or []
    for plan in resources:
        names = [
            plan.get("name", ""),
            plan.get("metadata", {}).get("origin_name", ""),
            plan.get("metadata", {}).get("ui", {}).get("display_name", ""),
            plan.get("metadata", {}).get("ui", {}).get("long_description", ""),
        ]
        if POWER_VIRTUAL_SERVER_PLAN_NAME in {_slug(name) for name in names}:
            return plan
    for plan in resources:
        pricing_type = str(
            plan.get("metadata", {}).get("pricing", {}).get("type", "")
        ).lower()
        if pricing_type in {"paid", "paygo"}:
            return plan
    return resources[0] if resources else {}


def _select_deployment(deployments_payload, region):
    resources = deployments_payload.get("resources", []) or []
    preferred_locations = POWER_REGION_DEPLOYMENT_LOCATIONS.get(region, ())
    for deployment in resources:
        if deployment.get("deployment_region") == region:
            return deployment
    for deployment in resources:
        if deployment.get("deployment_location") == region:
            return deployment
    for location in preferred_locations:
        for deployment in resources:
            if deployment.get("deployment_location") == location:
                return deployment
            if deployment.get("deployment_region") == location:
                return deployment
    for deployment in resources:
        if str(deployment.get("deployment_region", "")).startswith(region):
            return deployment
    return {}


def _deployment_choices(deployments_payload):
    choices = []
    for deployment in deployments_payload.get("resources", []) or []:
        location = deployment.get("deployment_location", "")
        region = deployment.get("deployment_region", "")
        choices.append(location or region)
    return ", ".join(choice for choice in choices if choice)


def fetch_power_virtual_server_pricing(
    *,
    region="us-south",
    country="USA",
    currency="USD",
    api_key=None,
    base_url=GLOBAL_CATALOG_BASE_URL,
    fetch_json=None,
):
    """Fetch and normalize public IBM Power Virtual Server catalog pricing."""
    plans = _catalog_get(
        f"/{POWER_VIRTUAL_SERVER_SERVICE_ID}/plan?_offset=0&_limit=50",
        base_url=base_url,
        fetch_json=fetch_json,
    )
    plan = _select_power_plan(plans)
    plan_id = plan.get("id", plan.get("_id", ""))
    if not plan_id:
        raise ValueError("IBM Global Catalog did not return a Power VS plan ID.")

    deployments = _catalog_get(
        f"/{quote(plan_id)}/pricing/deployment",
        base_url=base_url,
        fetch_json=fetch_json,
    )
    deployment = _select_deployment(deployments, region)
    if not deployment.get("deployment_id"):
        choices = _deployment_choices(deployments)
        raise ValueError(
            f"No Power VS pricing deployment found for region {region}. "
            f"Available deployments: {choices}"
        )

    source_timestamp = _now_utc()
    metrics = normalize_catalog_pricing(
        deployment,
        plan_id=plan_id,
        deployment_id=deployment.get("deployment_id", ""),
        deployment_location=deployment.get("deployment_location", ""),
        deployment_region=deployment.get("deployment_region", region),
        country=country,
        currency=currency,
        source_timestamp=source_timestamp,
    )
    rates, unmapped = map_catalog_billing_dimensions(metrics)
    metadata = {
        "mode": "cached",
        "source": "ibm-global-catalog",
        "region": region,
        "country": country,
        "currency": currency,
        "last_updated": source_timestamp,
        "schema_version": TRUSTED_PRICING_CACHE_SCHEMA_VERSION,
        "plan_id": plan_id,
        "deployment_id": deployment.get("deployment_id", ""),
        "status": (
            "Trusted cache generated from IBM Global Catalog pricing. "
            "Exact totals are used only for uniquely mapped linear metrics."
        ),
    }
    return _static_catalog_with_catalog_rates(metadata, metrics, rates, unmapped)


def write_catalog_cache(catalog, cache_path=DEFAULT_CACHE_PATH):
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": catalog.get("metadata", {}).get(
            "schema_version", TRUSTED_PRICING_CACHE_SCHEMA_VERSION
        ),
        "profiles": catalog.get("profiles", []),
        "storage_tier_rates": catalog.get(
            "storage_tier_rates", DEFAULT_STORAGE_TIER_RATES
        ),
        "billing_dimension_rates": catalog.get("billing_dimension_rates", {}),
        "catalog_metrics": catalog.get("catalog_metrics", []),
        "unmapped_catalog_metrics": catalog.get("unmapped_catalog_metrics", []),
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
        f"status={metadata.get('pricing_status', 'unknown')}",
    ]
    if metadata.get("last_updated"):
        parts.append(f"updated={metadata['last_updated']}")
    return " | ".join(parts)
