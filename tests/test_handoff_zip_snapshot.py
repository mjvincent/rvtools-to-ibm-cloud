"""
Snapshot test for complete handoff ZIP structure and contents.

Validates that the final ZIP handoff package contains:
- Manifest with complete schema
- All CSV exports (decision audit, remediation tracker, image import)
- Terraform files
- Mapping files
"""

import json
import zipfile
from io import BytesIO

import pytest

from catalog_pricing import CatalogPricing
from handoff import (
    decision_audit_export,
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_migration_manifest,
    generate_migration_runbook,
    generate_nic_mapping_csv,
    generate_partition_mapping_csv,
    generate_pricing_diagnostics_csv,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
    image_import_export,
    remediation_tracker_export,
)
from models import MigrationVm
from sizing import propose_and_rank_profiles
from terraform_renderer import render_terraform_root, render_terraform_storage, render_terraform_vsis


@pytest.fixture
def complete_test_vms():
    """Create comprehensive test VMs for snapshot comparison"""
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
def test_pricing_catalog():
    """Create test pricing catalog"""
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


@pytest.fixture
def test_remediation_tracker():
    """Create test remediation tracker"""
    return {
        "vm-001_VMware Tools": {
            "status": "In Progress",
            "due_date": "2025-02-15",
            "notes": "Install scheduled",
            "owner": "alice@example.com",
        },
    }


@pytest.fixture
def test_image_import_status():
    """Create test image import status"""
    return {
        "centos-7-template": {
            "target_id": "r001-12345678",
            "status": "Imported",
            "estimated_time": 120,
            "notes": "Imported successfully",
        },
    }


def test_handoff_zip_file_structure(
    complete_test_vms, test_pricing_catalog, test_remediation_tracker, test_image_import_status
):
    """
    Snapshot test for handoff ZIP file contents.
    Verifies all expected files are present with correct structure.
    """

    # Create ZIP buffer
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add manifest
        manifest = generate_migration_manifest(complete_test_vms, test_pricing_catalog)
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Add Priority 2 exports
        zf.writestr(
            "decision-audit.csv",
            decision_audit_export(complete_test_vms, test_pricing_catalog),
        )
        zf.writestr(
            "remediation-backlog.csv",
            remediation_tracker_export(complete_test_vms, test_remediation_tracker),
        )
        zf.writestr(
            "image-import-plan.csv",
            image_import_export(complete_test_vms, test_image_import_status),
        )

        # Add other mappings
        zf.writestr("vm-mapping.csv", generate_vm_mapping_csv(complete_test_vms))
        zf.writestr("disk-mapping.csv", generate_disk_mapping_csv(complete_test_vms))
        zf.writestr("nic-mapping.csv", generate_nic_mapping_csv(complete_test_vms))
        zf.writestr(
            "readiness-findings.csv",
            generate_readiness_findings_csv(complete_test_vms),
        )
        zf.writestr(
            "pricing-diagnostics.csv",
            generate_pricing_diagnostics_csv(test_pricing_catalog, complete_test_vms),
        )

        # Add Terraform files
        zf.writestr("terraform/main.tf", render_terraform_root(complete_test_vms))
        zf.writestr("terraform/vsis.tf", render_terraform_vsis(complete_test_vms))
        zf.writestr("terraform/storage.tf", render_terraform_storage(complete_test_vms))

    # Verify ZIP contents
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        file_list = zf.namelist()

        # Verify core files are present
        assert "manifest.json" in file_list
        assert "decision-audit.csv" in file_list
        assert "remediation-backlog.csv" in file_list
        assert "image-import-plan.csv" in file_list
        assert "vm-mapping.csv" in file_list
        assert "terraform/main.tf" in file_list

        # Verify manifest schema
        manifest_content = json.loads(zf.read("manifest.json").decode())
        assert "virtual_machines" in manifest_content
        assert "decision_audit_summary" in manifest_content
        assert "remediation_tracker_summary" in manifest_content
        assert "image_import_summary" in manifest_content

        # Verify each VM in manifest has wave metadata
        for vm in manifest_content["virtual_machines"]:
            assert "wave" in vm
            assert "owner" in vm
            assert "application" in vm
            assert "source_image" in vm

        # Verify CSV files have content
        decision_csv = zf.read("decision-audit.csv").decode()
        assert "VM Key" in decision_csv or len(decision_csv) > 0

        remediation_csv = zf.read("remediation-backlog.csv").decode()
        assert "Status" in remediation_csv or len(remediation_csv) > 0

        image_csv = zf.read("image-import-plan.csv").decode()
        assert "Source Image" in image_csv or len(image_csv) > 0


def test_handoff_zip_manifest_schema(complete_test_vms, test_pricing_catalog):
    """
    Snapshot test for manifest JSON schema validation.
    """

    manifest = generate_migration_manifest(complete_test_vms, test_pricing_catalog)

    # Snapshot the schema structure
    schema = {
        "root_keys": list(manifest.keys()),
        "vm_count": len(manifest.get("virtual_machines", [])),
        "vm_sample_keys": (
            list(manifest["virtual_machines"][0].keys())
            if manifest.get("virtual_machines")
            else []
        ),
        "decision_audit_keys": list(manifest.get("decision_audit_summary", {}).keys()),
        "remediation_tracker_keys": list(
            manifest.get("remediation_tracker_summary", {}).keys()
        ),
        "image_import_keys": list(manifest.get("image_import_summary", {}).keys()),
    }

    # Verify structure
    assert schema["root_keys"]
    assert schema["vm_count"] == 2
    assert "wave" in schema["vm_sample_keys"]
    assert "owner" in schema["vm_sample_keys"]
    assert "application" in schema["vm_sample_keys"]
    assert "source_image" in schema["vm_sample_keys"]

    # Decision audit summary keys
    assert "total_pricing_impact" in schema["decision_audit_keys"]
    assert "profile_override_count" in schema["decision_audit_keys"]

    # Remediation tracker summary keys
    assert "total_blockers" in schema["remediation_tracker_keys"]
    assert "blocker_counts_by_status" in schema["remediation_tracker_keys"]

    # Image import summary keys
    assert "total_images" in schema["image_import_keys"]
    assert "import_status_breakdown" in schema["image_import_keys"]


def test_handoff_zip_csv_headers(complete_test_vms, test_pricing_catalog, test_remediation_tracker, test_image_import_status):
    """
    Snapshot test for CSV header validation.
    """

    # Decision audit headers
    decision_csv = decision_audit_export(complete_test_vms, test_pricing_catalog)
    decision_header = decision_csv.split("\n")[0]
    assert "VM Key" in decision_header or "vm_key" in decision_header.lower()
    assert len(decision_csv.split("\n")) > 1

    # Remediation tracker headers
    remediation_csv = remediation_tracker_export(
        complete_test_vms, test_remediation_tracker
    )
    remediation_header = remediation_csv.split("\n")[0]
    assert "Status" in remediation_header
    assert len(remediation_csv.split("\n")) > 1

    # Image import headers
    image_csv = image_import_export(complete_test_vms, test_image_import_status)
    image_header = image_csv.split("\n")[0]
    assert "Source Image" in image_header
    assert len(image_csv.split("\n")) > 1


def test_priority2_data_integrity(
    complete_test_vms, test_pricing_catalog, test_remediation_tracker, test_image_import_status
):
    """
    Snapshot test for Priority 2 data round-trip validation.
    Verify data is preserved through parsing → export → manifest pipeline.
    """

    # Original VM data
    vm_001 = complete_test_vms[0]
    original_wave = vm_001.wave
    original_owner = vm_001.owner
    original_app = vm_001.application

    # Generate all exports
    manifest = generate_migration_manifest(complete_test_vms, test_pricing_catalog)
    decision_audit = decision_audit_export(complete_test_vms, test_pricing_catalog)
    remediation_export = remediation_tracker_export(
        complete_test_vms, test_remediation_tracker
    )
    image_export = image_import_export(complete_test_vms, test_image_import_status)

    # Verify data in manifest
    manifest_vm = next(
        (vm for vm in manifest["virtual_machines"] if vm["vm_key"] == "vm-001"), None
    )
    assert manifest_vm is not None
    assert manifest_vm["wave"] == original_wave
    assert manifest_vm["owner"] == original_owner
    assert manifest_vm["application"] == original_app

    # Verify data in decision audit
    assert vm_001.vm_name in decision_audit
    assert original_owner in decision_audit
    assert original_app in decision_audit

    # Verify data in remediation export
    assert vm_001.vm_name in remediation_export or "vm-001" in remediation_export

    # Verify data in image export
    assert vm_001.source_image in image_export
