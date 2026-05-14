import json
import os
import tempfile
from pathlib import Path

from catalog_pricing import (
    fetch_power_virtual_server_pricing,
    get_ibmcloud_api_key,
    get_pricing_catalog,
    map_catalog_billing_dimensions,
    normalize_catalog_pricing,
    pricing_status_summary,
)
from logic_engine import get_catalog_profiles, map_vmware_to_ibm_vpc


def test_static_catalog_preserves_existing_profile_selection():
    catalog = get_pricing_catalog("static", region="us-south")
    profiles = catalog["profiles"]
    mapping = map_vmware_to_ibm_vpc(
        cpus=2,
        memory=8192,
        usage=40,
        region="us-south",
        threshold=40,
        storage_gb=100,
        tier="3iops-tier",
        memory_is_sizing=True,
        catalog=profiles,
        storage_tier_rates=catalog["storage_tier_rates"],
        pricing_metadata=catalog["metadata"],
    )
    assert mapping["profile"] == "bx2-2x8"
    assert mapping["pricing_confidence"] == "fallback-static"
    assert "bx2-2x8" in get_catalog_profiles(profiles)


def test_cached_catalog_loads_profiles_and_pricing_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "pricing.json"
        cache_path.write_text(json.dumps({
            "source": "unit-test-cache",
            "confidence": "cached-exact",
            "region": "us-south",
            "last_updated": "2026-05-12T00:00:00+00:00",
            "profiles": [
                {
                    "name": "test-2x8",
                    "cpu": 2,
                    "ram": 8,
                    "hourly": 0.12,
                    "pricing_source": "unit-test-cache",
                    "pricing_confidence": "cached-exact",
                }
            ],
            "storage_tier_rates": {"3iops-tier": 0.11},
        }), encoding="utf-8")

        catalog = get_pricing_catalog(
            "cached", region="us-south", cache_path=cache_path
        )
        mapping = map_vmware_to_ibm_vpc(
            cpus=2,
            memory=8192,
            usage=40,
            region="us-south",
            threshold=40,
            storage_gb=100,
            tier="3iops-tier",
            memory_is_sizing=True,
            catalog=catalog["profiles"],
            storage_tier_rates=catalog["storage_tier_rates"],
            pricing_metadata=catalog["metadata"],
        )
        assert mapping["profile"] == "test-2x8"
        assert mapping["compute_cost"] == 87.6
        assert mapping["storage_cost"] == 11.0
        assert mapping["pricing_confidence"] == "cached-exact"
        assert mapping["pricing_status"] == "cached_catalog"
        assert "source=unit-test-cache" in pricing_status_summary(catalog)


def test_live_catalog_without_api_key_falls_back_static():
    catalog = get_pricing_catalog("live", region="us-south", api_key="")
    assert catalog["metadata"]["source"] == "static"
    assert catalog["metadata"]["confidence"] == "fallback-static"
    assert catalog["profiles"]


def test_api_key_can_load_from_dotenv_file():
    old_value = os.environ.pop("IBMCLOUD_API_KEY", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "IBMCLOUD_API_KEY=test-key-from-dotenv\n",
                encoding="utf-8"
            )
            assert get_ibmcloud_api_key(env_path) == "test-key-from-dotenv"
    finally:
        if old_value is not None:
            os.environ["IBMCLOUD_API_KEY"] = old_value



def catalog_pricing_payload(metrics):
    return {
        "deployment_id": "power-plan:us-south",
        "deployment_location": "us-south",
        "deployment_region": "us-south",
        "metrics": metrics,
    }


def linear_metric(metric_id, name, unit_name, price, tier_model="Linear Tier"):
    return {
        "metric_id": metric_id,
        "part_ref": f"part-{metric_id}",
        "tier_model": tier_model,
        "resource_display_name": name,
        "charge_unit": unit_name,
        "charge_unit_name": unit_name,
        "charge_unit_display_name": unit_name,
        "charge_unit_quantity": 1,
        "amounts": [
            {"country": "USA", "currency": "USD", "prices": [{"quantity_tier": 1, "price": price}]}
        ],
        "effective_from": "2026-01-01T00:00:00Z",
        "effective_until": "9999-12-31T00:00:00Z",
    }


def test_catalog_pricing_normalization_preserves_metric_provenance():
    metrics = normalize_catalog_pricing(
        catalog_pricing_payload([
            linear_metric("power-core", "Processor core", "Virtual Processor Core-Hour", 0.04)
        ]),
        plan_id="plan-1",
        country="USA",
        currency="USD",
        source_timestamp="2026-05-14T00:00:00+00:00",
    )

    assert metrics[0].plan_id == "plan-1"
    assert metrics[0].deployment_id == "power-plan:us-south"
    assert metrics[0].metric_id == "power-core"
    assert metrics[0].unit_price == 0.04
    assert metrics[0].country == "USA"
    assert metrics[0].currency == "USD"


def test_catalog_dimension_mapper_requires_unique_linear_positive_match():
    metrics = normalize_catalog_pricing(catalog_pricing_payload([
        linear_metric("power-core", "Processor core", "Virtual Processor Core-Hour", 0.04),
        linear_metric("power-memory", "Memory", "GB-Hour", 0.01),
        linear_metric("storage-3", "Storage 3 IOPS", "GB-Hour", 0.001),
    ]))

    rates, unmapped = map_catalog_billing_dimensions(metrics, storage_tiers=["3iops-tier"])

    assert rates["compute_core_hourly"] == 0.04
    assert rates["memory_gb_hourly"] == 0.01
    assert rates["storage_3iops-tier_monthly"] == 0.001
    assert unmapped == []


def test_catalog_dimension_mapper_marks_duplicate_or_non_linear_unmapped():
    metrics = normalize_catalog_pricing(catalog_pricing_payload([
        linear_metric("power-core-a", "Processor core", "Virtual Processor Core-Hour", 0.04),
        linear_metric("power-core-b", "Processor core", "Virtual Processor Core-Hour", 0.05),
        linear_metric("power-memory", "Memory", "GB-Hour", 0.01, tier_model="Graduated Tier"),
    ]))

    rates, unmapped = map_catalog_billing_dimensions(metrics, storage_tiers=[])

    assert "compute_core_hourly" not in rates
    assert "memory_gb_hourly" not in rates
    reasons = {item["dimension"]: item["reason"] for item in unmapped}
    assert reasons["compute_core_hourly"] == "multiple matching catalog metrics"
    assert reasons["memory_gb_hourly"] == "matching metrics were expired, unpriced, or non-linear"


def test_catalog_dimension_mapper_filters_country_and_currency():
    metric = linear_metric("power-core", "Processor core", "Virtual Processor Core-Hour", 0.04)
    metric["amounts"] = [
        {"country": "CAN", "currency": "CAD", "prices": [{"quantity_tier": 1, "price": 0.06}]}
    ]

    metrics = normalize_catalog_pricing(
        catalog_pricing_payload([metric]), country="USA", currency="USD"
    )

    assert metrics == []


def test_fetch_power_virtual_server_pricing_builds_exact_cache_from_fixture():
    def fake_fetch(url):
        if url.endswith("/plan?_offset=0&_limit=50"):
            return {"resources": [{"id": "plan-1", "metadata": {"pricing": {"type": "Paid"}}}]}
        if url.endswith("/plan-1/pricing/deployment"):
            deployment = catalog_pricing_payload([
                linear_metric("power-core", "Processor core", "Virtual Processor Core-Hour", 0.04),
                linear_metric("power-memory", "Memory", "GB-Hour", 0.01),
                linear_metric("tier3-storage", "HDD Storage 3 IOPS", "GB-Hour", 0.001),
                linear_metric("tier5-storage", "SSD Storage 5 IOPS", "GB-Hour", 0.002),
                linear_metric("tier10-storage", "SSD Storage 10 IOPS", "GB-Hour", 0.003),
            ])
            deployment["deployment_location"] = "dal10"
            deployment["deployment_region"] = "dal10"
            return {"resources": [deployment]}
        raise AssertionError(f"unexpected URL: {url}")

    catalog = fetch_power_virtual_server_pricing(
        region="us-south", fetch_json=fake_fetch, base_url="https://example.test/api/v1"
    )

    assert catalog["metadata"]["pricing_status"] == "exact_catalog"
    assert catalog["profiles"][0]["pricing_confidence"] == "exact_catalog"
    assert catalog["profiles"][0]["hourly"] > 0


def test_partial_catalog_mapping_is_cached_not_exact():
    def fake_fetch(url):
        if url.endswith("/plan?_offset=0&_limit=50"):
            return {"resources": [{"id": "plan-1", "metadata": {"pricing": {"type": "Paid"}}}]}
        if url.endswith("/plan-1/pricing/deployment"):
            deployment = catalog_pricing_payload([
                linear_metric("storage-3", "Storage 3 IOPS", "GB-Hour", 0.001),
            ])
            deployment["deployment_location"] = "dal10"
            deployment["deployment_region"] = "dal10"
            return {"resources": [deployment]}
        raise AssertionError(f"unexpected URL: {url}")

    catalog = fetch_power_virtual_server_pricing(
        region="us-south", fetch_json=fake_fetch, base_url="https://example.test/api/v1"
    )

    assert catalog["metadata"]["pricing_status"] == "cached_catalog"
    assert catalog["metadata"]["confidence"] == "cached_catalog"
    assert catalog["profiles"][0]["pricing_status"] == "static_fallback"


def test_exact_catalog_profile_price_overrides_static_cost():
    profiles = [{
        "name": "exact-2x8",
        "cpu": 2,
        "ram": 8,
        "hourly": 0.16,
        "pricing_source": "ibm-global-catalog",
        "pricing_confidence": "exact_catalog",
        "pricing_status": "exact_catalog",
    }]

    mapping = map_vmware_to_ibm_vpc(
        cpus=2,
        memory=8192,
        usage=40,
        region="us-south",
        threshold=40,
        storage_gb=100,
        tier="3iops-tier",
        memory_is_sizing=True,
        catalog=profiles,
        storage_tier_rates={"3iops-tier": 0.73},
        pricing_metadata={"source": "ibm-global-catalog", "confidence": "exact_catalog", "pricing_status": "exact_catalog"},
    )

    assert mapping["profile"] == "exact-2x8"
    assert mapping["compute_cost"] == 116.8
    assert mapping["storage_cost"] == 73.0
    assert mapping["pricing_status"] == "exact_catalog"


def test_partial_catalog_status_surfaces_when_profile_uses_static_price():
    profiles = [{
        "name": "static-2x8",
        "cpu": 2,
        "ram": 8,
        "hourly": 0.12,
        "pricing_source": "static",
        "pricing_confidence": "fallback-static",
        "pricing_status": "static_fallback",
    }]

    mapping = map_vmware_to_ibm_vpc(
        cpus=2,
        memory=8192,
        usage=40,
        region="us-south",
        threshold=40,
        storage_gb=100,
        tier="3iops-tier",
        memory_is_sizing=True,
        catalog=profiles,
        storage_tier_rates={"3iops-tier": 0.73},
        pricing_metadata={"pricing_status": "cached_catalog"},
    )

    assert mapping["pricing_status"] == "cached_catalog"
