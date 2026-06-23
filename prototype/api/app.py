"""Thin FastAPI prototype around the existing RVTools planning engine."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from catalog_pricing import get_pricing_catalog
from rvtools_parser import parse_rvtools_workbook
from streamlit_app.overview_readiness import (
    READINESS_STATUS_COLUMNS,
    calculate_estate_summary,
    calculate_overview_blockers,
)

from . import persistence


DEFAULT_REGION = "us-south"
DEFAULT_ZONE = "us-south-1"
DEFAULT_THRESHOLD = 40


@asynccontextmanager
async def lifespan(_app: FastAPI):
    persistence.initialize_schema()
    yield


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class ProjectStateSave(BaseModel):
    planning_state: dict[str, Any]
    target_region: str = DEFAULT_REGION

# Import network planning schemas
from .schemas import NetworkPlanningStateSchema, VmNetworkAssignmentSchema
from models.network_planning import NetworkPlanningState, from_dict, to_dict
    target_zone: str = DEFAULT_ZONE
    project_name: str = ""


app = FastAPI(
    title="RVTools to IBM Cloud Prototype API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_persistence() -> None:
    if not persistence.persistence_enabled():
        raise HTTPException(
            status_code=503,
            detail="Persistence is disabled because DATABASE_URL is not set.",
        )


def _parse_upload(
    upload: UploadFile,
    target_region: str = DEFAULT_REGION,
    utilization_threshold: int = DEFAULT_THRESHOLD,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not upload.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Upload a standard RVTools .xlsx workbook.",
        )
    pricing_catalog = get_pricing_catalog("static", region=target_region)
    upload.file.seek(0)
    try:
        parsed = parse_rvtools_workbook(
            upload.file,
            target_region=target_region,
            utilization_threshold=utilization_threshold,
            generate_security_groups=True,
            catalog_profiles=pricing_catalog.get("profiles", []),
            storage_tier_rates=pricing_catalog.get("storage_tier_rates"),
            pricing_metadata=pricing_catalog.get("metadata", {}),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse RVTools workbook: {exc}",
        ) from exc
    records = [vm.to_record() for vm in parsed.processed_vms]
    return pd.DataFrame(records), parsed.assessment_quality


def _status_counts(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    active = df[~df["Exclude?"]]
    counts: dict[str, dict[str, int]] = {}
    for column in READINESS_STATUS_COLUMNS:
        counts[column] = {
            status: int((active[column] == status).sum())
            for status in ["Blocked", "Review", "Ready"]
        }
    return counts


def _estate_summary_payload(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "in_scope": int(summary.get("in_scope", 0)),
        "excluded": int(summary.get("excluded", 0)),
        "monthly": float(summary.get("monthly", 0)),
        "savings": float(summary.get("savings", 0)),
        "blocked": int(summary.get("blocked", 0)),
        "review": int(summary.get("review", 0)),
    }


def _blocker_payload(blockers: dict[str, Any]) -> dict[str, int]:
    return {key: int(value) for key, value in blockers.items()}


ASSIGNMENT_COLUMNS = [
    "VM Key",
    "VM Name",
    "Image Readiness",
    "Readiness Reasons",
    "Migration Readiness",
    "Migration Readiness Reasons",
    "Memory Readiness",
    "Memory Readiness Reasons",
    "Network Readiness",
    "Network Readiness Reasons",
    "IBM Profile",
    "Override Profile",
    "Storage Tier",
    "Override Storage Tier",
    "Network",
    "Subnet",
    "Security Group",
    "Power State",
    "Owner",
    "Application",
    "Wave",
    "Cutover Group",
    "Priority",
    "Dependency Group",
]


def _assignment_rows_payload(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return VM rows with the fields Carbon needs for assignment planning."""
    active = df[~df["Exclude?"]].copy()
    for column in ASSIGNMENT_COLUMNS:
        if column not in active.columns:
            active[column] = ""
    active["_blocked_signals"] = active[
        READINESS_STATUS_COLUMNS
    ].eq("Blocked").sum(axis=1)
    active = active.sort_values(
        ["_blocked_signals", "VM Name"],
        ascending=[False, True],
    )
    rows = active[ASSIGNMENT_COLUMNS].fillna("").to_dict("records")
    for index, row in enumerate(rows):
        if not row.get("VM Key"):
            row["VM Key"] = row.get("VM Name") or f"vm-{index + 1}"
    return rows


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "persistence_enabled": persistence.persistence_enabled(),
    }


@app.post("/api/workbooks/summary")
async def summarize_workbook(
    workbook: UploadFile = File(...),
) -> dict[str, Any]:
    df, assessment_quality = _parse_upload(workbook)
    summary = calculate_estate_summary(df)
    blockers = calculate_overview_blockers(df)
    active = df[~df["Exclude?"]].copy()
    active["_blocked_signals"] = active[
        READINESS_STATUS_COLUMNS
    ].eq("Blocked").sum(axis=1)
    readiness_rows = active.sort_values(
        ["_blocked_signals", "VM Name"],
        ascending=[False, True],
    ).head(25)
    return {
        "filename": workbook.filename,
        "estate_summary": _estate_summary_payload(summary),
        "overview_blockers": _blocker_payload(blockers),
        "readiness_counts": _status_counts(df),
        "assessment_quality": assessment_quality.get("summary", {}),
        "assignment_rows": _assignment_rows_payload(df),
        "readiness_rows": readiness_rows[
            [
                "VM Name",
                "Image Readiness",
                "Migration Readiness",
                "Memory Readiness",
                "Network Readiness",
                "Power State",
            ]
        ].to_dict("records"),
    }


@app.get("/api/projects")
def list_projects() -> dict[str, Any]:
    _require_persistence()
    return {"projects": persistence.list_projects()}


@app.post("/api/projects")
def create_project(payload: ProjectCreate) -> dict[str, Any]:
    _require_persistence()
    return {"project": persistence.create_project(
        payload.name,
        payload.description,
    )}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    _require_persistence()
    project = persistence.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {
        "project": project,
        "state": persistence.get_project_state(project_id),
        "artifacts": persistence.list_artifacts(project_id),
    }


@app.patch("/api/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate) -> dict[str, Any]:
    _require_persistence()
    project = persistence.update_project(
        project_id,
        payload.name,
        payload.description,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"project": project}


@app.put("/api/projects/{project_id}/state")
def save_project_state(
    project_id: str,
    payload: ProjectStateSave,
) -> dict[str, Any]:
    _require_persistence()
    if not persistence.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    state = persistence.save_project_state(
        project_id,
        payload.planning_state,
        target_region=payload.target_region,
        target_zone=payload.target_zone,
        project_name=payload.project_name,
    )
    return {"state": state}


@app.post("/api/projects/{project_id}/artifacts")
async def save_project_artifact(
    project_id: str,
    artifact_type: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    _require_persistence()
    if not persistence.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    artifact = persistence.save_artifact(
        project_id,
        artifact_type,
        file.filename,
        file.content_type or "",
        file.file,
    )
    return {"artifact": artifact}


@app.get("/api/projects/{project_id}/artifacts/{artifact_id}")
def download_project_artifact(
    project_id: str,
    artifact_id: str,
) -> FileResponse:
    _require_persistence()
    artifacts = persistence.list_artifacts(project_id)
    artifact = next((row for row in artifacts if row["id"] == artifact_id), None)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return FileResponse(
        artifact["stored_path"],
        media_type=artifact.get("content_type") or "application/octet-stream",
        filename=artifact["original_filename"],
    )


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str) -> dict[str, str]:
    _require_persistence()
    persistence.delete_project(project_id)
    return {"status": "deleted"}


@app.post("/api/planning-state/validate")
async def validate_planning_state(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        content = await file.read()
        state = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid planning-state JSON: {exc}",
        ) from exc
    return {
        "project_name": state.get("metadata", {}).get("project_name", ""),
        "vm_decisions": len(state.get("vm_decisions", [])),
        "wave_planning": len(state.get("wave_planning", [])),
        "remediation_items": len(state.get("remediation_tracker", {})),
        "image_groups": len(state.get("image_import_status", {})),


# Network Planning Endpoints

@app.post("/api/projects/{project_id}/network-plan")
async def save_network_plan(
    project_id: str,
    network_plan: NetworkPlanningStateSchema
) -> dict[str, Any]:
    """Save Carbon UI network planning state."""
    _require_persistence()

    project = persistence.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate network plan
    try:
        # Convert Pydantic model to dict
        plan_dict = network_plan.dict()
        # Validate by creating NetworkPlanningState
        validated_plan = from_dict(plan_dict)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid network plan: {exc}"
        )

    # Save to planning_state_json
    planning_state_json = project.get("planning_state_json", {})
    planning_state_json["carbon_network_plan"] = plan_dict

    persistence.update_project_state(project_id, planning_state_json)

    return {"status": "success", "message": "Network plan saved"}


@app.get("/api/projects/{project_id}/network-plan")
async def get_network_plan(project_id: str) -> dict[str, Any]:
    """Retrieve saved network planning state."""
    _require_persistence()

    project = persistence.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    planning_state_json = project.get("planning_state_json", {})
    network_plan_data = planning_state_json.get("carbon_network_plan")

    if not network_plan_data:
        # Return empty network plan
        empty_plan = NetworkPlanningState()
        return to_dict(empty_plan)

    return network_plan_data


@app.put("/api/projects/{project_id}/vm-assignments")
async def update_vm_assignments(
    project_id: str,
    assignments: list[VmNetworkAssignmentSchema]
) -> dict[str, Any]:
    """Update VM network assignments from drag-and-drop."""
    _require_persistence()

    project = persistence.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load existing network plan
    planning_state_json = project.get("planning_state_json", {})
    network_plan_data = planning_state_json.get("carbon_network_plan")

    if not network_plan_data:
        raise HTTPException(
            status_code=400,
            detail="Network plan not found. Create network plan first."
        )

    # Update VM assignments
    network_plan_data["vm_assignments"] = [a.dict() for a in assignments]
    planning_state_json["carbon_network_plan"] = network_plan_data

    persistence.update_project_state(project_id, planning_state_json)

    return {
        "status": "success",
        "message": f"Updated {len(assignments)} VM assignments"
    }
    }
