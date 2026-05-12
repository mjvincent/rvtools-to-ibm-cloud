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
        "Storage Tier": "5iops-tier",
        "Subnet": "module.networking.app_net_id",
        "Security Group": "module.networking.app_net_sg_id",
        "Disk Count": 2,
        "Total Storage GB": 200,
        "Image Readiness": "Review",
        "Migration Readiness": "Review",
        "Memory Readiness": "Ready",
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
            },
            {
                "label": "Network adapter 2",
                "network": "db-net",
                "connected": True,
                "ipv4": "10.0.2.10",
            },
        ],
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
        image_readiness="Review",
        migration_readiness="Review",
        memory_readiness="Ready",
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


def test_exports_accept_normalized_vm_model():
    vm = sample_vm_model()
    manifest = json.loads(
        generate_migration_manifest([vm], {"project_name": "demo"})
    )
    vm_record = manifest["virtual_machines"][0]

    assert vm_record["vm_name"] == "app-01"
    assert vm_record["target"]["data_volumes"][0]["source_disk"] == "Hard disk 2"
    assert vm_record["migration_readiness"]["findings"][0]["source_tab"] == "vTools"


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
    assert "module.networking.db_net_id" in vsi_main


def test_nic_csv_accepts_model_and_preserves_roles():
    rows = list(csv.DictReader(io.StringIO(generate_nic_mapping_csv([
        sample_vm_model()
    ]))))

    assert rows[0]["Role"] == "primary"
    assert rows[1]["Role"] == "secondary"


if __name__ == "__main__":
    test_model_round_trips_from_legacy_record()
    test_exports_accept_normalized_vm_model()
    test_terraform_renderer_accepts_normalized_vm_model()
    test_nic_csv_accepts_model_and_preserves_roles()
    print("normalized model tests ok")
