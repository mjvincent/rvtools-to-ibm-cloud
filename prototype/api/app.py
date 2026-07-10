"""Thin FastAPI prototype around the existing RVTools planning engine."""

from __future__ import annotations

import io
import json
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import logging

from catalog_pricing import get_pricing_catalog
from rvtools_parser import parse_rvtools_workbook
from streamlit_app.overview_readiness import (
    READINESS_STATUS_COLUMNS,
    calculate_estate_summary,
    calculate_overview_blockers,
)
from terraform_carbon_renderer import render_networking_from_carbon_plan
from terraform_carbon_renderer_modular import render_modular_terraform_from_carbon_plan
from terraform_readme_generator import generate_modular_terraform_readme

from . import persistence
from .carbon_handoff import (
    carbon_decision_audit_csv,
    carbon_decision_audit_records,
    carbon_full_handoff_files,
    carbon_preflight_findings,
    carbon_state_native_handoff_files,
)
from preflight import summarize_preflight


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
    target_zone: str = DEFAULT_ZONE
    project_name: str = ""


# Import network planning schemas
from .schemas import NetworkPlanningStateSchema, VmNetworkAssignmentSchema
from models.network_planning import NetworkPlanningState, from_dict, to_dict


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RVTools to IBM Cloud Prototype API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    logger.error(f"Request body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())}
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


def _load_carbon_project_plan(project_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], NetworkPlanningState]:
    _require_persistence()

    project = persistence.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_state = persistence.get_project_state(project_id)
    if not project_state:
        raise HTTPException(
            status_code=400,
            detail="Project state not found. Save the project first.",
        )

    planning_state_json = project_state.get("planning_state_json", {})
    network_plan_data = planning_state_json.get("carbon_network_plan")
    if not network_plan_data:
        raise HTTPException(
            status_code=400,
            detail="Network plan not found. Create network plan first.",
        )

    try:
        network_plan = from_dict(network_plan_data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid network plan data: {exc}",
        ) from exc

    if not network_plan.vpcs:
        raise HTTPException(
            status_code=400,
            detail="Network plan must contain at least one VPC",
        )

    return project, project_state, planning_state_json, network_plan


def _render_carbon_terraform_files(
    project: dict[str, Any],
    project_state: dict[str, Any],
    network_plan: NetworkPlanningState,
) -> dict[str, str]:
    target_region = project_state.get("target_region", "us-south")
    target_zone = project_state.get("target_zone", "us-south-1")
    project_name = project.get("name", "carbon-migration")
    try:
        terraform_files = render_modular_terraform_from_carbon_plan(
            network_plan,
            project_name=project_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Terraform generation failed: {exc}",
        ) from exc
    terraform_files["README.md"] = generate_modular_terraform_readme(
        project_name=project_name,
        target_region=target_region,
        target_zone=target_zone,
        vpc_count=len(network_plan.vpcs),
        subnet_count=len(network_plan.subnets),
        vm_count=len(network_plan.vm_assignments),
        has_ssh_key=bool(network_plan.metadata.ssh_public_key),
        backend_type=network_plan.metadata.backend_type or "local",
    )
    return terraform_files


def _build_carbon_package_files(
    project: dict[str, Any],
    project_state: dict[str, Any],
    planning_state_json: dict[str, Any],
    network_plan: NetworkPlanningState,
) -> dict[str, str]:
    """Build the full Carbon Terraform ZIP file inventory."""
    target_region = project_state.get("target_region", "us-south")
    package_files = _render_carbon_terraform_files(
        project,
        project_state,
        network_plan,
    )
    package_files["network-plan.json"] = json.dumps(
        planning_state_json.get("carbon_network_plan"),
        indent=2,
    )
    pricing_catalog = get_pricing_catalog("static", region=target_region)
    package_files["decision-audit.csv"] = carbon_decision_audit_csv(
        network_plan,
        planning_state_json,
        pricing_catalog,
    )
    package_files.update(
        carbon_state_native_handoff_files(
            network_plan,
            planning_state_json,
        )
    )
    package_files.update(
        carbon_full_handoff_files(
            network_plan,
            planning_state_json,
            pricing_catalog,
        )
    )
    return package_files


TERRAFORM_PACKAGE_PREVIEW_FILES = {
    "README.md",
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "provider.tf",
    "versions.tf",
    "terraform.tfvars.example",
    "modules/networking/main.tf",
    "modules/networking/variables.tf",
    "modules/networking/outputs.tf",
    "modules/vsi/main.tf",
    "modules/vsi/variables.tf",
    "modules/vsi/outputs.tf",
    "modules/storage/main.tf",
    "modules/storage/variables.tf",
    "modules/storage/outputs.tf",
}


def _package_preview_category(path: str) -> str:
    if path in TERRAFORM_PACKAGE_PREVIEW_FILES:
        return "Terraform"
    if path == "network-plan.json":
        return "Carbon state"
    return "Migration handoff"


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
    "Original Specs",
    "IBM Profile",
    "Override Profile",
    "Storage Tier",
    "Override Storage Tier",
    "Network",
    "Subnet",
    "Security Group",
    "Power State",
    "Guest OS",
    "Source IP",
    "Datacenter",
    "Cluster",
    "Host",
    "Disk Count",
    "Data Disk Count",
    "Total Storage GB",
    "Firmware",
    "Boot Disk GB",
    "Configured Memory MiB",
    "Active Memory MiB",
    "Consumed Memory MiB",
    "Ballooned Memory MiB",
    "Swapped Memory MiB",
    "Memory Reservation MiB",
    "Memory Limit MiB",
    "Memory Hot Add",
    "Sizing Memory MiB",
    "Memory Sizing Basis",
    "Disk Details",
    "Partition Details",
    "Partition Count",
    "Unmatched Partition Count",
    "Network Details",
    "Readiness Findings",
    "Network Readiness Findings",
    "Compute (Mo)",
    "Storage (Mo)",
    "Monthly Cost",
    "Baseline Cost (Mo)",
    "Savings (Mo)",
    "Pricing Source",
    "Pricing Confidence",
    "Pricing Last Updated",
    "Pricing Status",
    "Profile Hourly",
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
    rows = active[ASSIGNMENT_COLUMNS].to_dict("records")
    for index, row in enumerate(rows):
        for column, value in list(row.items()):
            if value is None:
                row[column] = ""
            elif not isinstance(value, (list, dict)) and pd.isna(value):
                row[column] = ""
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
    }


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
        plan_dict = network_plan.model_dump()
        # Validate by creating NetworkPlanningState
        validated_plan = from_dict(plan_dict)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid network plan: {exc}"
        )

    # Get existing project state or create new one
    project_state = persistence.get_project_state(project_id)
    if project_state:
        planning_state_json = project_state.get("planning_state_json", {})
    else:
        planning_state_json = {}

    # Save network plan
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

    project_state = persistence.get_project_state(project_id)
    planning_state_json = project_state.get("planning_state_json", {}) if project_state else {}
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
    project_state = persistence.get_project_state(project_id)
    planning_state_json = project_state.get("planning_state_json", {}) if project_state else {}
    network_plan_data = planning_state_json.get("carbon_network_plan")

    if not network_plan_data:
        raise HTTPException(
            status_code=400,
            detail="Network plan not found. Create network plan first."
        )

    # Update VM assignments
    network_plan_data["vm_assignments"] = [a.model_dump() for a in assignments]
    planning_state_json["carbon_network_plan"] = network_plan_data

    persistence.update_project_state(project_id, planning_state_json)

    return {
        "status": "success",
        "message": f"Updated {len(assignments)} VM assignments"
    }



@app.post("/api/projects/{project_id}/preflight")
async def run_carbon_project_preflight(project_id: str) -> dict[str, Any]:
    """Run package preflight against saved Carbon network planning state."""
    project, project_state, planning_state_json, network_plan = (
        _load_carbon_project_plan(project_id)
    )
    target_region = project_state.get("target_region", "us-south")
    pricing_catalog = get_pricing_catalog("static", region=target_region)
    records = carbon_decision_audit_records(network_plan, planning_state_json)
    findings = carbon_preflight_findings(network_plan, records, pricing_catalog)
    return {
        "project_id": project_id,
        "project_name": project.get("name", "carbon-migration"),
        "summary": summarize_preflight(findings),
        "findings": [finding.to_record() for finding in findings],
    }


@app.post("/api/projects/{project_id}/terraform/preview")
async def preview_terraform_package(project_id: str) -> dict[str, Any]:
    """Preview the full Terraform package inventory from Carbon planning state."""
    project, project_state, planning_state_json, network_plan = (
        _load_carbon_project_plan(project_id)
    )
    package_files = _build_carbon_package_files(
        project,
        project_state,
        planning_state_json,
        network_plan,
    )
    preview_order = [
        "README.md",
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "provider.tf",
        "versions.tf",
        "terraform.tfvars.example",
        "modules/networking/main.tf",
        "modules/networking/variables.tf",
        "modules/networking/outputs.tf",
        "modules/vsi/main.tf",
        "modules/vsi/variables.tf",
        "modules/vsi/outputs.tf",
        "modules/storage/main.tf",
        "modules/storage/variables.tf",
        "modules/storage/outputs.tf",
        "migration-manifest.json",
        "assessment-quality.json",
        "assessment-quality.csv",
        "preflight-report.json",
        "preflight-report.csv",
        "pricing-diagnostics.json",
        "pricing-diagnostics.csv",
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
        "planning-state.json",
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
        "image-import-variables.tfvars.example",
        "migration-runbook.md",
        "network-plan.json",
    ]
    ordered_paths = [
        *[path for path in preview_order if path in package_files],
        *sorted(path for path in package_files if path not in preview_order),
    ]
    return {
        "project_id": project_id,
        "project_name": project.get("name", "carbon-migration"),
        "files": [
            {
                "path": path,
                "category": _package_preview_category(path),
                "size_bytes": len(package_files[path].encode("utf-8")),
                "content": package_files[path],
            }
            for path in ordered_paths
        ],
    }


@app.post("/api/projects/{project_id}/terraform")
async def generate_terraform_package(project_id: str) -> StreamingResponse:
    """Generate Terraform ZIP package from Carbon network planning state."""
    project, project_state, planning_state_json, network_plan = (
        _load_carbon_project_plan(project_id)
    )

    project_name = project.get("name", "carbon-migration")

    package_files = _build_carbon_package_files(
        project,
        project_state,
        planning_state_json,
        network_plan,
    )

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in package_files.items():
            zip_file.writestr(file_path, content)

    zip_buffer.seek(0)

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"{project_name}-terraform-{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _generate_carbon_terraform_readme(
    project_name: str,
    target_region: str,
    target_zone: str,
    vpc_count: int,
    subnet_count: int,
    vm_count: int,
) -> str:
    """Generate README for Carbon-generated Terraform package."""
    return f"""# Terraform Package: {project_name}

Generated from Carbon UI network planning workbench.

## Package Contents

- **main.tf**: VPC, subnet, security group, and VSI resources
- **variables.tf**: Input variable declarations
- **outputs.tf**: Output value declarations
- **network-plan.json**: Original Carbon network planning state (reference)

## Configuration

- **Region**: {target_region}
- **Zone**: {target_zone}
- **VPCs**: {vpc_count}
- **Subnets**: {subnet_count}
- **VMs**: {vm_count}

## Prerequisites

1. IBM Cloud CLI with VPC plugin
2. Terraform >= 1.0
3. IBM Cloud API key with VPC permissions
4. Custom images imported to IBM Cloud (if using custom images)

## Deployment Steps

### 1. Review Configuration

Review the generated Terraform files and ensure they match your requirements:

```bash
cat main.tf
cat variables.tf
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Validate Configuration

```bash
terraform validate
terraform fmt -check
```

### 4. Plan Deployment

```bash
terraform plan
```

Review the plan output carefully. Terraform will show:
- Resources to be created
- Estimated costs (if available)
- Any configuration issues

### 5. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm deployment.

### 6. Verify Deployment

```bash
terraform show
terraform output
```

## Network Architecture

This Terraform package creates:

- **VPC(s)**: Isolated virtual private clouds
- **Subnets**: Network segments within VPCs
- **Security Groups**: Firewall rules for VMs
- **VSIs**: Virtual server instances assigned to subnets
- **Network Components**: Public gateways, load balancers, VPE gateways (if configured)

## Customization

### Variables

You can override default values by creating a `terraform.tfvars` file:

```hcl
# terraform.tfvars
ibmcloud_api_key = "your-api-key-here"
resource_group = "your-resource-group"
```

### Image IDs

If using custom images, update the image IDs in the VSI resources after importing images to IBM Cloud.

## Troubleshooting

### Authentication Issues

Ensure your IBM Cloud API key is set:

```bash
export IC_API_KEY="your-api-key"
```

### Resource Quota

Verify you have sufficient quota for:
- VPCs
- Subnets
- Floating IPs
- VSIs

Check quota in IBM Cloud Console → VPC Infrastructure → Overview

### State Management

Terraform state is stored locally by default. For team collaboration, consider:
- IBM Cloud Schematics (managed Terraform)
- Remote state backend (S3, Terraform Cloud)

## Support

For issues with:
- **Terraform syntax**: Review Terraform documentation
- **IBM Cloud resources**: Check IBM Cloud VPC documentation
- **Carbon UI**: Contact the migration planning team

## Generated

- **Date**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Source**: Carbon UI Network Planning Workbench
- **Project**: {project_name}
"""
