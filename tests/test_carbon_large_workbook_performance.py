import io
import os
import re
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

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
WORKSHOP_WORKBOOK = SAMPLES_DIR / "SizingWorkshop-RVTools.xlsx"


def _max_seconds(env_var: str, default: float) -> float:
    return float(os.environ.get(env_var, default))


def _terraform_label(value: str) -> str:
    label = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return label or "unknown"


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


def test_workshop_workbook_summary_and_carbon_zip_performance_guard():
    client = TestClient(app)

    summary_start = time.perf_counter()
    with WORKSHOP_WORKBOOK.open("rb") as workbook:
        summary_response = client.post(
            "/api/workbooks/summary",
            files={
                "workbook": (
                    WORKSHOP_WORKBOOK.name,
                    workbook,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    summary_elapsed = time.perf_counter() - summary_start

    assert summary_response.status_code == 200
    summary = summary_response.json()
    rows = summary["assignment_rows"]
    assert len(rows) == 763
    assert summary_elapsed < _max_seconds("CARBON_PERF_SUMMARY_MAX_SECONDS", 15.0)

    network_plan = _network_plan_for_rows(rows)
    project_id = "workshop-performance"
    planning_state_json = {
        "carbon_assignment_rows": rows,
        "carbon_summary": {"assessment_quality": summary["assessment_quality"]},
        "carbon_network_plan": to_dict(network_plan),
    }

    zip_start = time.perf_counter()
    with (
        patch("prototype.api.persistence.persistence_enabled", return_value=True),
        patch(
            "prototype.api.persistence.get_project",
            return_value={
                "id": project_id,
                "name": "Workshop performance",
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
