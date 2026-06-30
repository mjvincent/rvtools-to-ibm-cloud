from pathlib import Path

from fastapi.testclient import TestClient

from prototype.api.app import app


SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"


def test_health_reports_persistence_flag():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["persistence_enabled"] is False


def test_workbook_summary_upload_uses_existing_engine():
    client = TestClient(app)
    sample_path = SAMPLES_DIR / "rvtools-small-complete.xlsx"

    with sample_path.open("rb") as workbook:
        response = client.post(
            "/api/workbooks/summary",
            files={
                "workbook": (
                    sample_path.name,
                    workbook,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["filename"] == "rvtools-small-complete.xlsx"
    assert payload["estate_summary"]["in_scope"] == 2
    assert payload["estate_summary"]["excluded"] == 1
    assert "readiness_counts" in payload
    assert payload["readiness_rows"]
    assert payload["assignment_rows"]
    assignment_row = payload["assignment_rows"][0]
    assert "VM Key" in assignment_row
    assert "VM Name" in assignment_row
    assert "Subnet" in assignment_row
    assert "Security Group" in assignment_row
    assert "Override Storage Tier" in assignment_row
    assert "Wave" in assignment_row
    assert "Disk Details" in assignment_row
    assert "Network Details" in assignment_row
    assert "Configured Memory MiB" in assignment_row
    assert isinstance(assignment_row["Disk Details"], list)
    assert isinstance(assignment_row["Network Details"], list)


def test_workbook_summary_rejects_non_xlsx_upload():
    client = TestClient(app)

    response = client.post(
        "/api/workbooks/summary",
        files={"workbook": ("not-rvtools.txt", b"nope", "text/plain")},
    )

    assert response.status_code == 400
    assert "RVTools .xlsx" in response.json()["detail"]


def test_project_endpoints_require_configured_persistence():
    client = TestClient(app)

    response = client.get("/api/projects")

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]

    response = client.patch(
        "/api/projects/project-1",
        json={"name": "Renamed project", "description": "updated"},
    )

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
