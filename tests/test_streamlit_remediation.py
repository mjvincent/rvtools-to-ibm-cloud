from types import SimpleNamespace

import pandas as pd

from models import ReadinessFinding
from streamlit_app.remediation import (
    build_remediation_backlog_items,
    import_remediation_tracker,
    persist_remediation_edits,
)


def test_build_remediation_backlog_items_uses_tracker_state():
    finding = ReadinessFinding(
        severity="Blocked",
        finding_type="Active snapshots",
        evidence="2 snapshots",
        recommended_action="Consolidate snapshots",
    )
    vm = SimpleNamespace(
        vm_key="vm-1",
        vm_name="app-01",
        owner="platform",
        readiness_findings=[finding],
        network_readiness_findings=[],
        migration=None,
    )
    tracker = {
        "vm-1::0": {
            "status": "In Progress",
            "due_date": "2026-06-15",
            "notes": "Owner assigned",
        }
    }

    rows = build_remediation_backlog_items([vm], tracker)

    assert rows == [{
        "blocker_id": "vm-1::0",
        "VM Key": "vm-1",
        "VM Name": "app-01",
        "Owner": "platform",
        "Blocker Type": "Active snapshots",
        "Blocker Description": "Consolidate snapshots",
        "Status": "In Progress",
        "Due Date": "2026-06-15",
        "Notes": "Owner assigned",
    }]


def test_persist_remediation_edits_keeps_existing_when_not_dataframe():
    tracker = {"vm-1::0": {"status": "Open"}}

    assert persist_remediation_edits(None, tracker) == tracker


def test_import_remediation_tracker_matches_by_blocker_id():
    imported_df = pd.DataFrame([{
        "blocker_id": "vm-1::0",
        "VM Key": "vm-1",
        "Blocker Type": "Active snapshots",
        "Blocker Description": "Consolidate snapshots",
        "Status": "Resolved",
        "Due Date": "2026-06-20",
        "Notes": "Done",
        "Owner": "platform",
    }])

    updated, result = import_remediation_tracker(imported_df, [], {})

    assert result == {"applied": 1, "skipped": 0}
    assert updated["vm-1::0"] == {
        "status": "Resolved",
        "due_date": "2026-06-20",
        "notes": "Done",
        "owner": "platform",
    }


def test_import_remediation_tracker_matches_current_backlog_shape():
    imported_df = pd.DataFrame([{
        "VM Key": "vm-1",
        "Blocker Type": "Active snapshots",
        "Blocker Description": "Consolidate snapshots",
        "Status": "In Progress",
        "Due Date": "",
        "Notes": "Scheduled",
        "Owner": "platform",
    }])
    backlog_rows = [{
        "blocker_id": "vm-1::0",
        "VM Key": "vm-1",
        "Blocker Type": "Active snapshots",
        "Blocker Description": "Consolidate snapshots",
    }]

    updated, result = import_remediation_tracker(
        imported_df,
        backlog_rows,
        {},
    )

    assert result == {"applied": 1, "skipped": 0}
    assert updated["vm-1::0"]["status"] == "In Progress"
