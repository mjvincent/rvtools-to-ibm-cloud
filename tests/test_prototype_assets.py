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
    assert "IBMCLOUD_API_KEY: ${IBMCLOUD_API_KEY:-}" in compose_text
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
    assert "/api/projects" in page_text
    assert "carbon-prototype-0.1" in page_text
    assert "Load" in page_text
    assert "Save project" in page_text
    assert "Streamlit remains the supported app" in page_text
    assert (
        ROOT / "prototype" / "carbon-ui" / "e2e" / "carbon-smoke.spec.ts"
    ).exists()


def test_carbon_strategy_documents_parallel_track_and_promotion_gates():
    strategy_text = (
        ROOT / "docs" / "carbon-react-ui-strategy.md"
    ).read_text(encoding="utf-8")

    assert "Keep Streamlit as the production workbench" in strategy_text
    assert "Do not fork the repository" in strategy_text
    assert "prototype/carbon-ui" in strategy_text
    assert "Promotion Gates" in strategy_text
    assert "FastAPI" in strategy_text


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

    assert "run:\n\tscripts/start_local_app.sh" in makefile_text
    assert "start:" in makefile_text
    assert "stop:" in makefile_text
    assert "scripts/start_local_app.sh" in makefile_text
    assert "scripts/stop_local_app.sh" in makefile_text
    assert "compose-up:" in makefile_text
    assert "docker compose up --build --detach" in makefile_text
    assert "compose-pull:" in makefile_text
    assert "ghcr.io/mjvincent/rvtools-to-ibm-cloud:latest" in makefile_text


def test_local_launcher_starts_compose_and_opens_streamlit():
    launcher_text = (
        ROOT / "scripts" / "start_local_app.sh"
    ).read_text(encoding="utf-8")
    stop_text = (
        ROOT / "scripts" / "stop_local_app.sh"
    ).read_text(encoding="utf-8")
    command_text = (ROOT / "start-rvtools.command").read_text(encoding="utf-8")
    stop_command_text = (
        ROOT / "stop-rvtools.command"
    ).read_text(encoding="utf-8")

    assert "docker compose up --build --detach" in launcher_text
    assert "http://localhost:8501" in launcher_text
    assert "/_stcore/health" in launcher_text
    assert "open \"$APP_URL\"" in launcher_text
    assert "docker compose down" in stop_text
    assert "Persistent database and artifact volumes were kept" in stop_text
    assert "scripts/start_local_app.sh" in command_text
    assert "scripts/stop_local_app.sh" in stop_command_text
