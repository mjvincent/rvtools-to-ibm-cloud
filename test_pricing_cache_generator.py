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


def sample_live_catalog():
    return {
        "profiles": [
            {
                "name": "bx2-2x8",
                "cpu": 2,
                "ram": 8,
                "hourly": 0.114,
                "pricing_source": "live-profile-static-price",
                "pricing_confidence": "profile-live-price-static",
                "family": "bx2",
            }
        ],
        "storage_tier_rates": {"3iops-tier": 0.10},
        "metadata": {
            "mode": "live",
            "source": "ibm-vpc-profile-api",
            "confidence": "profile-live-price-static",
            "region": "us-south",
            "last_updated": "2026-05-14T00:00:00+00:00",
            "status": "Live IBM profile discovery succeeded",
        },
    }


def test_build_trusted_cache_sets_expected_metadata():
    with patch(
        "scripts.generate_pricing_cache.get_ibmcloud_api_key",
        return_value="test-key",
    ), patch(
        "scripts.generate_pricing_cache.discover_live_catalog",
        return_value=sample_live_catalog(),
    ):
        cache = build_trusted_cache(region="us-south", env_file=".env")

    assert cache["metadata"]["mode"] == "cached"
    assert cache["metadata"]["source"] == TRUSTED_CACHE_SOURCE
    assert cache["metadata"]["confidence"] == TRUSTED_CACHE_CONFIDENCE
    assert cache["profiles"][0]["pricing_source"] == TRUSTED_CACHE_SOURCE
    assert cache["profiles"][0]["pricing_confidence"] == TRUSTED_CACHE_CONFIDENCE
    assert "exact IBM billing catalog pricing is not claimed" in cache["metadata"]["status"]


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


def test_missing_api_key_exits_cleanly():
    stderr = io.StringIO()
    with patch(
        "scripts.generate_pricing_cache.get_ibmcloud_api_key",
        return_value="",
    ), redirect_stderr(stderr):
        exit_code = main(["--dry-run"])

    assert exit_code == 1
    assert "IBMCLOUD_API_KEY was not found" in stderr.getvalue()


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


if __name__ == "__main__":
    test_build_trusted_cache_sets_expected_metadata()
    test_dry_run_does_not_write_cache_file()
    test_output_path_is_honored()
    test_missing_api_key_exits_cleanly()
    print("pricing cache generator tests ok")
