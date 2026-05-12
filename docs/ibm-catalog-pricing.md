# IBM Catalog Pricing

## Purpose
IBM Catalog Pricing mode controls where the app gets profile and price data for IBM Cloud VPC sizing estimates.

The app separates profile discovery from pricing confidence. This prevents the tool from treating a VPC profile name, such as `bx2-2x8`, as though it were automatically a Global Catalog pricing artifact name.

## Pricing Modes
### Static Fallback
Uses bundled profile and storage prices. This is the safest default for demos, offline work, and environments without IBM credentials.

### Cached IBM Catalog
Loads `data/ibm_vpc_pricing_cache.json` when present. Use this mode when a trusted pricing sync process has generated a cache file.

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
* `Profile Hourly`

## Handoff Fields
Pricing metadata is included in:
* `migration-manifest.json`
* `vm-mapping.csv`
* Business case CSV exports from the table

## Cache Format
The optional cache file uses JSON:

```json
{
  "source": "trusted-cache-generator",
  "confidence": "cached-exact",
  "region": "us-south",
  "last_updated": "2026-05-12T00:00:00+00:00",
  "profiles": [
    {
      "name": "bx2-2x8",
      "cpu": 2,
      "ram": 8,
      "hourly": 0.114,
      "pricing_source": "trusted-cache-generator",
      "pricing_confidence": "cached-exact"
    }
  ],
  "storage_tier_rates": {
    "3iops-tier": 0.10,
    "5iops-tier": 0.13,
    "10iops-tier": 0.17
  }
}
```

## Environment Variables
Live mode looks for:

```bash
IBMCLOUD_API_KEY=...
```

## Limitations
The app does not yet perform exact Global Catalog billing dimension resolution. IBM Cloud VPC profile names are discovered from the VPC API, while pricing confidence is tracked separately.

Treat estimates as planning guidance unless `Pricing Confidence` comes from a trusted exact pricing cache or a future verified IBM pricing mapper.
