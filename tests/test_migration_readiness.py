import csv
import io
import json

from logic_engine import (
    generate_migration_manifest,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
    make_readiness_finding,
    summarize_migration_readiness,
)


def test_migration_readiness_ready_without_findings():
    summary = summarize_migration_readiness([])
    assert summary["status"] == "Ready"
    assert "No migration readiness blockers" in summary["reasons"]


def test_migration_readiness_review_for_review_findings():
    findings = [
        make_readiness_finding(
            "VMware Tools status",
            "Review",
            "vTools",
            "toolsNotRunning",
            "Update VMware Tools",
        )
    ]
    summary = summarize_migration_readiness(findings)
    assert summary["status"] == "Review"
    assert "VMware Tools status" in summary["reasons"]


def test_migration_readiness_blocked_wins_over_review():
    findings = [
        make_readiness_finding(
            "VMware Tools status",
            "Review",
            "vTools",
            "toolsOld",
            "Update VMware Tools",
        ),
        make_readiness_finding(
            "Mounted CD/DVD media",
            "Blocked",
            "vCD",
            "CD/DVD drive 1: ISO datastore/image.iso",
            "Disconnect ISO media",
        ),
    ]
    summary = summarize_migration_readiness(findings)
    assert summary["status"] == "Blocked"
    assert "Mounted CD/DVD media" in summary["reasons"]


def test_handoff_outputs_include_migration_readiness_fields():
    findings = [
        make_readiness_finding(
            "Active snapshots",
            "Blocked",
            "vSnapshot",
            "1 snapshot(s), 24084.28 MiB total",
            "Remove or consolidate snapshots",
        )
    ]
    vm = {
        "VM Name": "app01",
        "Power State": "poweredOn",
        "Guest OS": "Microsoft Windows Server 2022 (64-bit)",
        "Source IP": "10.0.0.10",
        "Network": "App_Net",
        "Datacenter": "dc1",
        "Cluster": "cluster1",
        "Host": "host1",
        "Disk Count": 1,
        "Total Storage GB": 80,
        "Firmware": "efi",
        "Boot Disk GB": 80,
        "Guest Customization": "cloudbase-init required",
        "Image Readiness": "Ready",
        "Readiness Reasons": "No metadata blockers found",
        "Migration Readiness": "Blocked",
        "Migration Readiness Reasons": "Active snapshots",
        "Readiness Findings": findings,
        "Snapshot Count": 1,
        "Snapshot Size MiB": 24084.28,
        "VMware Tools Status": "toolsOk",
        "Mounted Media": "",
        "USB Devices": 0,
        "Health Warnings": 0,
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "3iops-tier",
        "Subnet": "module.networking.app_net_id",
        "Security Group": "module.networking.app_net_sg_id",
    }

    mapping_rows = list(csv.DictReader(io.StringIO(generate_vm_mapping_csv([vm]))))
    assert mapping_rows[0]["Migration Readiness"] == "Blocked"
    assert mapping_rows[0]["Snapshot Count"] == "1"

    findings_rows = list(
        csv.DictReader(io.StringIO(generate_readiness_findings_csv([vm])))
    )
    assert findings_rows[0]["Severity"] == "Blocked"
    assert findings_rows[0]["Source Tab"] == "vSnapshot"

    manifest = json.loads(generate_migration_manifest([vm], {
        "project_name": "test",
        "target_region": "us-south",
        "target_zone": "us-south-1",
        "vpc_name": "migration-vpc",
    }))
    handoff_files = manifest["handoff_files"]
    assert handoff_files["readiness_findings_csv"] == "readiness-findings.csv"
    migration_readiness = manifest["virtual_machines"][0]["migration_readiness"]
    assert migration_readiness["status"] == "Blocked"
    assert migration_readiness["findings"][0]["finding_type"] == "Active snapshots"
