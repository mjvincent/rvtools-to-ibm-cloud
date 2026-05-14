import csv
import io
import json

from handoff import (
    generate_disk_mapping_csv,
    generate_migration_manifest,
    generate_partition_mapping_csv,
)
from models import DiskMapping, MigrationVm, PartitionMapping
from rvtools_parser import parse_rvtools_workbook
from ui import build_partition_planning_rows


def test_parser_correlates_vpartition_by_disk_key_and_keeps_unmatched(partition_workbook):
    parsed = parse_rvtools_workbook(
        partition_workbook,
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


def test_partition_handoff_outputs_are_additive(partition_workbook):
    parsed = parse_rvtools_workbook(
        partition_workbook,
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
