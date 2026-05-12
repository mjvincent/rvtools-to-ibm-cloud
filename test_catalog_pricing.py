import json
import os
import tempfile
from pathlib import Path

from catalog_pricing import (
    get_ibmcloud_api_key,
    get_pricing_catalog,
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


if __name__ == "__main__":
    test_static_catalog_preserves_existing_profile_selection()
    test_cached_catalog_loads_profiles_and_pricing_metadata()
    test_live_catalog_without_api_key_falls_back_static()
    test_api_key_can_load_from_dotenv_file()
    print("catalog pricing tests ok")
