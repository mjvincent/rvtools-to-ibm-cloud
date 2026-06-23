import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_compose_declares_persistent_services_and_volumes():
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "rvtools-to-ibm-cloud:local" in compose_text
    assert "build:" in compose_text
    assert "postgres:" in compose_text
    assert "${POSTGRES_PORT:-5432}:5432" in compose_text
    assert "rvtools-artifacts:" in compose_text
    assert "DATABASE_URL:" in compose_text
    assert "ARTIFACT_STORAGE_PATH:" in compose_text
    assert "uvicorn prototype.api.app:app" in compose_text


def test_carbon_ui_prototype_declares_expected_stack_and_workflows():
    package_json = json.loads(
        (ROOT / "prototype" / "carbon-ui" / "package.json").read_text(
            encoding="utf-8"
        )
    )
    page_text = (
        ROOT / "prototype" / "carbon-ui" / "app" / "page.tsx"
    ).read_text(encoding="utf-8")

    assert "@carbon/react" in package_json["dependencies"]
    assert "next" in package_json["dependencies"]
    assert "FileUploaderDropContainer" in page_text
    assert "/api/workbooks/summary" in page_text
    assert "Streamlit remains the supported app" in page_text


def test_github_actions_publish_ghcr_and_smoke_compose():
    workflow_text = (
        ROOT / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")

    assert "ghcr.io/mjvincent/rvtools-to-ibm-cloud" in workflow_text
    assert "docker/build-push-action" in workflow_text
    assert "Docker Compose persistence smoke test" in workflow_text
    assert "docker compose up --detach" in workflow_text


def test_makefile_compose_up_builds_persistent_stack():
    makefile_text = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "compose-up:" in makefile_text
    assert "docker compose up --build --detach" in makefile_text
    assert "compose-pull:" in makefile_text
    assert "ghcr.io/mjvincent/rvtools-to-ibm-cloud:latest" in makefile_text
