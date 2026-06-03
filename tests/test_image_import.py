"""Snapshot tests for Image Import Planning UI and export.

Tests cover:
- Image grouping logic (VMs grouped by source image)
- Bulk status assignment UI
- Export CSV generation using image_import_export()
- Summary metrics (total images, VMs, import progress)
"""
import json
import pandas as pd
from handoff import image_import_export
from models import MigrationVm
from streamlit_app.image_import import (
    apply_bulk_import_status,
    import_image_import_status,
)


def test_image_grouping_single_image_single_vm(assert_matches_snapshot):
    """Test image grouping when single source image has one VM."""
    vm = MigrationVm(
        vm_key="vm-001",
        vm_name="app-01",
        power_state="poweredOn",
        source_ip="10.0.1.10",
        network="app-net",
        guest_os="Linux",
        ibm_profile="bx2-2x8",
        storage_tier="5iops-tier",
        subnet="subnet-id",
        security_group="sg-id",
        disk_count=1,
        total_storage_gb=100,
    )

    # Build groups from VMs (simulating UI grouping logic)
    groups = {}
    for migration_vm in [vm]:
        source_image = migration_vm.original_specs or migration_vm.vm_name
        entry = groups.setdefault(source_image, {"vms": [], "owners": set()})
        entry["vms"].append(migration_vm)

    # Format as table display
    rows = []
    for source in sorted(groups.keys()):
        entry = groups[source]
        count = len(entry["vms"])
        owners = "; ".join(sorted(entry["owners"])) if entry["owners"] else ""
        rows.append({
            "Source Image": source,
            "Count of VMs": count,
            "Owners": owners,
        })

    result = json.dumps(rows, indent=2) + "\n"
    assert_matches_snapshot("image_grouping_single_image_single_vm.json", result)


def test_apply_bulk_import_status_preserves_existing_fields():
    state = {
        "RHEL-8": {
            "target_catalog_id": "catalog-1",
            "import_status": "Pending",
            "estimated_import_time": "2h",
            "notes": "keep",
        },
        "Windows-2022": {"import_status": "Pending"},
    }

    updated = apply_bulk_import_status(state, ["RHEL-8"], "Imported")

    assert updated["RHEL-8"] == {
        "target_catalog_id": "catalog-1",
        "import_status": "Imported",
        "estimated_import_time": "2h",
        "notes": "keep",
    }
    assert updated["Windows-2022"] == {"import_status": "Pending"}
    assert state["RHEL-8"]["import_status"] == "Pending"


def test_import_image_import_status_updates_source_images():
    imported_df = pd.DataFrame([
        {
            "Source Image": "RHEL-8",
            "Target Catalog ID": "catalog-1",
            "Import Status": "Imported",
            "Estimated Import Time": "2h",
            "Notes": "ready",
        },
        {
            "Source Image": "TOTAL",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
    ])

    updated, result = import_image_import_status(
        imported_df,
        {"Windows-2022": {"import_status": "Pending"}},
    )

    assert result == {"applied": 1, "skipped": 1}
    assert updated["RHEL-8"] == {
        "target_catalog_id": "catalog-1",
        "import_status": "Imported",
        "estimated_import_time": "2h",
        "notes": "ready",
    }
    assert updated["Windows-2022"] == {"import_status": "Pending"}


def test_image_grouping_single_image_multiple_vms(assert_matches_snapshot):
    """Test image grouping when single source image has multiple VMs."""
    vms = [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            power_state="poweredOn",
            source_ip="10.0.1.10",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-2x8",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=1,
            total_storage_gb=100,
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-02",
            power_state="poweredOn",
            source_ip="10.0.1.20",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=2,
            total_storage_gb=200,
        ),
    ]

    # Build groups from VMs
    groups = {}
    for migration_vm in vms:
        source_image = migration_vm.original_specs or migration_vm.vm_name
        entry = groups.setdefault(source_image, {"vms": [], "owners": set()})
        entry["vms"].append(migration_vm)

    # Format as table display
    rows = []
    for source in sorted(groups.keys()):
        entry = groups[source]
        count = len(entry["vms"])
        owners = ""
        rows.append({
            "Source Image": source,
            "Count of VMs": count,
            "Owners": owners,
        })

    result = json.dumps(rows, indent=2) + "\n"
    assert_matches_snapshot("image_grouping_single_image_multiple_vms.json", result)


def test_image_grouping_multiple_images(assert_matches_snapshot):
    """Test image grouping with multiple source images and VMs."""
    vms = [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            power_state="poweredOn",
            source_ip="10.0.1.10",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-2x8",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=1,
            total_storage_gb=100,
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-02",
            power_state="poweredOn",
            source_ip="10.0.1.20",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=2,
            total_storage_gb=200,
        ),
        MigrationVm(
            vm_key="vm-003",
            vm_name="db-01",
            power_state="poweredOn",
            source_ip="10.0.2.10",
            network="db-net",
            guest_os="Linux",
            ibm_profile="bx2-8x32",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=3,
            total_storage_gb=500,
        ),
    ]

    # Build groups from VMs
    groups = {}
    for migration_vm in vms:
        source_image = migration_vm.original_specs or migration_vm.vm_name
        entry = groups.setdefault(source_image, {"vms": [], "owners": set()})
        entry["vms"].append(migration_vm)

    # Format as table display
    rows = []
    for source in sorted(groups.keys()):
        entry = groups[source]
        count = len(entry["vms"])
        owners = ""
        rows.append({
            "Source Image": source,
            "Count of VMs": count,
            "Owners": owners,
        })

    result = json.dumps(rows, indent=2) + "\n"
    assert_matches_snapshot("image_grouping_multiple_images.json", result)


def test_image_grouping_with_owners(assert_matches_snapshot):
    """Test image grouping correctly aggregates multiple owners."""
    # Build a dataframe and extract VM models
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Owner": "Alice Smith",
            "Original Specs": "RHEL-8",
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Owner": "Bob Johnson",
            "Original Specs": "RHEL-8",
        },
        {
            "VM Key": "vm-003",
            "VM Name": "app-03",
            "Owner": "Charlie Davis",
            "Original Specs": "RHEL-8",
        },
    ])

    # Simulate grouping logic from app.py
    groups = {}
    for _, r in df.iterrows():
        source = r.get("Original Specs") or r.get("VM Name")
        entry = groups.setdefault(source, {"vms": [], "owners": set()})
        entry["vms"].append(r)
        owner = r.get("Owner") or ""
        if owner:
            entry["owners"].add(owner)

    # Format as table display
    rows = []
    for source in sorted(groups.keys()):
        entry = groups[source]
        count = len(entry["vms"])
        owners = "; ".join(sorted(entry["owners"])) if entry["owners"] else ""
        rows.append({
            "Source Image": source,
            "Count of VMs": count,
            "Owners": owners,
        })

    result = json.dumps(rows, indent=2) + "\n"
    assert_matches_snapshot("image_grouping_with_owners.json", result)


def test_bulk_status_assignment_pending(assert_matches_snapshot):
    """Test bulk status assignment: select multiple images and apply 'Pending' status."""
    # Create initial image import planning table
    df_images = pd.DataFrame([
        {
            "Source Image": "RHEL-8",
            "Count of VMs": 3,
            "Owners": "Alice Smith; Bob Johnson; Charlie Davis",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
        {
            "Source Image": "RHEL-9",
            "Count of VMs": 2,
            "Owners": "Eve Wilson",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
        {
            "Source Image": "Ubuntu-22.04",
            "Count of VMs": 1,
            "Owners": "Frank Miller",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
    ])

    # Simulate bulk assignment: select first two images and apply 'Pending' status
    selected_images = ["RHEL-8", "RHEL-9"]
    bulk_status = "Pending"

    # Apply status update
    mask = df_images["Source Image"].isin(selected_images)
    df_images.loc[mask, "Import Status"] = bulk_status

    result = df_images.to_json(orient="records", indent=2)
    assert_matches_snapshot("bulk_status_assignment_pending.json", result)


def test_bulk_status_assignment_scheduled(assert_matches_snapshot):
    """Test bulk status assignment: apply 'Scheduled' status to selected images."""
    # Create initial image import planning table
    df_images = pd.DataFrame([
        {
            "Source Image": "RHEL-8",
            "Count of VMs": 3,
            "Owners": "Alice Smith; Bob Johnson; Charlie Davis",
            "Target Catalog ID": "ibm-rhel8-v1",
            "Import Status": "Pending",
            "Estimated Import Time": "2 hours",
            "Notes": "",
        },
        {
            "Source Image": "RHEL-9",
            "Count of VMs": 2,
            "Owners": "Eve Wilson",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
        {
            "Source Image": "Ubuntu-22.04",
            "Count of VMs": 1,
            "Owners": "Frank Miller",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
    ])

    # Simulate bulk assignment: select all and apply 'Scheduled' status
    selected_images = ["RHEL-8", "RHEL-9", "Ubuntu-22.04"]
    bulk_status = "Scheduled"

    # Apply status update
    mask = df_images["Source Image"].isin(selected_images)
    df_images.loc[mask, "Import Status"] = bulk_status

    result = df_images.to_json(orient="records", indent=2)
    assert_matches_snapshot("bulk_status_assignment_scheduled.json", result)


def test_bulk_status_assignment_imported(assert_matches_snapshot):
    """Test bulk status assignment: mark images as 'Imported'."""
    # Create initial image import planning table with various statuses
    df_images = pd.DataFrame([
        {
            "Source Image": "RHEL-8",
            "Count of VMs": 3,
            "Owners": "Alice Smith; Bob Johnson; Charlie Davis",
            "Target Catalog ID": "ibm-rhel8-v1",
            "Import Status": "Scheduled",
            "Estimated Import Time": "2 hours",
            "Notes": "Scheduled for Monday morning",
        },
        {
            "Source Image": "RHEL-9",
            "Count of VMs": 2,
            "Owners": "Eve Wilson",
            "Target Catalog ID": "ibm-rhel9-v2",
            "Import Status": "Pending",
            "Estimated Import Time": "1.5 hours",
            "Notes": "",
        },
        {
            "Source Image": "Ubuntu-22.04",
            "Count of VMs": 1,
            "Owners": "Frank Miller",
            "Target Catalog ID": "",
            "Import Status": "",
            "Estimated Import Time": "",
            "Notes": "",
        },
    ])

    # Simulate bulk assignment: select first two and mark as imported
    selected_images = ["RHEL-8", "RHEL-9"]
    bulk_status = "Imported"

    # Apply status update
    mask = df_images["Source Image"].isin(selected_images)
    df_images.loc[mask, "Import Status"] = bulk_status

    result = df_images.to_json(orient="records", indent=2)
    assert_matches_snapshot("bulk_status_assignment_imported.json", result)


def test_export_csv_single_image_single_vm(assert_matches_snapshot):
    """Test CSV export with single source image and one VM."""
    vm = MigrationVm(
        vm_key="vm-001",
        vm_name="app-01",
        power_state="poweredOn",
        source_ip="10.0.1.10",
        network="app-net",
        guest_os="Linux",
        ibm_profile="bx2-2x8",
        storage_tier="5iops-tier",
        subnet="subnet-id",
        security_group="sg-id",
        disk_count=1,
        total_storage_gb=100,
    )

    csv_text = image_import_export([vm])
    assert_matches_snapshot("image_import_export_single_vm.csv", csv_text)


def test_export_csv_multiple_vms_single_image(assert_matches_snapshot):
    """Test CSV export with single source image and multiple VMs."""
    vms = [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            power_state="poweredOn",
            source_ip="10.0.1.10",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-2x8",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=1,
            total_storage_gb=100,
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-02",
            power_state="poweredOn",
            source_ip="10.0.1.20",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=2,
            total_storage_gb=200,
        ),
    ]

    csv_text = image_import_export(vms)
    assert_matches_snapshot("image_import_export_multiple_vms_single_image.csv", csv_text)


def test_export_csv_multiple_images(assert_matches_snapshot):
    """Test CSV export with multiple source images and VMs."""
    vms = [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            power_state="poweredOn",
            source_ip="10.0.1.10",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-2x8",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=1,
            total_storage_gb=100,
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-02",
            power_state="poweredOn",
            source_ip="10.0.1.20",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=2,
            total_storage_gb=200,
        ),
        MigrationVm(
            vm_key="vm-003",
            vm_name="db-01",
            power_state="poweredOn",
            source_ip="10.0.2.10",
            network="db-net",
            guest_os="Linux",
            ibm_profile="bx2-8x32",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=3,
            total_storage_gb=500,
        ),
    ]

    csv_text = image_import_export(vms)
    assert_matches_snapshot("image_import_export_multiple_images.csv", csv_text)


def test_export_csv_with_import_status(assert_matches_snapshot):
    """Test CSV export with import status mapping."""
    vms = [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            power_state="poweredOn",
            source_ip="10.0.1.10",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-2x8",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=1,
            total_storage_gb=100,
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-02",
            power_state="poweredOn",
            source_ip="10.0.1.20",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=2,
            total_storage_gb=200,
        ),
    ]

    # Provide import status mapping
    image_import_status = {
        "app-01": {
            "target_catalog_id": "ibm-app-v1",
            "import_status": "Scheduled",
            "estimated_import_time": "2 hours",
            "notes": "Scheduled for Monday",
        },
        "app-02": {
            "target_catalog_id": "ibm-app-v1",
            "import_status": "Pending",
            "estimated_import_time": "",
            "notes": "",
        },
    }

    csv_text = image_import_export(vms, image_import_status)
    assert_matches_snapshot("image_import_export_with_status.csv", csv_text)


def test_export_csv_with_partial_status(assert_matches_snapshot):
    """Test CSV export when only some images have status data."""
    vms = [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            power_state="poweredOn",
            source_ip="10.0.1.10",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-2x8",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=1,
            total_storage_gb=100,
        ),
        MigrationVm(
            vm_key="vm-002",
            vm_name="app-02",
            power_state="poweredOn",
            source_ip="10.0.1.20",
            network="app-net",
            guest_os="Linux",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            subnet="subnet-id",
            security_group="sg-id",
            disk_count=2,
            total_storage_gb=200,
        ),
    ]

    # Only provide status for first image
    image_import_status = {
        "app-01": {
            "target_catalog_id": "ibm-app-v1",
            "import_status": "Imported",
            "estimated_import_time": "2 hours",
            "notes": "Successfully imported",
        },
    }

    csv_text = image_import_export(vms, image_import_status)
    assert_matches_snapshot("image_import_export_with_partial_status.csv", csv_text)


def test_summary_metrics_single_image_single_vm(assert_matches_snapshot):
    """Test summary metrics for single image with one VM."""
    vm = MigrationVm(
        vm_key="vm-001",
        vm_name="app-01",
        power_state="poweredOn",
        source_ip="10.0.1.10",
        network="app-net",
        guest_os="Linux",
        ibm_profile="bx2-2x8",
        storage_tier="5iops-tier",
        subnet="subnet-id",
        security_group="sg-id",
        disk_count=1,
        total_storage_gb=100,
    )

    # Group VMs
    groups = {}
    for migration_vm in [vm]:
        source_image = migration_vm.original_specs or migration_vm.vm_name
        entry = groups.setdefault(source_image, {"vms": []})
        entry["vms"].append(migration_vm)

    # Calculate metrics
    total_images = len(groups)
    total_vms = sum(len(entry["vms"]) for entry in groups.values())

    metrics = {
        "total_images": total_images,
        "total_vms": total_vms,
        "images_pending": 0,
        "images_scheduled": 0,
        "images_imported": 0,
        "images_failed": 0,
    }

    result = json.dumps(metrics, indent=2) + "\n"
    assert_matches_snapshot("summary_metrics_single_image_single_vm.json", result)


def test_summary_metrics_multiple_images_with_status(assert_matches_snapshot):
    """Test summary metrics for multiple images with various import statuses."""
    # Create sample image import table
    df_images = pd.DataFrame([
        {
            "Source Image": "RHEL-8",
            "Count of VMs": 3,
            "Import Status": "Imported",
        },
        {
            "Source Image": "RHEL-9",
            "Count of VMs": 2,
            "Import Status": "Scheduled",
        },
        {
            "Source Image": "Ubuntu-22.04",
            "Count of VMs": 1,
            "Import Status": "Pending",
        },
        {
            "Source Image": "Windows-2022",
            "Count of VMs": 2,
            "Import Status": "Failed",
        },
    ])

    # Calculate metrics
    total_images = len(df_images)
    total_vms = df_images["Count of VMs"].sum()
    images_pending = len(df_images[df_images["Import Status"] == "Pending"])
    images_scheduled = len(df_images[df_images["Import Status"] == "Scheduled"])
    images_imported = len(df_images[df_images["Import Status"] == "Imported"])
    images_failed = len(df_images[df_images["Import Status"] == "Failed"])

    metrics = {
        "total_images": int(total_images),
        "total_vms": int(total_vms),
        "images_pending": int(images_pending),
        "images_scheduled": int(images_scheduled),
        "images_imported": int(images_imported),
        "images_failed": int(images_failed),
    }

    result = json.dumps(metrics, indent=2) + "\n"
    assert_matches_snapshot("summary_metrics_multiple_images_with_status.json", result)


def test_summary_metrics_import_progress(assert_matches_snapshot):
    """Test summary metrics showing import progress percentage."""
    # Create sample image import table
    df_images = pd.DataFrame([
        {
            "Source Image": "RHEL-8",
            "Count of VMs": 3,
            "Import Status": "Imported",
        },
        {
            "Source Image": "RHEL-9",
            "Count of VMs": 2,
            "Import Status": "Imported",
        },
        {
            "Source Image": "Ubuntu-22.04",
            "Count of VMs": 1,
            "Import Status": "Pending",
        },
        {
            "Source Image": "Windows-2022",
            "Count of VMs": 4,
            "Import Status": "Scheduled",
        },
    ])

    # Calculate metrics including progress
    total_images = len(df_images)
    total_vms = df_images["Count of VMs"].sum()
    images_imported = len(df_images[df_images["Import Status"] == "Imported"])
    vms_imported = df_images[df_images["Import Status"] == "Imported"]["Count of VMs"].sum()

    import_progress = (vms_imported / total_vms * 100) if total_vms > 0 else 0

    metrics = {
        "total_images": int(total_images),
        "total_vms": int(total_vms),
        "images_imported": int(images_imported),
        "vms_imported": int(vms_imported),
        "import_progress_percent": round(import_progress, 1),
    }

    result = json.dumps(metrics, indent=2) + "\n"
    assert_matches_snapshot("summary_metrics_import_progress.json", result)
