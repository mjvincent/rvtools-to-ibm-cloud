import pandas as pd

from rvtools import build_storage_inventory


def test_build_storage_inventory_maps_disks_and_partitions():
    df_vdisk = pd.DataFrame(
        [
            {
                "VM": "db-01",
                "Disk": "Hard disk 1",
                "Disk Key": "2000",
                "Capacity MiB": 102400,
                "Unit #": 0,
                "Disk Path": "[datastore] db-01/db-01.vmdk",
            },
            {
                "VM": "db-01",
                "Disk": "Hard disk 2",
                "Disk Key": "2001",
                "Capacity MiB": 51200,
                "Unit #": 1,
            },
        ]
    )
    df_vpartition = pd.DataFrame(
        [
            {
                "VM": "db-01",
                "Disk": "C:",
                "Disk Key": "2000",
                "Capacity MiB": 102400,
                "Consumed MiB": 40000,
                "Free MiB": 62400,
                "Free % ": 60,
            }
        ]
    )

    inventory = build_storage_inventory(df_vdisk, df_vpartition)

    assert inventory.disk_sum == {"db-01": 153600}
    assert inventory.disk_count == {"db-01": 2}
    assert inventory.boot_disk_gb == {"db-01": 100.0}
    assert inventory.unmatched_partition_details == {"db-01": []}
    assert inventory.disk_details["db-01"][0]["partitions"] == [
        {
            "disk": "C:",
            "disk_key": "2000",
            "capacity_mib": 102400.0,
            "consumed_mib": 40000.0,
            "free_mib": 62400.0,
            "free_pct": 60.0,
            "matched": True,
        }
    ]


def test_build_storage_inventory_attaches_single_disk_unmatched_partitions():
    df_vdisk = pd.DataFrame(
        [
            {
                "VM": "app-01",
                "Disk": "Hard disk 1",
                "Disk Key": "",
                "Capacity MiB": 10240,
            }
        ]
    )
    df_vpartition = pd.DataFrame(
        [
            {
                "VM": "app-01",
                "Disk": "/",
                "Disk Key": "missing",
                "Capacity MiB": 10240,
                "Consumed MiB": 5000,
                "Free MiB": 5240,
                "Free % ": 51,
            }
        ]
    )

    inventory = build_storage_inventory(df_vdisk, df_vpartition)

    assert inventory.unmatched_partition_details == {"app-01": []}
    assert inventory.disk_details["app-01"][0]["partitions"][0]["matched"]
