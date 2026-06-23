import json
import inspect
import zipfile
from io import BytesIO

import pandas as pd

from handoff import (
    extract_image_import_status,
    extract_remediation_tracker,
    generate_migration_manifest,
    generate_planning_state_json,
    load_planning_state_json,
)
from streamlit_app.package_builder import build_terraform_bundle
from streamlit_app.planning_state import apply_planning_state_to_dataframe
from streamlit_app.planning_state import build_current_planning_state_json
from streamlit_app.planning_state import build_planning_state_restore_summary
from streamlit_app.planning_state import build_session_safety_rows
from streamlit_app.planning_state import database_persistence_status
from streamlit_app.planning_state import database_persistence_available
from streamlit_app import planning_state


def _vm(**overrides):
    record = {
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Network": "app-net",
        "Guest OS": "Linux",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "5iops-tier",
        "Subnet": "module.networking.app_net_id",
        "Security Group": "module.networking.app_net_sg_id",
        "Disk Count": 1,
        "Total Storage GB": 100,
        "Wave": "wave-01",
        "Cutover Group": "cg-app",
        "Owner": "app-team",
        "Application": "orders",
        "Priority": "High",
        "Dependency Group": "dg-01",
    }
    record.update(overrides)
    return record


def test_planning_state_json_roundtrip():
    remediation_tracker = {
        "vm-001::0": {
            "status": "In Progress",
            "owner": "app-team",
        }
    }
    image_import_status = {
        "rhel-8-template": {
            "import_status": "Imported",
            "target_catalog_id": "catalog-1",
        }
    }

    state_json = generate_planning_state_json(
        [_vm()],
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
        metadata={
            "project_name": "demo",
            "target_region": "us-south",
            "target_zone": "us-south-1",
        },
    )
    state = load_planning_state_json(state_json)

    assert state["schema_version"] == "1.0"
    assert state["metadata"]["project_name"] == "demo"
    assert state["vm_decisions"][0]["VM Key"] == "vm-001"
    assert state["vm_decisions"][0]["Network"] == "app-net"
    assert state["wave_planning"][0]["Wave"] == "wave-01"
    assert extract_remediation_tracker(state) == remediation_tracker
    assert extract_image_import_status(state) == image_import_status


def test_apply_planning_state_to_dataframe_restores_wave_fields():
    df = pd.DataFrame([{
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Exclude?": False,
        "Wave": "",
        "Cutover Group": "",
        "Owner": "",
        "Application": "",
    }])
    state = json.loads(generate_planning_state_json([_vm()]))

    updated, result = apply_planning_state_to_dataframe(df, state)

    assert result == {
        "applied": 1,
        "skipped": 0,
        "wave_applied": 1,
        "wave_skipped": 0,
        "decision_applied": 1,
        "decision_skipped": 0,
    }
    assert updated.loc[0, "Wave"] == "wave-01"
    assert updated.loc[0, "Cutover Group"] == "cg-app"
    assert updated.loc[0, "Owner"] == "app-team"
    assert updated.loc[0, "Application"] == "orders"
    assert updated.loc[0, "Priority"] == "High"
    assert updated.loc[0, "Dependency Group"] == "dg-01"


def test_apply_planning_state_to_dataframe_restores_vm_decisions():
    df = pd.DataFrame([{
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Exclude?": False,
        "Override Profile": "",
        "Override Storage Tier": "",
        "Network": "old-net",
        "Subnet": "",
        "Security Group": "",
    }])
    state = json.loads(generate_planning_state_json(
        [_vm()],
        decision_records=[_vm(
            **{
                "Exclude?": True,
                "Override Profile": "bx2-4x16",
                "Override Storage Tier": "10iops-tier",
                "Network": "app-net",
                "Subnet": "module.networking.app_net_id",
                "Security Group": "module.networking.app_net_sg_id",
            }
        )],
    ))

    updated, result = apply_planning_state_to_dataframe(df, state)

    assert result["decision_applied"] == 1
    assert result["decision_skipped"] == 0
    assert updated.loc[0, "Exclude?"] == True
    assert updated.loc[0, "Override Profile"] == "bx2-4x16"
    assert updated.loc[0, "Override Storage Tier"] == "10iops-tier"
    assert updated.loc[0, "Network"] == "app-net"
    assert updated.loc[0, "Subnet"] == "module.networking.app_net_id"
    assert updated.loc[0, "Security Group"] == "module.networking.app_net_sg_id"


def test_planning_state_restore_summary_combines_session_and_dataframe_counts():
    rows = build_planning_state_restore_summary(
        {"schema_version": "1.0"},
        {
            "decision_applied": 2,
            "decision_skipped": 1,
            "wave_applied": 3,
            "wave_skipped": 0,
        },
        {"remediation_items": 4, "image_groups": 5},
    )

    assert rows == [
        {"Restored Area": "VM decisions", "Applied": 2, "Skipped": 1},
        {"Restored Area": "Wave planning", "Applied": 3, "Skipped": 0},
        {"Restored Area": "Remediation tracker", "Applied": 4, "Skipped": 0},
        {"Restored Area": "Image import status", "Applied": 5, "Skipped": 0},
    ]


def test_session_safety_rows_explain_restore_boundary_and_actions():
    text = " ".join(
        f"{row['Area']} {row['What It Covers']} {row['Recommended Action']}"
        for row in build_session_safety_rows()
    )

    assert "VM decisions" in text
    assert "wave planning" in text
    assert "remediation tracker" in text
    assert "image import status" in text
    assert "project metadata" in text
    assert "Uploaded RVTools workbook" in text
    assert "generated ZIP bytes" in text
    assert "Terraform execution state" in text
    assert "Download planning state before closing" in text
    assert "handing work to another teammate" in text


def test_database_persistence_availability_follows_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_persistence_available() is False

    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    assert database_persistence_available() is True


def test_database_persistence_status_reports_not_configured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    status, message = database_persistence_status()

    assert status == "not_configured"
    assert "DATABASE_URL" in message


def test_database_unavailable_guidance_keeps_save_action_visible():
    source = inspect.getsource(planning_state._render_database_save_unavailable)

    assert '"Save To Database"' in source
    assert "disabled=True" in source
    assert "docker compose up --build --detach" in source
    assert "start-rvtools.command" in source
    assert "make run" in source
    assert "DATABASE_URL is only needed manually" in source


def test_build_current_planning_state_json_matches_export_shape():
    df = pd.DataFrame([_vm(**{"Exclude?": False})])

    state = json.loads(build_current_planning_state_json(
        df,
        [_vm()],
        disk_details={},
        nic_details={},
        project_name="demo",
        target_region="us-south",
        target_zone="us-south-1",
    ))

    assert state["metadata"]["project_name"] == "demo"
    assert state["metadata"]["target_region"] == "us-south"
    assert state["vm_decisions"][0]["VM Key"] == "vm-001"
    assert state["wave_planning"][0]["Wave"] == "wave-01"


def test_manifest_references_planning_state_file():
    manifest = json.loads(generate_migration_manifest([_vm()], {}))

    assert manifest["handoff_files"]["planning_state_json"] == "planning-state.json"


def test_terraform_bundle_includes_planning_state_json():
    bundle = build_terraform_bundle(
        [_vm()],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
        True,
        "demo-vpc",
        {},
        "manual",
        "Plain CLI",
        "demo",
        "0.0.0.0/0",
        {
            "mode": "static",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
        },
        {},
        {},
        [],
        {"vm-001::0": {"status": "Resolved"}},
        {"rhel-8-template": {"import_status": "Imported"}},
    )

    with zipfile.ZipFile(BytesIO(bundle)) as zf:
        names = set(zf.namelist())
        state = json.loads(zf.read("planning-state.json"))

    assert "planning-state.json" in names
    assert state["metadata"]["project_name"] == "demo"
    assert state["remediation_tracker"]["vm-001::0"]["status"] == "Resolved"
