import csv
import io
import json

from handoff import (
    generate_pricing_diagnostics_csv,
    generate_pricing_diagnostics_json,
)


def test_pricing_diagnostics_exports_catalog_mapping(sample_vm_record):
    catalog = {
        "billing_dimension_rates": {
            "compute_core_hourly": 0.04,
            "memory_gb_hourly": 0.01,
        },
        "unmapped_catalog_metrics": [
            {
                "dimension": "storage_3iops-tier_monthly",
                "reason": "multiple matching catalog metrics",
            }
        ],
        "catalog_metrics": [
            {
                "deployment_id": "plan-1:dal10",
                "deployment_location": "dal10",
                "deployment_region": "us-south",
            }
        ],
        "metadata": {
            "mode": "cached",
            "source": "ibm-global-catalog",
            "confidence": "cached_catalog",
            "pricing_status": "cached_catalog",
            "region": "us-south",
            "country": "USA",
            "currency": "USD",
            "last_updated": "2026-05-14T00:00:00+00:00",
        },
    }

    json_payload = json.loads(
        generate_pricing_diagnostics_json(catalog, [sample_vm_record])
    )
    csv_rows = list(csv.DictReader(io.StringIO(
        generate_pricing_diagnostics_csv(catalog, [sample_vm_record])
    )))

    assert json_payload["metadata"]["deployment_location"] == "dal10"
    assert json_payload["billing_dimension_rates"]["compute_core_hourly"] == 0.04
    assert json_payload["unmapped_catalog_metrics"][0]["reason"] == (
        "multiple matching catalog metrics"
    )
    assert csv_rows[0]["Pricing Status"] == "static_fallback"
    assert "compute_core_hourly=0.04" in csv_rows[0]["Mapped Billing Dimensions"]
    assert "storage_3iops-tier_monthly" in csv_rows[0]["Unmapped Catalog Metrics"]
