from pathlib import Path


HOSTED_READINESS = Path("docs/carbon-hosted-operations-readiness.md")
OPERATIONS_RUNBOOK = Path("docs/carbon-operations-runbook.md")


def test_hosted_operations_readiness_lists_required_gates():
    content = HOSTED_READINESS.read_text(encoding="utf-8")

    for gate in {
        "Health checks",
        "Alerting",
        "Logs",
        "Retention",
        "Backup",
        "Restore",
        "Artifact handling",
        "Access control",
        "Support ownership",
        "Rollback",
    }:
        assert gate in content


def test_hosted_operations_readiness_preserves_fallback_and_data_boundary():
    content = HOSTED_READINESS.read_text(encoding="utf-8")

    assert "Streamlit remains the supported production UI and rollback path" in content
    assert "Uploaded RVTools workbooks" in content
    assert "generated Terraform ZIPs" in content
    assert "sensitive infrastructure data" in content
    assert "/Users/" not in content


def test_hosted_operations_readiness_documents_restore_acceptance():
    content = HOSTED_READINESS.read_text(encoding="utf-8")

    for criterion in {
        "Restore Postgres",
        "Restore artifact storage",
        "Load a restored Carbon project",
        "Generate a Carbon Terraform ZIP",
        "Confirm Streamlit fallback remains available",
    }:
        assert criterion in content


def test_operations_runbook_links_hosted_readiness_checklist():
    content = OPERATIONS_RUNBOOK.read_text(encoding="utf-8")

    assert "Carbon Hosted Operations Readiness Checklist" in content
    assert "carbon-hosted-operations-readiness.md" in content
