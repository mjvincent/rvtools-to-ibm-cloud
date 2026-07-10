import io
import os
import re
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from models.network_planning import (
    NetworkPlanningState,
    PlanningMetadata,
    SecurityGroupPlan,
    SubnetPlan,
    VmNetworkAssignment,
    VpcPlan,
    to_dict,
)
from prototype.api.app import app
from prototype.api.handoff_parity import (
    CARBON_CURRENT_EXTRA_FILES,
    CARBON_MODULAR_TERRAFORM_FILES,
    STREAMLIT_HANDOFF_FILES,
)


SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"
SMALL_WORKBOOK = SAMPLES_DIR / "rvtools-small-complete.xlsx"
WORKSHOP_WORKBOOK = SAMPLES_DIR / "SizingWorkshop-RVTools.xlsx"
SAMPLE_WORKBOOKS = (
    pytest.param("small-complete", SMALL_WORKBOOK, 2, id="small-complete"),
    pytest.param("workshop", WORKSHOP_WORKBOOK, 763, id="workshop"),
)
CUSTOMER_WORKBOOKS_ENV = "CARBON_PERF_CUSTOMER_WORKBOOKS"
SYNTHETIC_STATE_ROWS_ENV = "CARBON_PERF_SYNTHETIC_STATE_ROWS"


def _max_seconds(env_var: str, default: float) -> float:
    return float(os.environ.get(env_var, default))


def _customer_workbook_paths() -> list[Path]:
    raw_paths = os.environ.get(CUSTOMER_WORKBOOKS_ENV, "")
    return [Path(path).expanduser() for path in raw_paths.split(os.pathsep) if path.strip()]


def _terraform_label(value: str) -> str:
    label = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return label or "unknown"


def _synthetic_assignment_rows(count: int) -> list[dict]:
    rows = []
    for index in range(1, count + 1):
        network = f"synthetic-net-{index % 12:02d}"
        rows.append(
            {
                "VM Key": f"synthetic-vm-{index:05d}",
                "VM Name": f"synthetic-app-{index:05d}",
                "IBM Profile": "bx2-4x16" if index % 4 == 0 else "bx2-2x8",
                "Storage Tier": "10iops-tier" if index % 5 == 0 else "3iops-tier",
                "Guest OS": "Red Hat Enterprise Linux 9 (64-bit)",
                "Network": network,
                "Owner": f"Owner {index % 20}",
                "Application": "Database" if index % 3 == 0 else "App tier",
                "Boot Disk GB": 100,
            }
        )
    return rows


def _upload_workbook_summary(client: TestClient, workbook_path: Path):
    with workbook_path.open("rb") as workbook:
        return client.post(
            "/api/workbooks/summary",
            files={
                "workbook": (
                    workbook_path.name,
                    workbook,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )


def _network_plan_for_rows(rows: list[dict]) -> NetworkPlanningState:
    network_names = sorted({row.get("Network") or "unknown-net" for row in rows})
    subnets = []
    security_groups = []
    subnet_by_network = {}
    sg_by_network = {}

    for index, network_name in enumerate(network_names, start=1):
        label = _terraform_label(network_name)
        subnet_id = f"subnet-{label}"
        security_group_id = f"sg-{label}"
        subnet_by_network[network_name] = subnet_id
        sg_by_network[network_name] = security_group_id
        subnets.append(
            SubnetPlan(
                id=subnet_id,
                name=f"{network_name}-subnet",
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr=f"10.250.{index}.0/24",
                source_network=network_name,
            )
        )
        security_groups.append(
            SecurityGroupPlan(
                id=security_group_id,
                name=f"{network_name}-sg",
                vpc_id="vpc-1",
            )
        )

    assignments = [
        VmNetworkAssignment(
            vm_key=row["VM Key"],
            vm_name=row["VM Name"],
            primary_subnet_id=subnet_by_network[row.get("Network") or "unknown-net"],
            primary_security_group_id=sg_by_network[row.get("Network") or "unknown-net"],
            ibm_profile=row.get("IBM Profile"),
            storage_tier=row.get("Storage Tier"),
            guest_os=row.get("Guest OS"),
            network=row.get("Network"),
            owner=row.get("Owner"),
            application=row.get("Application"),
            boot_disk_gb=row.get("Boot Disk GB"),
        )
        for row in rows
    ]

    return NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        subnets=subnets,
        security_groups=security_groups,
        vm_assignments=assignments,
        metadata=PlanningMetadata(
            project_name="Workshop performance",
            target_region="us-south",
            target_zone="us-south-1",
            deployment_target="Plain CLI",
        ),
    )


def _planning_state_json(rows: list[dict], summary: dict) -> dict:
    network_plan = _network_plan_for_rows(rows)
    return {
        "carbon_assignment_rows": rows,
        "carbon_summary": {"assessment_quality": summary["assessment_quality"]},
        "carbon_network_plan": to_dict(network_plan),
    }


def _endpoint_assignment_payload(planning_state_json: dict) -> list[dict]:
    assignments = []
    for assignment in planning_state_json["carbon_network_plan"]["vm_assignments"]:
        payload = dict(assignment)
        if payload.get("boot_disk_gb") is not None and payload["boot_disk_gb"] < 10:
            payload.pop("boot_disk_gb")
        assignments.append(payload)
    return assignments


@contextmanager
def _mock_large_project(project_id: str, planning_state_json: dict):
    with (
        patch("prototype.api.persistence.persistence_enabled", return_value=True),
        patch(
            "prototype.api.persistence.get_project",
            return_value={
                "id": project_id,
                "name": "Sample performance",
                "description": "",
            },
        ),
        patch(
            "prototype.api.persistence.get_project_state",
            return_value={
                "target_region": "us-south",
                "target_zone": "us-south-1",
                "planning_state_json": planning_state_json,
            },
        ),
    ):
        yield


@pytest.mark.parametrize(("sample_name", "workbook_path", "expected_rows"), SAMPLE_WORKBOOKS)
def test_sample_workbook_summary_performance_guard(sample_name, workbook_path, expected_rows):
    client = TestClient(app)

    summary_start = time.perf_counter()
    summary_response = _upload_workbook_summary(client, workbook_path)
    summary_elapsed = time.perf_counter() - summary_start

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert len(summary["assignment_rows"]) == expected_rows
    assert summary_elapsed < _max_seconds(
        f"CARBON_PERF_{sample_name.upper().replace('-', '_')}_SUMMARY_MAX_SECONDS",
        15.0,
    )


def test_private_customer_workbook_summary_performance_guard():
    workbook_paths = _customer_workbook_paths()
    if not workbook_paths:
        pytest.skip(f"Set {CUSTOMER_WORKBOOKS_ENV} to run private workbook performance fixtures")

    client = TestClient(app)
    max_seconds = _max_seconds("CARBON_PERF_CUSTOMER_SUMMARY_MAX_SECONDS", 30.0)

    for workbook_path in workbook_paths:
        assert workbook_path.exists(), f"Private workbook does not exist: {workbook_path}"
        assert workbook_path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}

        summary_start = time.perf_counter()
        summary_response = _upload_workbook_summary(client, workbook_path)
        summary_elapsed = time.perf_counter() - summary_start

        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert len(summary["assignment_rows"]) > 0
        assert summary_elapsed < max_seconds


def test_workshop_workbook_carbon_zip_performance_guard():
    client = TestClient(app)

    summary_response = _upload_workbook_summary(client, WORKSHOP_WORKBOOK)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    rows = summary["assignment_rows"]
    assert len(rows) == 763

    project_id = "workshop-performance"
    planning_state_json = _planning_state_json(rows, summary)

    zip_start = time.perf_counter()
    with _mock_large_project(project_id, planning_state_json):
        zip_response = client.post(f"/api/projects/{project_id}/terraform")
    zip_elapsed = time.perf_counter() - zip_start

    assert zip_response.status_code == 200
    assert zip_elapsed < _max_seconds("CARBON_PERF_ZIP_MAX_SECONDS", 30.0)
    assert len(zip_response.content) > 250_000

    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as archive:
        names = set(archive.namelist())

    assert STREAMLIT_HANDOFF_FILES.issubset(names)
    assert CARBON_MODULAR_TERRAFORM_FILES.issubset(names)
    assert CARBON_CURRENT_EXTRA_FILES.issubset(names)


def test_workshop_carbon_preview_performance_guard():
    client = TestClient(app)
    summary_response = _upload_workbook_summary(client, WORKSHOP_WORKBOOK)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    rows = summary["assignment_rows"]
    project_id = "workshop-preview-performance"
    planning_state_json = _planning_state_json(rows, summary)

    preview_start = time.perf_counter()
    with _mock_large_project(project_id, planning_state_json):
        preview_response = client.post(f"/api/projects/{project_id}/terraform/preview")
    preview_elapsed = time.perf_counter() - preview_start

    assert preview_response.status_code == 200
    assert preview_elapsed < _max_seconds("CARBON_PERF_PREVIEW_MAX_SECONDS", 30.0)
    payload = preview_response.json()
    assert payload["project_id"] == project_id
    assert len(payload["files"]) >= len(STREAMLIT_HANDOFF_FILES)
    preview_names = {file["path"] for file in payload["files"]}
    assert STREAMLIT_HANDOFF_FILES.issubset(preview_names)
    assert CARBON_MODULAR_TERRAFORM_FILES.issubset(preview_names)
    assert CARBON_CURRENT_EXTRA_FILES.issubset(preview_names)


def test_large_carbon_project_state_save_load_update_performance_guard():
    client = TestClient(app)
    summary_response = _upload_workbook_summary(client, WORKSHOP_WORKBOOK)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    rows = summary["assignment_rows"]
    project_id = "workshop-state-performance"
    project = {"id": project_id, "name": "Workshop performance", "description": ""}
    persisted_state: dict = {}

    def save_project_state(project_id_arg, planning_state, **kwargs):
        assert project_id_arg == project_id
        persisted_state.update(
            {
                "planning_state_json": planning_state,
                "target_region": kwargs.get("target_region"),
                "target_zone": kwargs.get("target_zone"),
                "project_name": kwargs.get("project_name"),
            }
        )
        return persisted_state

    def get_project_state(project_id_arg):
        assert project_id_arg == project_id
        return persisted_state or None

    def update_project_state(project_id_arg, planning_state_json):
        assert project_id_arg == project_id
        persisted_state["planning_state_json"] = planning_state_json
        return persisted_state

    planning_state_json = _planning_state_json(rows, summary)

    with (
        patch("prototype.api.persistence.persistence_enabled", return_value=True),
        patch("prototype.api.persistence.get_project", return_value=project),
        patch("prototype.api.persistence.save_project_state", side_effect=save_project_state),
        patch("prototype.api.persistence.get_project_state", side_effect=get_project_state),
        patch("prototype.api.persistence.update_project_state", side_effect=update_project_state),
        patch("prototype.api.persistence.list_artifacts", return_value=[]),
    ):
        save_start = time.perf_counter()
        save_response = client.put(
            f"/api/projects/{project_id}/state",
            json={
                "planning_state": planning_state_json,
                "target_region": "us-south",
                "target_zone": "us-south-1",
                "project_name": "Workshop performance",
            },
        )
        save_elapsed = time.perf_counter() - save_start

        load_start = time.perf_counter()
        load_response = client.get(f"/api/projects/{project_id}")
        load_elapsed = time.perf_counter() - load_start

        update_start = time.perf_counter()
        update_response = client.put(
            f"/api/projects/{project_id}/vm-assignments",
            json=_endpoint_assignment_payload(planning_state_json),
        )
        update_elapsed = time.perf_counter() - update_start

    assert save_response.status_code == 200
    assert load_response.status_code == 200
    assert update_response.status_code == 200
    assert save_elapsed < _max_seconds("CARBON_PERF_STATE_SAVE_MAX_SECONDS", 5.0)
    assert load_elapsed < _max_seconds("CARBON_PERF_STATE_LOAD_MAX_SECONDS", 5.0)
    assert update_elapsed < _max_seconds("CARBON_PERF_ASSIGNMENT_UPDATE_MAX_SECONDS", 5.0)
    loaded_state = load_response.json()["state"]["planning_state_json"]
    assert len(loaded_state["carbon_assignment_rows"]) == 763
    assert len(loaded_state["carbon_network_plan"]["vm_assignments"]) == 763
    assert update_response.json()["message"] == "Updated 763 VM assignments"


def test_synthetic_large_carbon_project_state_save_load_update_performance_guard():
    client = TestClient(app)
    row_count = int(os.environ.get(SYNTHETIC_STATE_ROWS_ENV, "3000"))
    rows = _synthetic_assignment_rows(row_count)
    project_id = "synthetic-state-performance"
    project = {"id": project_id, "name": "Synthetic performance", "description": ""}
    persisted_state: dict = {}
    planning_state_json = _planning_state_json(
        rows,
        {"assessment_quality": {"source": "synthetic", "row_count": row_count}},
    )

    def save_project_state(project_id_arg, planning_state, **kwargs):
        assert project_id_arg == project_id
        persisted_state.update(
            {
                "planning_state_json": planning_state,
                "target_region": kwargs.get("target_region"),
                "target_zone": kwargs.get("target_zone"),
                "project_name": kwargs.get("project_name"),
            }
        )
        return persisted_state

    def get_project_state(project_id_arg):
        assert project_id_arg == project_id
        return persisted_state or None

    def update_project_state(project_id_arg, planning_state_json_arg):
        assert project_id_arg == project_id
        persisted_state["planning_state_json"] = planning_state_json_arg
        return persisted_state

    with (
        patch("prototype.api.persistence.persistence_enabled", return_value=True),
        patch("prototype.api.persistence.get_project", return_value=project),
        patch("prototype.api.persistence.save_project_state", side_effect=save_project_state),
        patch("prototype.api.persistence.get_project_state", side_effect=get_project_state),
        patch("prototype.api.persistence.update_project_state", side_effect=update_project_state),
        patch("prototype.api.persistence.list_artifacts", return_value=[]),
    ):
        save_start = time.perf_counter()
        save_response = client.put(
            f"/api/projects/{project_id}/state",
            json={
                "planning_state": planning_state_json,
                "target_region": "us-south",
                "target_zone": "us-south-1",
                "project_name": "Synthetic performance",
            },
        )
        save_elapsed = time.perf_counter() - save_start

        load_start = time.perf_counter()
        load_response = client.get(f"/api/projects/{project_id}")
        load_elapsed = time.perf_counter() - load_start

        update_start = time.perf_counter()
        update_response = client.put(
            f"/api/projects/{project_id}/vm-assignments",
            json=_endpoint_assignment_payload(planning_state_json),
        )
        update_elapsed = time.perf_counter() - update_start

    assert save_response.status_code == 200
    assert load_response.status_code == 200
    assert update_response.status_code == 200
    assert save_elapsed < _max_seconds("CARBON_PERF_SYNTHETIC_STATE_SAVE_MAX_SECONDS", 8.0)
    assert load_elapsed < _max_seconds("CARBON_PERF_SYNTHETIC_STATE_LOAD_MAX_SECONDS", 8.0)
    assert update_elapsed < _max_seconds("CARBON_PERF_SYNTHETIC_ASSIGNMENT_UPDATE_MAX_SECONDS", 8.0)
    loaded_state = load_response.json()["state"]["planning_state_json"]
    assert len(loaded_state["carbon_assignment_rows"]) == row_count
    assert len(loaded_state["carbon_network_plan"]["vm_assignments"]) == row_count
    assert update_response.json()["message"] == f"Updated {row_count} VM assignments"
