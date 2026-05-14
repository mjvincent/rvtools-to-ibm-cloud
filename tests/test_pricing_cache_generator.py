import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts.generate_pricing_cache import (
    TRUSTED_CACHE_CONFIDENCE,
    TRUSTED_CACHE_SOURCE,
    build_trusted_cache,
    main,
)


def test_build_trusted_cache_sets_expected_metadata(sample_live_catalog):
    sample_live_catalog["metadata"]["source"] = TRUSTED_CACHE_SOURCE
    sample_live_catalog["metadata"]["confidence"] = TRUSTED_CACHE_CONFIDENCE
    sample_live_catalog["metadata"]["pricing_status"] = "exact_catalog"
    sample_live_catalog["profiles"][0]["pricing_source"] = TRUSTED_CACHE_SOURCE
    sample_live_catalog["profiles"][0]["pricing_confidence"] = TRUSTED_CACHE_CONFIDENCE
    sample_live_catalog["profiles"][0]["pricing_status"] = "exact_catalog"
    with patch(
        "scripts.generate_pricing_cache.get_ibmcloud_api_key",
        return_value="test-key",
    ), patch(
        "scripts.generate_pricing_cache.fetch_power_virtual_server_pricing",
        return_value=sample_live_catalog,
    ):
        cache = build_trusted_cache(region="us-south", env_file=".env")

    assert cache["metadata"]["mode"] == "cached"
    assert cache["metadata"]["source"] == TRUSTED_CACHE_SOURCE
    assert cache["metadata"]["confidence"] == TRUSTED_CACHE_CONFIDENCE
    assert cache["profiles"][0]["pricing_source"] == TRUSTED_CACHE_SOURCE
    assert cache["profiles"][0]["pricing_confidence"] == TRUSTED_CACHE_CONFIDENCE


def test_dry_run_does_not_write_cache_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cache.json"
        stdout = io.StringIO()
        with patch(
            "scripts.generate_pricing_cache.build_trusted_cache",
            return_value=build_sample_cache(),
        ), redirect_stdout(stdout):
            exit_code = main([
                "--output", str(output_path),
                "--dry-run",
            ])

        assert exit_code == 0
        assert not output_path.exists()
        assert "Dry run complete" in stdout.getvalue()


def test_output_path_is_honored():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "custom-cache.json"
        with patch(
            "scripts.generate_pricing_cache.build_trusted_cache",
            return_value=build_sample_cache(),
        ):
            exit_code = main(["--output", str(output_path)])

        assert exit_code == 0
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert data["source"] == TRUSTED_CACHE_SOURCE
        assert data["profiles"][0]["name"] == "bx2-2x8"


def test_pricing_fetch_failure_exits_cleanly():
    stderr = io.StringIO()
    with patch(
        "scripts.generate_pricing_cache.get_ibmcloud_api_key",
        return_value="test-key",
    ), patch(
        "scripts.generate_pricing_cache.fetch_power_virtual_server_pricing",
        side_effect=RuntimeError("network unavailable"),
    ), redirect_stderr(stderr):
        exit_code = main(["--dry-run"])

    assert exit_code == 1
    assert "IBM Global Catalog pricing fetch failed" in stderr.getvalue()



def build_sample_cache():
    return {
        "profiles": [
            {
                "name": "bx2-2x8",
                "cpu": 2,
                "ram": 8,
                "hourly": 0.114,
                "pricing_source": TRUSTED_CACHE_SOURCE,
                "pricing_confidence": TRUSTED_CACHE_CONFIDENCE,
                "family": "bx2",
            }
        ],
        "storage_tier_rates": {"3iops-tier": 0.10},
        "metadata": {
            "mode": "cached",
            "source": TRUSTED_CACHE_SOURCE,
            "confidence": TRUSTED_CACHE_CONFIDENCE,
            "region": "us-south",
            "last_updated": "2026-05-14T00:00:00+00:00",
            "status": "Trusted cache generated for tests.",
        },
    }
