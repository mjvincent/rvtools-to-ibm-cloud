#!/usr/bin/env python3
"""Generate a trusted IBM pricing cache for the Streamlit app."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog_pricing import (  # noqa: E402
    DEFAULT_CACHE_PATH,
    fetch_power_virtual_server_pricing,
    get_ibmcloud_api_key,
    write_catalog_cache,
)


TRUSTED_CACHE_SOURCE = "ibm-global-catalog"
TRUSTED_CACHE_CONFIDENCE = "exact_catalog"


class PricingCacheError(RuntimeError):
    """Raised when the cache cannot be safely generated."""


def build_trusted_cache(
    region="us-south",
    env_file=".env",
    country="USA",
    currency="USD",
    fetch_json=None,
):
    """Build a cache payload from IBM Global Catalog pricing dimensions."""
    api_key = get_ibmcloud_api_key(env_file)
    try:
        catalog = fetch_power_virtual_server_pricing(
            region=region,
            country=country,
            currency=currency,
            api_key=api_key,
            fetch_json=fetch_json,
        )
    except Exception as exc:
        raise PricingCacheError(f"IBM Global Catalog pricing fetch failed: {exc}") from exc

    metadata = catalog.get("metadata", {})
    if metadata.get("source") != TRUSTED_CACHE_SOURCE:
        raise PricingCacheError("IBM Global Catalog pricing did not produce a trusted cache.")

    profiles = catalog.get("profiles", [])
    if not profiles:
        raise PricingCacheError("IBM Global Catalog pricing returned no profile records.")

    catalog["metadata"] = {
        **metadata,
        "mode": "cached",
        "source": TRUSTED_CACHE_SOURCE,
        "confidence": metadata.get("confidence", TRUSTED_CACHE_CONFIDENCE),
        "region": region,
        "country": country,
        "currency": currency,
    }
    return catalog


def cache_summary(catalog):
    """Return a concise human-readable cache summary."""
    metadata = catalog.get("metadata", {})
    profiles = catalog.get("profiles", [])
    priced_count = len([profile for profile in profiles if profile.get("hourly", 0) > 0])
    exact_count = len([
        profile for profile in profiles
        if profile.get("pricing_status") == "exact_catalog"
    ])
    exact_dimension_count = len(catalog.get("billing_dimension_rates", {}))
    unmapped_count = len(catalog.get("unmapped_catalog_metrics", []))
    return (
        f"profiles={len(profiles)} | priced={priced_count} | exact={exact_count} | "
        f"exact_dimensions={exact_dimension_count} | unmapped={unmapped_count} | "
        f"region={metadata.get('region', '')} | "
        f"confidence={metadata.get('confidence', '')}"
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate data/ibm_vpc_pricing_cache.json from IBM Global Catalog pricing."
    )
    parser.add_argument(
        "--region",
        default="us-south",
        help="IBM Cloud region/deployment to fetch pricing for. Default: us-south",
    )
    parser.add_argument(
        "--country",
        default="USA",
        help="Catalog pricing country code. Default: USA",
    )
    parser.add_argument(
        "--currency",
        default="USD",
        help="Catalog pricing currency. Default: USD",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_CACHE_PATH),
        help=f"Cache output path. Default: {DEFAULT_CACHE_PATH}",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional environment file for existing IBMCLOUD_API_KEY workflows.",
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
        catalog = build_trusted_cache(
            region=args.region,
            env_file=args.env_file,
            country=args.country,
            currency=args.currency,
        )
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
