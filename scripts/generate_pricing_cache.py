#!/usr/bin/env python3
"""Generate a trusted IBM VPC pricing cache for the Streamlit app."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog_pricing import (  # noqa: E402
    DEFAULT_CACHE_PATH,
    discover_live_catalog,
    get_ibmcloud_api_key,
    write_catalog_cache,
)


TRUSTED_CACHE_SOURCE = "trusted-cache-generator"
TRUSTED_CACHE_CONFIDENCE = "profile-live-price-static"


class PricingCacheError(RuntimeError):
    """Raised when the cache cannot be safely generated."""


def build_trusted_cache(region="us-south", env_file=".env"):
    """Build a cache payload from live profile discovery and mapped prices."""
    api_key = get_ibmcloud_api_key(env_file)
    if not api_key:
        raise PricingCacheError(
            "IBMCLOUD_API_KEY was not found in the environment or env file."
        )

    catalog = discover_live_catalog(region, api_key=api_key)
    metadata = catalog.get("metadata", {})
    if metadata.get("source") != "ibm-vpc-profile-api":
        status = metadata.get("status", "unknown error")
        raise PricingCacheError(
            f"Live IBM VPC profile discovery did not succeed: {status}"
        )

    profiles = catalog.get("profiles", [])
    if not profiles:
        raise PricingCacheError("Live IBM VPC profile discovery returned no profiles.")

    trusted_profiles = []
    for profile in profiles:
        trusted = dict(profile)
        trusted["pricing_source"] = TRUSTED_CACHE_SOURCE
        trusted["pricing_confidence"] = TRUSTED_CACHE_CONFIDENCE
        trusted_profiles.append(trusted)

    return {
        "profiles": trusted_profiles,
        "storage_tier_rates": catalog.get("storage_tier_rates", {}),
        "metadata": {
            "mode": "cached",
            "source": TRUSTED_CACHE_SOURCE,
            "confidence": TRUSTED_CACHE_CONFIDENCE,
            "region": region,
            "last_updated": metadata.get("last_updated", ""),
            "status": (
                "Trusted cache generated from live IBM VPC profile discovery "
                "with existing static mapped prices; exact IBM billing catalog "
                "pricing is not claimed."
            ),
        },
    }


def cache_summary(catalog):
    """Return a concise human-readable cache summary."""
    metadata = catalog.get("metadata", {})
    profiles = catalog.get("profiles", [])
    priced_count = len([profile for profile in profiles if profile.get("hourly", 0) > 0])
    return (
        f"profiles={len(profiles)} | priced={priced_count} | "
        f"region={metadata.get('region', '')} | "
        f"confidence={metadata.get('confidence', '')}"
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate data/ibm_vpc_pricing_cache.json from IBM VPC profile discovery."
    )
    parser.add_argument(
        "--region",
        default="us-south",
        help="IBM Cloud region to discover profiles from. Default: us-south",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_CACHE_PATH),
        help=f"Cache output path. Default: {DEFAULT_CACHE_PATH}",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Environment file to load IBMCLOUD_API_KEY from. Default: .env",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate discovery and print a summary without writing the cache.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        catalog = build_trusted_cache(region=args.region, env_file=args.env_file)
    except PricingCacheError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(cache_summary(catalog))
    if args.dry_run:
        print("Dry run complete; cache file was not written.")
        return 0

    path = write_catalog_cache(catalog, args.output)
    print(f"Wrote pricing cache to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
