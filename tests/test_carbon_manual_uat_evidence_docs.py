from pathlib import Path


EVIDENCE_INDEX = Path("docs/carbon-manual-uat-evidence-index.md")


def test_carbon_manual_uat_evidence_index_links_required_sources():
    content = EVIDENCE_INDEX.read_text(encoding="utf-8")

    for reference in {
        "carbon-manual-uat-runbook.md",
        "carbon-accessibility-uat-checklist.md",
        "carbon-accessibility-uat-results-template.md",
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
