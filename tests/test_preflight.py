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
    sample_vm_record["Boot Disk GB"] = 300
    sample_vm_record["Readiness Reasons"] = "Boot disk exceeds IBM Cloud custom image 250 GB limit"

    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    assert has_blockers(findings)
    assert "readiness" in _categories(findings)
    image_blocker = next(finding for finding in findings if finding.category == "readiness")
    assert image_blocker.quick_fix_type == "exclude_vm"
    assert image_blocker.fix_location == "Readiness tab > Image Readiness"
    assert "250 GB" in image_blocker.constraint
    assert "Boot Disk GB: 300" in image_blocker.current_value


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
    storage_blocker = next(finding for finding in findings if finding.category == "storage")
    assert storage_blocker.quick_fix_type == "storage_tier"
    assert storage_blocker.valid_options == ("3iops-tier", "5iops-tier", "10iops-tier")
    assert storage_blocker.recommended_option == "5iops-tier"
    assert storage_blocker.field == "Override Storage Tier"


def test_preflight_blank_profile_includes_catalog_quick_fix(sample_vm_record):
    sample_vm_record["IBM Profile"] = ""
    sample_vm_record["Override Profile"] = ""

    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}, {"name": "cx2-4x8"}],
    )

    profile_blocker = next(finding for finding in findings if finding.category == "profile")
    assert profile_blocker.quick_fix_type == "profile"
    assert profile_blocker.valid_options == ("bx2-2x8", "cx2-4x8")
    assert profile_blocker.recommended_option == "bx2-2x8"


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
    assert "Fix Location" in rows[0]
    assert "Suggested Action" in rows[0]
    assert "Valid Options" in rows[0]
    assert payload["summary"]["total"] == len(findings)
    assert "fix_location" not in payload["findings"][0]
    assert "Fix Location" in payload["findings"][0]
