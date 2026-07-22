from pathlib import Path


EVIDENCE_INDEX = Path("docs/carbon-manual-uat-evidence-index.md")
SESSION_WORKSHEET = Path("docs/carbon-uat-session-worksheet.md")


def test_carbon_manual_uat_evidence_index_links_required_sources():
    content = EVIDENCE_INDEX.read_text(encoding="utf-8")

    for reference in {
        "carbon-manual-uat-runbook.md",
        "carbon-accessibility-uat-checklist.md",
        "carbon-accessibility-uat-results-template.md",
        "carbon-uat-session-worksheet.md",
        "carbon-real-workbook-parity-evidence.md",
    }:
        assert reference in content


def test_carbon_manual_uat_evidence_index_names_remaining_manual_reviews():
    content = EVIDENCE_INDEX.read_text(encoding="utf-8")

    for review_area in {
        "Migration-user walkthrough",
        "Screen-reader review",
        "Responsive/high-zoom review",
        "Error recovery",
        "Output acceptability",
        "Pilot decision",
    }:
        assert review_area in content


def test_carbon_manual_uat_evidence_index_preserves_sensitive_data_boundary():
    content = EVIDENCE_INDEX.read_text(encoding="utf-8")

    assert "Do not include raw customer RVTools content" in content
    assert "IBM Cloud credentials" in content
    assert "/Users/" not in content
    assert "Streamlit remains available as fallback" in content


def test_carbon_uat_session_worksheet_covers_review_workflow_and_decision():
    content = SESSION_WORKSHEET.read_text(encoding="utf-8")

    for section in {
        "Session Metadata",
        "Pre-Session Checks",
        "Walkthrough Notes",
        "Accessibility Notes",
        "Error-Recovery Notes",
        "Issues Found",
        "Session Decision",
        "Sensitive-Data Check",
    }:
        assert section in content

    for workflow_step in {
        "Upload workbook",
        "Save project",
        "Complete one keyboard assignment",
        "Complete one drag/drop assignment",
        "Run Export preflight",
        "Preview Terraform package",
        "Download Terraform ZIP",
    }:
        assert workflow_step in content


def test_carbon_uat_session_worksheet_keeps_fallback_and_sensitive_data_boundary():
    content = SESSION_WORKSHEET.read_text(encoding="utf-8")

    assert "Streamlit fallback" in content
    assert "default UI based on this session alone? | No" in content
    assert "IBM Cloud credentials" in content
    assert "private workbook paths" in content
    assert "/Users/" not in content
