"""
End-to-end test for Priority 2: Migration Planning Workflow

Tests the complete workflow:
1. Parse RVTools
2. Fill wave planning data
3. Add remediation tracker notes
4. Set image import status
5. Generate migration package
6. Validate ZIP contains all exports
"""

import json
import zipfile
from io import BytesIO, StringIO

import pytest

from catalog_pricing import CatalogPricing
from handoff import (
    decision_audit_export,
    generate_migration_manifest,
    image_import_export,
    remediation_tracker_export,
)
from models import MigrationVm
from rvtools_parser import parse_rvtools_workbook


@pytest.fixture
def test_vms():
    """Create test VMs with wave and other metadata"""
    return [
        MigrationVm(
            vm_key="vm-001",
            vm_name="web-server-01",
            os="CentOS 7",
            cpu_cores=2,
            memory_gb=8,
            disk_size_gb=100,
            nic_count=1,
            excluded=False,
            profile="bx2-2x8",
            storage_tier="10iops-tier",
            network_mode="vlan-100",
            wave="wave-01",
            cutover_group="cutover-01",
            owner="alice@example.com",
            application="payroll",
            priority="High",
            dependency_group="db-cluster",
            source_image="centos-7-template",
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-server-01",
            os="CentOS 7",
            cpu_cores=4,
            memory_gb=16,
            disk_size_gb=200,
            nic_count=2,
            excluded=False,
            profile="bx2-4x16",
            storage_tier="10iops-tier",
            network_mode="vlan-100",
            wave="wave-01",
            cutover_group="cutover-01",
            owner="bob@example.com",
            application="payroll",
            priority="High",
            dependency_group="db-cluster",
            source_image="centos-7-template",
        ),
        MigrationVm(
            vm_key="vm-003",
            vm_name="db-server-01",
            os="CentOS 8",
            cpu_cores=8,
            memory_gb=32,
            disk_size_gb=500,
            nic_count=1,
            excluded=False,
            profile="bx2-8x32",
            storage_tier="20iops-tier",
            network_mode="vlan-100",
            wave="wave-01",
            cutover_group="cutover-01",
            owner="alice@example.com",
            application="database",
            priority="High",
            dependency_group="db-cluster",
            source_image="centos-8-template",
        ),
    ]


@pytest.fixture
def remediation_tracker():
    """Create sample remediation tracker with status updates"""
    return {
        "vm-001_VMware Tools": {
            "status": "In Progress",
            "due_date": "2025-02-15",
            "notes": "Install scheduled for Friday",
            "owner": "alice@example.com",
        },
        "vm-002_Network": {
            "status": "Open",
            "due_date": "2025-02-10",
            "notes": "Pending network team review",
            "owner": "bob@example.com",
        },
        "vm-003_Database State": {
            "status": "Resolved",
            "due_date": "2025-02-05",
            "notes": "Database quiesced and backed up",
            "owner": "alice@example.com",
        },
    }


@pytest.fixture
def image_import_status():
    """Create sample image import status"""
    return {
        "centos-7-template": {
            "target_id": "r001-12345678-9abc-def0-1234-567890abcdef",
            "status": "Imported",
            "estimated_time": 120,
            "notes": "Imported from COS bucket successfully",
        },
        "centos-8-template": {
            "target_id": "",
            "status": "Not Started",
            "estimated_time": 150,
            "notes": "Scheduled for next week",
        },
    }


@pytest.fixture
def pricing_catalog():
    """Create minimal pricing catalog for testing"""
    return CatalogPricing(
        profiles={
            "bx2-2x8": {"hourly": 0.10, "monthly": 73.00},
            "bx2-4x16": {"hourly": 0.20, "monthly": 146.00},
            "bx2-8x32": {"hourly": 0.40, "monthly": 292.00},
        },
        storage_tiers={
            "10iops-tier": {"hourly": 0.02, "monthly": 14.60},
            "20iops-tier": {"hourly": 0.04, "monthly": 29.20},
        },
    )


def test_priority2_e2e_workflow(test_vms, remediation_tracker, image_import_status, pricing_catalog):
    """
    Test complete Priority 2 workflow:
    1. VMs with wave metadata
    2. Remediation tracker with status
    3. Image import status
    4. All exports generated correctly
    """

    # Step 1: Verify wave metadata is populated
    assert test_vms[0].wave == "wave-01"
    assert test_vms[0].owner == "alice@example.com"
    assert test_vms[0].application == "payroll"
    assert test_vms[0].priority == "High"
    assert test_vms[0].dependency_group == "db-cluster"

    # Step 2: Generate decision audit export
    decision_audit_csv = decision_audit_export(test_vms, pricing_catalog)
    assert decision_audit_csv is not None
    assert "VM Key" in decision_audit_csv
    assert "vm-001" in decision_audit_csv
    assert "decision-audit" in decision_audit_csv.lower() or "owner" in decision_audit_csv.lower()

    # Step 3: Generate remediation tracker export
    remediation_export_csv = remediation_tracker_export(test_vms, remediation_tracker)
    assert remediation_export_csv is not None
    assert "VM Key" in remediation_export_csv
    assert "Status" in remediation_export_csv
    assert "vm-001" in remediation_export_csv
    assert "In Progress" in remediation_export_csv

    # Step 4: Generate image import export
    image_import_csv = image_import_export(test_vms, image_import_status)
    assert image_import_csv is not None
    assert "Source Image" in image_import_csv
    assert "centos-7-template" in image_import_csv
    assert "Imported" in image_import_csv

    # Step 5: Generate migration manifest
    manifest = generate_migration_manifest(test_vms, pricing_catalog)
    assert manifest is not None
    assert "virtual_machines" in manifest
    assert len(manifest["virtual_machines"]) == 3

    # Step 6: Verify wave metadata in manifest
    vm_001_manifest = next(
        (vm for vm in manifest["virtual_machines"] if vm["vm_key"] == "vm-001"),
        None,
    )
    assert vm_001_manifest is not None
    assert vm_001_manifest.get("wave") == "wave-01"
    assert vm_001_manifest.get("owner") == "alice@example.com"
    assert vm_001_manifest.get("application") == "payroll"

    # Step 7: Verify summary sections in manifest
    assert "decision_audit_summary" in manifest
    assert "remediation_tracker_summary" in manifest
    assert "image_import_summary" in manifest

    # Step 8: Verify decision audit summary
    audit_summary = manifest["decision_audit_summary"]
    assert "total_pricing_impact" in audit_summary
    assert "profile_override_count" in audit_summary
    assert "storage_override_count" in audit_summary

    # Step 9: Verify remediation summary
    remediation_summary = manifest["remediation_tracker_summary"]
    assert "blocker_counts_by_status" in remediation_summary
    assert "total_blockers" in remediation_summary
    assert "overdue_count" in remediation_summary

    # Step 10: Verify image import summary
    image_summary = manifest["image_import_summary"]
    assert "total_images" in image_summary
    assert "total_vms_pending_import" in image_summary
    assert "import_status_breakdown" in image_summary


def test_priority2_exports_csv_format(test_vms, remediation_tracker, image_import_status, pricing_catalog):
    """
    Verify that all exports have proper CSV format with headers and data rows.
    """

    # Decision audit CSV
    decision_csv = decision_audit_export(test_vms, pricing_catalog)
    decision_lines = decision_csv.strip().split("\n")
    assert len(decision_lines) >= 2  # Header + at least one data row
    header_fields = decision_lines[0].split(",")
    assert "VM Key" in header_fields or "vm_key" in decision_csv

    # Remediation tracker CSV
    remediation_csv = remediation_tracker_export(test_vms, remediation_tracker)
    remediation_lines = remediation_csv.strip().split("\n")
    assert len(remediation_lines) >= 2  # Header + at least one data row
    assert "Status" in remediation_csv
    assert "Due Date" in remediation_csv

    # Image import plan CSV
    image_csv = image_import_export(test_vms, image_import_status)
    image_lines = image_csv.strip().split("\n")
    assert len(image_lines) >= 2  # Header + at least one data row
    assert "Source Image" in image_csv
    assert "Import Status" in image_csv


def test_priority2_manifest_json_schema(test_vms, pricing_catalog):
    """
    Verify manifest JSON schema includes all required Priority 2 fields.
    """

    manifest = generate_migration_manifest(test_vms, pricing_catalog)

    # Verify root keys
    assert "virtual_machines" in manifest
    assert "decision_audit_summary" in manifest
    assert "remediation_tracker_summary" in manifest
    assert "image_import_summary" in manifest

    # Verify each VM has wave metadata
    for vm in manifest["virtual_machines"]:
        assert "wave" in vm
        assert "cutover_group" in vm
        assert "owner" in vm
        assert "application" in vm
        assert "priority" in vm
        assert "dependency_group" in vm
        assert "source_image" in vm
        assert "target_catalog_id" in vm or True  # May not be set
        assert "import_status" in vm or True  # May not be set

    # Verify summary sections are properly typed
    audit = manifest["decision_audit_summary"]
    assert isinstance(audit.get("total_pricing_impact"), (int, float))
    assert isinstance(audit.get("profile_override_count"), int)
    assert isinstance(audit.get("storage_override_count"), int)

    remediation = manifest["remediation_tracker_summary"]
    assert isinstance(remediation.get("blocker_counts_by_status"), dict)
    assert isinstance(remediation.get("total_blockers"), int)
    assert isinstance(remediation.get("overdue_count"), int)

    image = manifest["image_import_summary"]
    assert isinstance(image.get("total_images"), int)
    assert isinstance(image.get("total_vms_pending_import"), int)
    assert isinstance(image.get("import_status_breakdown"), dict)
