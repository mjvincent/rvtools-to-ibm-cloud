import csv
import io
import json
import zipfile

from handoff import (
    build_cutover_readiness_rows,
    generate_cutover_readiness_csv,
    generate_migration_manifest,
    summarize_cutover_readiness,
)
from models import MigrationVm
from streamlit_app.package_builder import build_terraform_bundle


def _vm(**overrides):
    record = {
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Network": "app-net",
        "Guest OS": "Linux",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "5iops-tier",
        "Subnet": "module.networking.app_net_id",
        "Security Group": "module.networking.app_net_sg_id",
        "Disk Count": 1,
        "Total Storage GB": 100,
        "Original Specs": "rhel-8-template",
        "Wave": "wave-01",
        "Cutover Group": "cg-app",
        "Owner": "app-team",
        "Application": "orders",
        "Image Readiness": "Ready",
        "Migration Readiness": "Ready",
        "Memory Readiness": "Ready",
        "Network Readiness": "Ready",
    }
    record.update(overrides)
    return record


def _csv_rows(csv_text):
    return list(csv.DictReader(io.StringIO(csv_text)))


def test_cutover_readiness_rows_flag_blockers():
    rows = build_cutover_readiness_rows(
        [
            _vm(
                **{
                    "Owner": "",
                    "Migration Readiness": "Blocked",
                    "Migration Readiness Reasons": "Snapshot sprawl",
                }
            )
        ],
        remediation_tracker={
            "vm-001::0": {
                "status": "In Progress",
                "blocker_type": "VMware Tools",
                "blocker_description": "Update tools",
            }
        },
        image_import_status={
            "rhel-8-template": {"import_status": "Pending"}
        },
    )

    categories = {row["Blocker Category"] for row in rows}
    assert categories == {
        "Missing Planning",
        "Readiness Blocker",
        "Unresolved Remediation",
        "Image Import Pending",
    }
    assert {row["Cutover Status"] for row in rows} == {"Blocked"}


def test_cutover_readiness_summary_counts_by_wave():
    rows = build_cutover_readiness_rows(
        [
            _vm(),
            _vm(
                **{
                    "VM Key": "vm-002",
                    "VM Name": "db-01",
                    "Wave": "wave-01",
                    "Cutover Group": "",
                    "Original Specs": "windows-2022-template",
                }
            ),
        ],
        image_import_status={
            "rhel-8-template": {"import_status": "Imported"},
            "windows-2022-template": {"import_status": "Pending"},
        },
    )

    summary = summarize_cutover_readiness(rows, "Wave")

    assert summary == [{
        "Wave": "wave-01",
        "VMs": 2,
        "Ready": 1,
        "Review": 0,
        "Blocked": 1,
        "Missing Planning": 1,
        "Unresolved Remediation": 0,
        "Image Pending": 1,
    }]


def test_cutover_readiness_csv_has_stable_headers():
    csv_text = generate_cutover_readiness_csv(
        [_vm()],
        image_import_status={"rhel-8-template": {"import_status": "Imported"}},
    )
    rows = _csv_rows(csv_text)

    assert list(rows[0]) == [
        "VM Name",
        "Wave",
        "Cutover Group",
        "Owner",
        "Application",
        "Cutover Status",
        "Blocker Category",
        "Blocker Reason",
        "Recommended Next Action",
    ]
    assert rows[0]["Cutover Status"] == "Ready"


def test_migration_vm_preserves_wave_planning_title_fields():
    migration_vm = MigrationVm.from_record(_vm())

    assert migration_vm.wave == "wave-01"
    assert migration_vm.cutover_group == "cg-app"
    assert migration_vm.owner == "app-team"
    assert migration_vm.application == "orders"


def test_manifest_references_cutover_readiness_export():
    manifest = json.loads(generate_migration_manifest([_vm()], {}))

    assert (
        manifest["handoff_files"]["cutover_readiness_csv"]
        == "cutover-readiness.csv"
    )


def test_terraform_bundle_includes_cutover_readiness_csv():
    bundle = build_terraform_bundle(
        [_vm()],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
        True,
        "demo-vpc",
        {},
        "manual",
        "Plain CLI",
        "demo",
        "0.0.0.0/0",
        {
            "mode": "static",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
        },
        {},
        {},
        [],
        {},
        {"rhel-8-template": {"import_status": "Imported"}},
    )

    with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("migration-manifest.json"))
        readiness_rows = _csv_rows(zf.read("cutover-readiness.csv").decode())

    assert "cutover-readiness.csv" in names
    assert (
        manifest["handoff_files"]["cutover_readiness_csv"]
        == "cutover-readiness.csv"
    )
    assert readiness_rows[0]["Cutover Status"] == "Ready"
