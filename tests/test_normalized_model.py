import csv
import io
import json

from logic_engine import (
    generate_migration_manifest,
    generate_nic_mapping_csv,
    render_terraform_templates,
)
from models import DiskMapping, MigrationVm, NicMapping, ReadinessFinding


def sample_vm_record():
    return {
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Power State": "poweredOn",
        "Source IP": "10.0.1.10",
        "Network": "app-net",
        "Guest OS": "Red Hat Enterprise Linux 9 (64-bit)",
        "IBM Profile": "bx2-2x8",
        "Override Profile": "",
        "Storage Tier": "5iops-tier",
        "Override Storage Tier": "",
        "Subnet": "module.networking.app_net_id",
        "Security Group": "module.networking.app_net_sg_id",
        "Compute (Mo)": 83.22,
        "Storage (Mo)": 26.0,
        "Monthly Cost": 109.22,
        "Baseline Cost (Mo)": 192.4,
        "Savings (Mo)": 83.18,
        "Pricing Source": "static",
        "Pricing Confidence": "fallback-static",
        "Pricing Last Updated": "2026-05-12T00:00:00+00:00",
        "Pricing Status": "static_fallback",
        "Profile Hourly": 0.114,
        "Disk Count": 2,
        "Data Disk Count": 1,
        "Total Storage GB": 200,
        "Image Readiness": "Review",
        "Readiness Reasons": "Multiple disks detected",
        "Migration Readiness": "Review",
        "Migration Readiness Reasons": "VMware Tools status: toolsOld",
        "Network Readiness": "Ready",
        "Network Readiness Reasons": "No network readiness blockers found",
        "Memory Readiness": "Ready",
        "Memory Readiness Reasons": "No memory pressure",
        "Configured Memory MiB": 8192,
        "Active Memory MiB": 4096,
        "Consumed Memory MiB": 6144,
        "Ballooned Memory MiB": 0,
        "Swapped Memory MiB": 0,
        "Memory Reservation MiB": 0,
        "Memory Limit MiB": -1,
        "Memory Hot Add": "False",
        "Sizing Memory MiB": 8192,
        "Memory Sizing Basis": "preserve-configured-memory",
        "Disk Details": [
            {
                "disk": "Hard disk 1",
                "capacity_gb": 80,
                "is_boot": True,
            },
            {
                "disk": "Hard disk 2",
                "capacity_gb": 120,
                "is_boot": False,
            },
        ],
        "Network Details": [
            {
                "label": "Network adapter 1",
                "network": "app-net",
                "connected": True,
                "ipv4": "10.0.1.10",
                "switch_type": "standard",
                "port_group": "app-net",
                "vlan": "101",
                "backing_source_tab": "vPort",
                "match_confidence": "matched",
            },
            {
                "label": "Network adapter 2",
                "network": "db-net",
                "connected": True,
                "ipv4": "10.0.2.10",
            },
        ],
        "Network Readiness Findings": [],
        "Readiness Findings": [
            {
                "finding_type": "VMware Tools status",
                "severity": "Review",
                "source_tab": "vTools",
                "evidence": "toolsOld",
                "recommended_action": "Update VMware Tools",
            }
        ],
    }


def sample_vm_model():
    return MigrationVm(
        vm_key="vm-001",
        vm_name="app-01",
        power_state="poweredOn",
        source_ip="10.0.1.10",
        network="app-net",
        guest_os="Red Hat Enterprise Linux 9 (64-bit)",
        ibm_profile="bx2-2x8",
        storage_tier="5iops-tier",
        subnet="module.networking.app_net_id",
        security_group="module.networking.app_net_sg_id",
        disk_count=2,
        total_storage_gb=200,
        compute_cost_monthly=83.22,
        storage_cost_monthly=26.0,
        monthly_cost=109.22,
        baseline_cost_monthly=192.4,
        savings_monthly=83.18,
        pricing_source="static",
        pricing_confidence="fallback-static",
        pricing_last_updated="2026-05-12T00:00:00+00:00",
        pricing_status="static_fallback",
        profile_hourly=0.114,
        data_disk_count=1,
        image_readiness="Review",
        readiness_reasons="Multiple disks detected",
        migration_readiness="Review",
        migration_readiness_reasons="VMware Tools status: toolsOld",
        network_readiness="Ready",
        network_readiness_reasons="No network readiness blockers found",
        memory_readiness="Ready",
        memory_readiness_reasons="No memory pressure",
        configured_memory_mib=8192,
        active_memory_mib=4096,
        consumed_memory_mib=6144,
        memory_limit_mib=-1,
        sizing_memory_mib=8192,
        memory_sizing_basis="preserve-configured-memory",
        disks=[
            DiskMapping(disk="Hard disk 1", capacity_gb=80, is_boot=True),
            DiskMapping(disk="Hard disk 2", capacity_gb=120, is_boot=False),
        ],
        nics=[
            NicMapping(
                label="Network adapter 1",
                network="app-net",
                connected=True,
                ipv4="10.0.1.10",
                switch_type="standard",
                port_group="app-net",
                vlan="101",
                backing_source_tab="vPort",
                match_confidence="matched",
            ),
            NicMapping(
                label="Network adapter 2",
                network="db-net",
                connected=True,
                ipv4="10.0.2.10",
            ),
        ],
        readiness_findings=[
            ReadinessFinding(
                finding_type="VMware Tools status",
                severity="Review",
                source_tab="vTools",
                evidence="toolsOld",
                recommended_action="Update VMware Tools",
            )
        ],
    )


def test_model_round_trips_from_legacy_record():
    model = MigrationVm.from_record(sample_vm_record())
    record = model.to_record()

    assert record["VM Name"] == "app-01"
    assert record["Disk Details"][1]["capacity_gb"] == 120
    assert record["Network Details"][1]["network"] == "db-net"
    assert record["Readiness Findings"][0]["source_tab"] == "vTools"
    assert record["Network Readiness"] == "Ready"
    assert record["Network Details"][0]["switch_type"] == "standard"
    assert record["Compute (Mo)"] == 83.22
    assert record["Data Disk Count"] == 1


def test_nested_records_are_canonical_views():
    model = MigrationVm.from_record(sample_vm_record())

    assert model.source.vm_name == "app-01"
    assert model.source.disks[1].disk == "Hard disk 2"
    assert model.target.effective_profile == "bx2-2x8"
    assert model.target.compute_cost_monthly == 83.22
    assert model.pricing.confidence == "fallback-static"
    assert model.image.reasons == "Multiple disks detected"
    assert model.memory.sizing_basis == "preserve-configured-memory"
    assert model.network_status.status == "Ready"
    assert model.migration.findings[0].recommended_action == "Update VMware Tools"


def test_table_boundary_round_trip_preserves_user_edits():
    processed_vm = sample_vm_model()
    table_record = processed_vm.to_record()
    table_record.pop("Disk Details")
    table_record.pop("Network Details")
    table_record.pop("Readiness Findings")
    table_record["Override Profile"] = "cx2-2x4"
    table_record["Override Storage Tier"] = "3iops-tier"

    table_record["Disk Details"] = [disk.to_record() for disk in processed_vm.disks]
    table_record["Network Details"] = [nic.to_record() for nic in processed_vm.nics]
    table_record["Readiness Findings"] = [
        finding.to_record() for finding in processed_vm.readiness_findings
    ]
    edited_vm = MigrationVm.from_record(table_record)

    assert edited_vm.target.effective_profile == "cx2-2x4"
    assert edited_vm.target.effective_storage_tier == "3iops-tier"
    assert edited_vm.source.nics[1].network == "db-net"


def test_exports_accept_normalized_vm_model():
    vm = sample_vm_model()
    manifest = json.loads(
        generate_migration_manifest([vm], {"project_name": "demo"})
    )
    vm_record = manifest["virtual_machines"][0]

    assert vm_record["vm_name"] == "app-01"
    assert vm_record["target"]["data_volumes"][0]["source_disk"] == "Hard disk 2"
    assert vm_record["migration_readiness"]["findings"][0]["source_tab"] == "vTools"
    assert vm_record["assessment"]["pricing"]["confidence"] == "fallback-static"
    assert vm_record["assessment"]["memory_readiness"]["sizing_memory_mib"] == 8192
    assert vm_record["network_readiness"]["status"] == "Ready"


def test_terraform_renderer_accepts_normalized_vm_model():
    files = render_terraform_templates(
        [sample_vm_model()],
        [
            {"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"},
            {"name": "db-net", "vlan": "", "cidr": "10.0.2.0/24"},
        ],
        "us-south",
        "us-south-1",
    )
    vsi_main, storage_main = files[0], files[2]

    assert "app_01_hard_disk_2_vol" in storage_main
    assert 'var.subnet_ids["db_net"]' in vsi_main


def test_nic_csv_accepts_model_and_preserves_roles():
    rows = list(csv.DictReader(io.StringIO(generate_nic_mapping_csv([
        sample_vm_model()
    ]))))

    assert rows[0]["Role"] == "primary"
    assert rows[1]["Role"] == "secondary"
