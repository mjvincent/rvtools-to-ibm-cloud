import csv
import io
import json

from preflight import (
    FIX_APP,
    FIX_OPERATOR,
    FIX_SOURCE,
    generate_preflight_report_csv,
    generate_preflight_report_json,
    has_blockers,
    preflight_fix_category,
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
    assert preflight_fix_category(image_blocker) == FIX_SOURCE
    assert image_blocker.fix_location == "Readiness tab > Image Readiness"
    assert "250 GB" in image_blocker.constraint
    assert "Boot Disk GB: 300" in image_blocker.current_value


def test_preflight_explains_migration_readiness_source_side_fixes(sample_vm_record):
    sample_vm_record["Migration Readiness"] = "Blocked"
    sample_vm_record["Migration Readiness Reasons"] = (
        "Mounted CD/DVD media: CD/DVD drive 1: ISO datastore/image.iso; "
        "VMware Tools status: toolsOld"
    )
    sample_vm_record["Readiness Findings"] = [
        {
            "finding_type": "Mounted CD/DVD media",
            "severity": "Blocked",
            "source_tab": "vCD",
            "evidence": "CD/DVD drive 1: ISO datastore/image.iso",
            "recommended_action": "Disconnect ISO media",
        },
        {
            "finding_type": "VMware Tools status",
            "severity": "Review",
            "source_tab": "vTools",
            "evidence": (
                "toolsOld, upgradeable=Yes, heartbeat=appStatusGray, "
                "operation_ready=True"
            ),
            "recommended_action": "Update VMware Tools",
        },
        {
            "finding_type": "RVTools health warning",
            "severity": "Review",
            "source_tab": "vHealth",
            "evidence": "Warning: VM Tools are out of date",
            "recommended_action": "Review RVTools health finding",
        },
    ]

    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    migration_blocker = next(
        finding for finding in findings
        if finding.category == "readiness"
        and "Migration readiness" in finding.message
    )
    assert migration_blocker.quick_fix_type == "exclude_vm"
    assert "Mounted CD/DVD media" in migration_blocker.message
    assert "Source tabs: vCD, vHealth, vTools" in migration_blocker.message
    assert "Fix outside app" in migration_blocker.current_value
    assert "disconnect or remove the CD/DVD ISO" in migration_blocker.current_value
    assert "update/start VMware Tools" in migration_blocker.current_value
    assert "vHealth warning" in migration_blocker.current_value
    assert "This app cannot disconnect media" in migration_blocker.constraint
    assert "Fix in app: exclude this VM" in migration_blocker.suggested_action
    assert preflight_fix_category(migration_blocker) == FIX_SOURCE


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


def test_preflight_blocks_invalid_ssh_source_cidr(sample_vm_record):
    findings = run_package_preflight(
        [sample_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        ssh_source_cidr="not-a-cidr",
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    ssh_finding = next(
        finding for finding in findings
        if finding.category == "security_group"
    )
    assert ssh_finding.severity == "blocker"
    assert ssh_finding.fix_location == "Export > SSH Source CIDR"
    assert preflight_fix_category(ssh_finding) == FIX_APP


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
    assert preflight_fix_category(storage_blocker) == FIX_APP


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
    sample_vm_record["Migration Readiness"] = "Blocked"
    sample_vm_record["Readiness Findings"] = [
        {
            "finding_type": "Mounted CD/DVD media",
            "severity": "Blocked",
            "source_tab": "vCD",
            "evidence": "CD/DVD drive 1: ISO datastore/image.iso",
            "recommended_action": "Disconnect ISO media",
        }
    ]
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
    assert "Fix Category" in rows[0]
    assert "Fix Location" in rows[0]
    assert "Suggested Action" in rows[0]
    assert "Valid Options" in rows[0]
    assert payload["summary"]["total"] == len(findings)
    assert "Fix Category" in payload["findings"][0]
    assert "fix_location" not in payload["findings"][0]
    assert "Fix Location" in payload["findings"][0]
    assert "Fix outside app" in generate_preflight_report_json(findings)


def test_preflight_fix_categories_route_common_findings(sample_vm_record):
    sample_vm_record["Custom Image ID"] = "replace-with-imported-image-id"
    disconnected_vm = {
        **sample_vm_record,
        "VM Name": "no-nic",
        "Network Details": [{"connected": False, "network": "app-net"}],
    }

    findings = run_package_preflight(
        [sample_vm_record, disconnected_vm],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        custom_cidrs={"app-net": "not-a-cidr"},
        catalog_profiles=[{"name": "bx2-2x8"}],
    )

    image_warning = next(
        finding for finding in findings
        if finding.quick_fix_type == "image_placeholder"
    )
    cidr_blocker = next(
        finding for finding in findings
        if finding.category == "cidr"
    )
    nic_blocker = next(
        finding for finding in findings
        if finding.category == "network_mapping"
        and finding.subject == "no-nic"
    )

    assert preflight_fix_category(image_warning) == FIX_OPERATOR
    assert preflight_fix_category(cidr_blocker) == FIX_APP
    assert preflight_fix_category(nic_blocker) == FIX_SOURCE
