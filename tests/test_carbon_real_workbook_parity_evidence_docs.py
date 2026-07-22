from pathlib import Path


EVIDENCE_DOC = Path("docs/carbon-real-workbook-parity-evidence.md")


def test_carbon_real_workbook_parity_evidence_names_checked_in_samples():
    content = EVIDENCE_DOC.read_text(encoding="utf-8")

    assert "samples/rvtools-small-complete.xlsx" in content
    assert "samples/SizingWorkshop-RVTools.xlsx" in content


def test_carbon_real_workbook_parity_evidence_links_executable_checks():
    content = EVIDENCE_DOC.read_text(encoding="utf-8")

    for test_name in {
        "tests/test_sample_workbooks.py",
        "tests/test_carbon_large_workbook_performance.py",
        "tests/test_carbon_handoff_parity.py",
        "test_carbon_workshop_workbook_unknown_network_subset_matches_streamlit_handoff",
        "test_carbon_workshop_operational_edge_subset_matches_streamlit_handoff",
        "test_carbon_sample_workbook_operational_overlays_match_streamlit_handoff",
        "test_carbon_sample_workbook_api_zip_matches_expected_handoff_inventory",
        "test_carbon_workshop_api_zip_preserves_operational_handoff_evidence",
        "test_carbon_package_preview_matches_api_zip_contents",
    }:
        assert test_name in content


def test_carbon_real_workbook_parity_evidence_keeps_promotion_boundary_clear():
    content = EVIDENCE_DOC.read_text(encoding="utf-8")

    assert "Streamlit remains the supported production UI" in content
    assert "checked-in workbooks do not replace private customer-scale validation" in content
    assert "/Users/" not in content
