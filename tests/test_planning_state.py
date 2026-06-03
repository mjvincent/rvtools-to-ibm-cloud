import json
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

    assert result == {"applied": 1, "skipped": 0}
    assert updated.loc[0, "Wave"] == "wave-01"
    assert updated.loc[0, "Cutover Group"] == "cg-app"
    assert updated.loc[0, "Owner"] == "app-team"
    assert updated.loc[0, "Application"] == "orders"
    assert updated.loc[0, "Priority"] == "High"
    assert updated.loc[0, "Dependency Group"] == "dg-01"


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
