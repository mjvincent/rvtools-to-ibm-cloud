import csv
import io
import json

import pandas as pd

from handoff import (
    generate_disk_mapping_csv,
    generate_migration_manifest,
    generate_partition_mapping_csv,
)
from models import DiskMapping, MigrationVm, PartitionMapping
from rvtools_parser import parse_rvtools_workbook
from ui import build_partition_planning_rows


def _workbook_with_partitions():
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


def test_parser_correlates_vpartition_by_disk_key_and_keeps_unmatched():
    parsed = parse_rvtools_workbook(
        _workbook_with_partitions(),
        "us-south",
        40,
        True,
    )
    record = parsed.processed_vms[0].to_record()
    disks = record["Disk Details"]

    assert disks[0]["partitions"][0]["disk"] == "C:\\"
    assert disks[1]["partitions"][0]["disk"] == "D:\\"
    assert record["Partition Details"][0]["disk"] == "E:\\"
    assert record["Partition Count"] == 3
    assert record["Unmatched Partition Count"] == 1


def test_model_round_trips_partition_details():
    model = MigrationVm(
        vm_name="app-01",
        disks=[
            DiskMapping(
                disk="Hard disk 1",
                disk_key="2000",
                is_boot=True,
                partitions=[
                    PartitionMapping(
                        disk="C:\\",
                        disk_key="2000",
                        capacity_mib=61440,
                        free_mib=20480,
                        matched=True,
                    )
                ],
            )
        ],
        partitions=[
            PartitionMapping(disk="E:\\", capacity_mib=10240, free_mib=5120)
        ],
    )
    record = MigrationVm.from_record(model.to_record()).to_record()

    assert record["Disk Details"][0]["partition_count"] == 1
    assert record["Disk Details"][0]["partition_labels"] == "C:\\"
    assert record["Partition Details"][0]["disk"] == "E:\\"


def test_partition_handoff_outputs_are_additive():
    parsed = parse_rvtools_workbook(
        _workbook_with_partitions(),
        "us-south",
        40,
        True,
    )
    vm = parsed.processed_vms[0]
    partition_rows = list(csv.DictReader(
        io.StringIO(generate_partition_mapping_csv([vm]))
    ))
    disk_rows = list(csv.DictReader(
        io.StringIO(generate_disk_mapping_csv([vm]))
    ))
    manifest = json.loads(generate_migration_manifest([vm], {
        "project_name": "demo",
    }))

    assert len(partition_rows) == 3
    assert partition_rows[2]["Matched To Disk"] == "False"
    assert "Partition Count" in disk_rows[0]
    assert disk_rows[1]["Partition Labels"] == "D:\\"
    assert manifest["handoff_files"]["partition_mapping_csv"] == "partition-mapping.csv"
    assert manifest["virtual_machines"][0]["source"]["partitions"][2]["disk"] == "E:\\"


def test_partition_planning_rows_shape_for_ui():
    vm = MigrationVm.from_record({
        "VM Name": "app-01",
        "Disk Details": [{
            "disk": "Hard disk 1",
            "disk_key": "2000",
            "partitions": [{
                "disk": "C:\\",
                "disk_key": "2000",
                "capacity_mib": 61440,
                "consumed_mib": 40960,
                "free_mib": 20480,
                "free_pct": 33,
                "matched": True,
            }],
        }],
        "Partition Details": [{
            "disk": "E:\\",
            "capacity_mib": 10240,
            "free_mib": 5120,
            "free_pct": 50,
        }],
    })

    rows = build_partition_planning_rows([vm])

    assert rows[0]["Matched"] is True
    assert rows[1]["Matched"] is False
    assert rows[1]["Partition"] == "E:\\"


if __name__ == "__main__":
    test_parser_correlates_vpartition_by_disk_key_and_keeps_unmatched()
    test_model_round_trips_partition_details()
    test_partition_handoff_outputs_are_additive()
    test_partition_planning_rows_shape_for_ui()
    print("partition mapping tests ok")
