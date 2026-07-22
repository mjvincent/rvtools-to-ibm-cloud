from pathlib import Path


DRY_RUN_EVIDENCE = Path("docs/carbon-pilot-dry-run-evidence-2026-07-22.md")


def test_carbon_pilot_dry_run_evidence_records_checked_in_samples_and_results():
    content = DRY_RUN_EVIDENCE.read_text(encoding="utf-8")

    assert "small-sample" in content
    assert "workshop-sample" in content
    assert "23 passed, 1 skipped" in content
    assert "tests/test_carbon_handoff_parity.py" in content
    assert "tests/test_carbon_large_workbook_performance.py" in content


def test_carbon_pilot_dry_run_evidence_keeps_scope_conservative():
    content = DRY_RUN_EVIDENCE.read_text(encoding="utf-8")

    assert "not a human UAT sign-off" in content
    assert "No-go for replacing Streamlit" in content
    assert "does not approve Carbon as the default UI" in content
    assert "Streamlit fallback" in content


def test_carbon_pilot_dry_run_evidence_lists_remaining_promotion_gaps():
    content = DRY_RUN_EVIDENCE.read_text(encoding="utf-8")

    for gap in {
        "Human migration-user UAT",
        "Accessibility sign-off",
        "Hosted operations",
        "Customer-scale validation",
        "Final decision",
    }:
        assert gap in content


def test_carbon_pilot_dry_run_evidence_preserves_sensitive_data_boundary():
    content = DRY_RUN_EVIDENCE.read_text(encoding="utf-8")

    assert "does not include raw RVTools rows" in content
    assert "private workbook paths" in content
    assert "IBM Cloud credentials" in content
    assert "/Users/" not in content
