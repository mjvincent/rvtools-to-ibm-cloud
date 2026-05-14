import csv
import io
import json
from pathlib import Path

import pandas as pd
import pytest

from models import DiskMapping, MigrationVm, NicMapping, ReadinessFinding


@pytest.fixture
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
            {"disk": "Hard disk 1", "capacity_gb": 80, "is_boot": True},
            {"disk": "Hard disk 2", "capacity_gb": 120, "is_boot": False},
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


@pytest.fixture
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


@pytest.fixture
def disk_vm_record():
    return {
        "VM Name": "app-01",
        "Network": "app-net",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "5iops-tier",
        "Disk Details": [
            {
                "disk": "Hard disk 1",
                "capacity_gb": 80,
                "is_boot": True,
                "disk_key": "2000",
                "unit_number": 0,
            },
            {
                "disk": "Hard disk 2",
                "capacity_gb": 120,
                "is_boot": False,
                "disk_key": "2001",
                "unit_number": 1,
            },
        ],
    }


@pytest.fixture
def partition_workbook():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([{
            "VM": "app-01",
            "Powerstate": "poweredOn",
            "CPUs": 2,
            "Memory": 8192,
            "Host": "host-01",
            "Disks": 2,
            "Provisioned MiB": 153600,
            "CPU Usage %": 20,
            "Network #1": "app-net",
            "Primary IP Address": "10.0.1.10",
            "OS according to the VMware Tools": "Microsoft Windows Server 2022",
        }]).to_excel(writer, sheet_name="vInfo", index=False)
        pd.DataFrame([
            {
                "VM": "app-01",
                "Disk": "Hard disk 1",
                "Disk Key": "2000",
                "Capacity MiB": 81920,
                "Unit #": 0,
            },
            {
                "VM": "app-01",
                "Disk": "Hard disk 2",
                "Disk Key": "2001",
                "Capacity MiB": 71680,
                "Unit #": 1,
            },
        ]).to_excel(writer, sheet_name="vDisk", index=False)
        pd.DataFrame([
            {
                "VM": "app-01",
                "Disk Key": "2000",
                "Disk": "C:\\",
                "Capacity MiB": 61440,
                "Consumed MiB": 40960,
                "Free MiB": 20480,
                "Free % ": 33,
            },
            {
                "VM": "app-01",
                "Disk Key": "2001",
                "Disk": "D:\\",
                "Capacity MiB": 51200,
                "Consumed MiB": 10240,
                "Free MiB": 40960,
                "Free % ": 80,
            },
            {
                "VM": "app-01",
                "Disk": "E:\\",
                "Capacity MiB": 10240,
                "Consumed MiB": 5120,
                "Free MiB": 5120,
                "Free % ": 50,
            },
        ]).to_excel(writer, sheet_name="vPartition", index=False)
        pd.DataFrame([{
            "VM": "app-01",
            "Overall": 100,
            "CPU ready %": 0,
            "CPU co-stop": 0,
            "Limit": 0,
        }]).to_excel(writer, sheet_name="vCPU", index=False)
        pd.DataFrame([{
            "VM": "app-01",
            "Size MiB": 8192,
            "Active": 4096,
            "Consumed": 6144,
            "Ballooned": 0,
            "Swapped": 0,
            "Reservation": 0,
            "Limit": -1,
            "Hot Add": "False",
        }]).to_excel(writer, sheet_name="vMemory", index=False)
        pd.DataFrame([{
            "Host": "host-01",
            "Speed": 2400,
            "# Cores": 8,
        }]).to_excel(writer, sheet_name="vHost", index=False)
        pd.DataFrame([{
            "Cluster": "cluster-01",
            "TotalCpu": 19200,
        }]).to_excel(writer, sheet_name="vCluster", index=False)
        pd.DataFrame([{
            "VM": "app-01",
            "Network": "app-net",
            "Connected": True,
            "IPv4 Address": "10.0.1.10",
        }]).to_excel(writer, sheet_name="vNetwork", index=False)
    output.seek(0)
    return output


@pytest.fixture
def sample_live_catalog():
    return {
        "profiles": [
            {
                "name": "bx2-2x8",
                "cpu": 2,
                "ram": 8,
                "hourly": 0.114,
                "pricing_source": "live-profile-static-price",
                "pricing_confidence": "profile-live-price-static",
                "family": "bx2",
            }
        ],
        "storage_tier_rates": {"3iops-tier": 0.10},
        "metadata": {
            "mode": "live",
            "source": "ibm-vpc-profile-api",
            "confidence": "profile-live-price-static",
            "region": "us-south",
            "last_updated": "2026-05-14T00:00:00+00:00",
            "status": "Live IBM profile discovery succeeded",
        },
    }


@pytest.fixture
def parse_csv_rows():
    return lambda text: list(csv.DictReader(io.StringIO(text)))


@pytest.fixture
def parse_json():
    return json.loads


@pytest.fixture
def assert_matches_snapshot():
    snapshot_dir = Path(__file__).parent / "snapshots"

    def _assert_matches_snapshot(name, actual):
        expected = (snapshot_dir / name).read_text(encoding="utf-8")
        normalized_actual = actual.replace("\r\n", "\n")
        assert normalized_actual == expected

    return _assert_matches_snapshot
