import pandas as pd

from streamlit_app.network_storage import (
    build_network_planning_rows,
    summarize_partition_planning,
)
from ui import build_partition_planning_rows


def test_build_network_planning_rows_preserves_switch_context():
    vms = pd.DataFrame(
        [
            {
                "VM Name": "app-01",
                "Network Readiness": "Review",
                "Network Details": [
                    {
                        "label": "Network adapter 1",
                        "connected": True,
                        "planned": True,
                        "network": "VM Network",
                        "switch": "dvSwitch01",
                        "switch_type": "distributed",
                        "port_group": "App PG",
                        "vlan": "101",
                        "port_key": "123",
                        "port_status": "up",
                        "backing_source_tab": "dvPort",
                        "match_confidence": "High",
                    }
                ],
            }
        ]
    )

    rows = build_network_planning_rows(vms)

    assert rows == [
        {
            "VM Name": "app-01",
            "NIC Label": "Network adapter 1",
            "Connected": True,
            "Planned": True,
            "Source Network": "VM Network",
            "Switch": "dvSwitch01",
            "Switch Type": "distributed",
            "Port Group": "App PG",
            "VLAN / Segment": "101",
            "Port Key": "123",
            "Port Status": "up",
            "Backing Source Tab": "dvPort",
            "Match Confidence": "High",
            "Network Readiness": "Review",
        }
    ]


def test_summarize_partition_planning_counts_high_free_and_unmatched():
    vms = [
        {
            "VM Name": "db-01",
            "Disk Details": [
                {
                    "disk": "Hard disk 1",
                    "disk_key": "2000",
                    "partitions": [
                        {
                            "disk": "C:",
                            "disk_key": "2000",
                            "capacity_mib": 102400,
                            "consumed_mib": 40000,
                            "free_mib": 62400,
                            "free_pct": 60,
                        }
                    ],
                }
            ],
            "Partition Details": [
                {
                    "disk": "orphan",
                    "disk_key": "missing",
                    "capacity_mib": 1024,
                    "consumed_mib": 900,
                    "free_mib": 124,
                    "free_pct": 12,
                }
            ],
        }
    ]

    partition_rows, high_free, unmatched = summarize_partition_planning(vms)

    assert len(partition_rows) == 2
    assert len(high_free) == 1
    assert len(unmatched) == 1
    assert build_partition_planning_rows(vms) == partition_rows
