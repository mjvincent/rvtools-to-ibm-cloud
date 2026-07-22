from pathlib import Path

import yaml


ISSUE_TEMPLATE = Path(".github/ISSUE_TEMPLATE/carbon-pilot-finding.yml")


def _template() -> dict:
    return yaml.safe_load(ISSUE_TEMPLATE.read_text(encoding="utf-8"))


def _field_ids(template: dict) -> set[str]:
    return {
        item["id"]
        for item in template["body"]
        if isinstance(item, dict) and "id" in item
    }


def test_carbon_pilot_issue_template_is_structured_for_github():
    template = _template()

    assert template["name"] == "Carbon pilot finding"
    assert "carbon" in template["labels"]
    assert "pilot-feedback" in template["labels"]
    assert "body" in template


def test_carbon_pilot_issue_template_collects_promotion_finding_fields():
    field_ids = _field_ids(_template())

    for field_id in {
        "severity",
        "workflow",
        "release_candidate",
        "workbook_label",
        "steps",
        "expected",
        "actual",
        "evidence",
        "streamlit_fallback",
        "promotion_impact",
        "mitigation",
        "owner",
        "revisit_date",
        "sensitive_data_check",
    }:
        assert field_id in field_ids


def test_carbon_pilot_issue_template_keeps_sensitive_data_boundary():
    content = ISSUE_TEMPLATE.read_text(encoding="utf-8")

    assert "Do not include raw RVTools rows" in content
    assert "IBM Cloud credentials" in content
    assert "Terraform state" in content
    assert "/Users/" not in content
