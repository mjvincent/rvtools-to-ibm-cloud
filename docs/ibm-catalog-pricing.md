# IBM Catalog Pricing

## Purpose
IBM Catalog Pricing mode controls where the app gets profile and price data for IBM Cloud VPC sizing estimates.

The app separates profile discovery from pricing confidence. This prevents the tool from treating a VPC profile name, such as `bx2-2x8`, as though it were automatically a Global Catalog pricing artifact name.

## Pricing Modes
### Static Fallback
Uses bundled profile and storage prices. This is the safest default for demos, offline work, and environments without IBM credentials.

### Cached IBM Catalog
Loads `data/ibm_vpc_pricing_cache.json` when present. Use this mode when a trusted pricing sync process has generated a cache file.

Generate the supported cache file with:

```bash
python scripts/generate_pricing_cache.py --region us-south
```

The generator uses IBM Global Catalog pricing endpoints for the public Power Virtual Server plan, normalizes deployment metrics for the selected region/country/currency, and maps only uniquely matched linear billing dimensions into the cache. For common IBM regions, it selects the corresponding Power VS deployment location, such as `us-south` to `dal10`/`dal12`. It writes `source=ibm-global-catalog` and `confidence=exact_catalog` only when exact dimensions are available; ambiguous dimensions remain visible as `unmapped_catalog_metrics` and fall back to bundled estimates.

Use `--dry-run` to validate credentials and profile discovery without writing a file:

```bash
python scripts/generate_pricing_cache.py --region us-south --dry-run
```

Use `--output` to write a cache somewhere other than `data/ibm_vpc_pricing_cache.json`, `--country`/`--currency` for a supported catalog amount, and `--env-file` to preserve compatibility with existing credential workflows. Global Catalog cache generation is standalone and does not require Streamlit at runtime.

### Live IBM Profile Discovery
Uses the IBM Cloud VPC API to discover available instance profiles for the selected region when `IBMCLOUD_API_KEY` is available.

Live mode currently uses mapped static pricing for profiles where a known fallback price exists. It labels confidence as `profile-live-price-static`. This is intentional: profile discovery is live, but exact catalog pricing is not claimed unless it can be safely resolved.

## UI Fields
The Streamlit sidebar shows:
* `Pricing Mode`
* Pricing mode/source/confidence summary
* Status text explaining whether static, cached, or live fallback behavior is active

The VM table includes:
* `Pricing Source`
* `Pricing Confidence`
* `Pricing Last Updated`
* `Pricing Status`
* `Profile Hourly`

`Pricing Status` is one of `exact_catalog`, `cached_catalog`, `static_fallback`, or `unmapped`. Exact catalog pricing is used only for dimensions that map to one positive, currently effective, linear Global Catalog metric.

## Handoff Fields
Pricing metadata is included in:
* `migration-manifest.json`
* `vm-mapping.csv`
* Business case CSV exports from the table

## Cache Format
The optional cache file uses JSON:

```json
{
  "source": "ibm-global-catalog",
  "schema_version": 2,
  "confidence": "exact_catalog",
  "pricing_status": "exact_catalog",
  "region": "us-south",
  "country": "USA",
  "currency": "USD",
  "last_updated": "2026-05-12T00:00:00+00:00",
  "profiles": [
    {
      "name": "bx2-2x8",
      "cpu": 2,
      "ram": 8,
      "hourly": 0.114,
      "pricing_source": "ibm-global-catalog",
      "pricing_confidence": "exact_catalog",
      "pricing_status": "exact_catalog"
    }
  ],
  "storage_tier_rates": {
    "3iops-tier": 0.10,
    "5iops-tier": 0.13,
    "10iops-tier": 0.17
  },
  "billing_dimension_rates": {
    "compute_core_hourly": 0.04,
    "memory_gb_hourly": 0.01
  },
  "catalog_metrics": [],
  "unmapped_catalog_metrics": []
}
```

## Environment Variables
Live mode looks for `IBMCLOUD_API_KEY` in the running process environment first. If it is not present, the app also attempts to load a local `.env` file from the repository root.

```bash
IBMCLOUD_API_KEY=...
```

After creating or changing `.env`, restart Streamlit so the running process reloads the value. The standalone cache generator also reads `IBMCLOUD_API_KEY` from the process environment or the env file passed with `--env-file`.

## Limitations
Exact catalog pricing means exact against the public IBM Global Catalog metrics that the mapper can uniquely resolve for the selected region, country, and currency. Invoices can still differ because of account-specific discounts, subscriptions, taxes, billing-cycle proration, reserved terms, or private offers.

Unsupported, duplicate, expired, zero-priced, missing, or non-linear metrics are not folded into exact totals. They are preserved in `unmapped_catalog_metrics`, and the app continues to use the static fallback for those dimensions.

The old scripts under `experiments/pricing/` are retained as research artifacts. Use `scripts/generate_pricing_cache.py` as the supported cache-generation path.
