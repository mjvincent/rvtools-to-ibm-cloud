from streamlit_app.help_panel import (
    build_help_samples_sections,
    build_workshop_sample_findings,
)


def _help_text():
    return " ".join(
        f"{section['title']} {section['body']}"
        for section in build_help_samples_sections()
    )


def test_help_panel_mentions_bundled_samples():
    text = _help_text()

    assert "rvtools-small-complete.xlsx" in text
    assert "SizingWorkshop-RVTools.xlsx" in text


def test_help_panel_mentions_recommended_workflow():
    text = _help_text()

    assert "Overview" in text
    assert "Readiness" in text
    assert "Migration Ops" in text
    assert "Export package" in text


def test_help_panel_mentions_documentation_references():
    text = _help_text()

    assert "README.md" in text
    assert "docs/user-manual.md" in text
    assert "docs/testing.md" in text
    assert "docs/migration-handoff-package.md" in text
    assert "docs/demo-video-guide.md" in text


def test_help_panel_mentions_tool_boundary():
    text = _help_text()

    assert "generates Terraform" in text
    assert "does not run Terraform" in text
    assert "import images" in text
    assert "perform cutover" in text


def test_workshop_sample_findings_describe_expected_practice_cases():
    text = " ".join(
        f"{finding['title']} {finding['body']}"
        for finding in build_workshop_sample_findings()
    )

    assert "image placeholder" in text
    assert "unknown-net" in text
    assert "wowas3" in text
    assert "network readiness review" in text
    assert "exclude it from the package" in text
