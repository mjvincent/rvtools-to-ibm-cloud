import csv
import io

import pandas as pd

from models import MigrationVm, ReadinessFinding
from streamlit_app.guided_migration import (
    SAFE_DEFAULTS_BUTTON_LABEL,
    SAFE_DEFAULTS_HELP,
    action_plan_csv,
    apply_safe_migration_defaults,
    build_guided_checklist,
    build_migration_action_plan,
    has_session_planning_state,
    hard_blocked_vm_names,
    queue_exclusions_for_hard_blockers,
)


def _decision_df():
    return pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Exclude?": False,
            "Original Specs": "rhel-template",
            "Wave": "",
            "Cutover Group": "cg-app",
            "Owner": "app-team",
            "Application": "orders",
            "Image Readiness": "Ready",
            "Migration Readiness": "Blocked",
            "Migration Readiness Reasons": "Snapshot cleanup required",
            "Memory Readiness": "Ready",
            "Network Readiness": "Ready",
            "Network": "app-net",
            "Guest OS": "Linux",
            "IBM Profile": "bx2-2x8",
            "Storage Tier": "5iops-tier",
            "Subnet": "module.networking.app_net_id",
            "Security Group": "module.networking.app_net_sg_id",
            "Disk Count": 1,
            "Total Storage GB": 100,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "db-01",
            "Exclude?": False,
            "Original Specs": "windows-template",
            "Wave": "wave-01",
            "Cutover Group": "cg-db",
            "Owner": "db-team",
            "Application": "orders-db",
            "Image Readiness": "Ready",
            "Migration Readiness": "Ready",
            "Memory Readiness": "Ready",
            "Network Readiness": "Ready",
            "Network": "db-net",
            "Guest OS": "Windows",
            "IBM Profile": "bx2-4x16",
            "Storage Tier": "5iops-tier",
            "Subnet": "module.networking.db_net_id",
            "Security Group": "module.networking.db_net_sg_id",
            "Disk Count": 1,
            "Total Storage GB": 200,
        },
    ])


def _processed_vms():
    return [
        MigrationVm(
            vm_key="vm-001",
            vm_name="app-01",
            owner="app-team",
            readiness_findings=[
                ReadinessFinding(
                    finding_type="snapshot",
                    severity="Blocked",
                    source_tab="vSnapshot",
                    evidence="Snapshot cleanup required",
                    recommended_action="Remove snapshot before migration.",
                )
            ],
        ),
        MigrationVm(vm_key="vm-002", vm_name="db-01", owner="db-team"),
    ]


def test_guided_checklist_flags_missing_planning_and_blockers():
    checklist = build_guided_checklist(
        _decision_df(),
        _processed_vms(),
        disk_details={},
        nic_details={},
        remediation_tracker={},
        image_import_status={
            "rhel-template": {"import_status": "Pending"},
            "windows-template": {"import_status": "Imported"},
        },
    )

    by_step = {row["Step"]: row for row in checklist}

    assert by_step["Review readiness blockers"]["Count"] == 1
    assert by_step["Track remediation work"]["Count"] == 2
    assert by_step["Complete wave planning"]["Count"] == 1
    assert by_step["Update image import status"]["Count"] == 1
    assert by_step["Build Terraform bundle"]["Status"] == "Needs attention"


def test_session_planning_state_reminder_detects_saved_work():
    empty = pd.DataFrame([{
        "VM Name": "app-01",
        "Exclude?": False,
        "Wave": "",
        "Cutover Group": "",
        "Owner": "",
        "Application": "",
    }])
    planned = empty.copy()
    planned.loc[0, "Wave"] = "wave-01"
    excluded = empty.copy()
    excluded.loc[0, "Exclude?"] = True

    assert has_session_planning_state(empty) is False
    assert has_session_planning_state(planned) is True
    assert has_session_planning_state(excluded) is True
    assert has_session_planning_state(empty, remediation_tracker={"b1": {}}) is True
    assert has_session_planning_state(
        empty,
        image_import_status={"template": {"import_status": "Pending"}},
    ) is True


def test_action_plan_and_safe_defaults_do_not_mark_imported_or_exclude():
    df = _decision_df()
    action_plan = build_migration_action_plan(
        df,
        _processed_vms(),
        remediation_tracker={},
        image_import_status={},
    )
    by_action = {row["Action"]: row for row in action_plan}

    assert by_action["Initialize image import tracking"]["Count"] == 2
    assert by_action["Create remediation tracker entries"]["Count"] == 2
    assert by_action["Review hard-blocked VMs for exclusion"]["Count"] == 1

    remediation, images, applied = apply_safe_migration_defaults(
        df,
        _processed_vms(),
        remediation_tracker={},
        image_import_status={},
    )

    assert applied == {"image_import_pending": 2, "remediation_entries": 2}
    assert images["rhel-template"]["import_status"] == "Pending"
    assert images["windows-template"]["import_status"] == "Pending"
    assert next(iter(remediation.values()))["status"] == "Open"
    assert "Exclude?" not in next(iter(remediation.values()))


def test_safe_defaults_control_copy_explains_scope():
    assert "Pending/Open" in SAFE_DEFAULTS_BUTTON_LABEL
    assert "Pending" in SAFE_DEFAULTS_HELP
    assert "Open remediation" in SAFE_DEFAULTS_HELP
    assert "does not mark images Imported" in SAFE_DEFAULTS_HELP
    assert "exclude VMs" in SAFE_DEFAULTS_HELP
    assert "change profiles" in SAFE_DEFAULTS_HELP
    assert "build Terraform" in SAFE_DEFAULTS_HELP
    assert "migrate workloads" in SAFE_DEFAULTS_HELP


def test_hard_blocked_exclusions_are_explicit_and_queued_by_vm_name():
    df = _decision_df()

    assert hard_blocked_vm_names(df) == ["app-01"]

    fixes = queue_exclusions_for_hard_blockers(
        df,
        {"existing-vm": {"Exclude?": True}},
    )

    assert fixes["app-01"] == {"Exclude?": True}
    assert fixes["existing-vm"] == {"Exclude?": True}


def test_action_plan_csv_has_stable_headers():
    rows = build_migration_action_plan(
        _decision_df(),
        _processed_vms(),
        remediation_tracker={},
        image_import_status={},
    )

    parsed = list(csv.DictReader(io.StringIO(action_plan_csv(rows))))

    assert list(parsed[0]) == ["Action", "Count", "Impact", "Next Step"]
    assert parsed[0]["Action"] == "Initialize image import tracking"
