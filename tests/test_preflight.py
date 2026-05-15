import csv
import io
import json

from preflight import (
    generate_preflight_report_csv,
    generate_preflight_report_json,
    has_blockers,
    run_package_preflight,
    summarize_preflight,
)


def _categories(findings):
    return {finding.category for finding in findings}


def test_preflight_blocks_empty_scope():
    findings = run_package_preflight([], [], "us-south")

    assert has_blockers(findings)
    assert findings[0].category == "scope"


def test_preflight_flags_blocked_readiness(sample_vm_record):
    sample_vm_record["Image Readiness"] = "Blocked"

    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    assert has_blockers(findings)
    assert "readiness" in _categories(findings)


def test_preflight_detects_invalid_duplicate_and_overlapping_cidrs(sample_vm_record):
    networks = [
        {"name": "app-net", "cidr": "10.0.1.0/24", "cidr_key": "app"},
        {"name": "db-net", "cidr": "10.0.1.128/25", "cidr_key": "db"},
        {"name": "bad-net", "cidr": "not-a-cidr", "cidr_key": "bad"},
    ]

    findings = run_package_preflight(
        [sample_vm_record],
        networks,
        "us-south",
        custom_cidrs={
            "app": "10.0.1.0/24",
            "db": "10.0.1.0/24",
            "bad": "not-a-cidr",
        },
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    messages = " ".join(finding.message for finding in findings)
    assert "Invalid CIDR" in messages
    assert "duplicates" in messages
    assert "overlaps" in messages


def test_preflight_detects_duplicate_terraform_resource_names(sample_vm_record):
    duplicate_vm = {**sample_vm_record, "VM Name": "app_01"}

    findings = run_package_preflight(
        [sample_vm_record, duplicate_vm],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    assert "terraform_names" in _categories(findings)
    assert has_blockers(findings)


def test_preflight_warns_for_image_profile_region_and_unknown_catalog(sample_vm_record):
    sample_vm_record["Override Profile"] = "unsupported-2x8"

    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    categories = _categories(findings)
    assert "custom_image" in categories
    assert "profile" in categories
    assert "profile_region" in categories


def test_preflight_blocks_unsupported_storage_tier(sample_vm_record):
    sample_vm_record["Override Storage Tier"] = "gold-tier"

    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    assert has_blockers(findings)
    assert "storage" in _categories(findings)


def test_preflight_reports_are_exportable(sample_vm_record):
    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    summary = summarize_preflight(findings)
    rows = list(csv.DictReader(io.StringIO(generate_preflight_report_csv(findings))))
    payload = json.loads(generate_preflight_report_json(findings))

    assert summary["warnings"] >= 1
    assert rows[0]["Severity"]
    assert payload["summary"]["total"] == len(findings)
