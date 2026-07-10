import os

from scripts import collect_carbon_perf_evidence as evidence


def test_workbook_values_from_env_uses_path_separator():
    raw_value = os.pathsep.join([
        "medium-wave=/private/customer-a.xlsx",
        "large-estate=/private/customer-b.xlsx",
        "",
    ])

    assert evidence.workbook_values_from_env(raw_value) == [
        "medium-wave=/private/customer-a.xlsx",
        "large-estate=/private/customer-b.xlsx",
    ]


def test_parse_labeled_workbooks_keeps_paths_out_of_labels():
    labeled_paths = evidence.parse_labeled_workbooks([
        "medium-wave=/private/customer-a.xlsx",
        "/private/customer-b.xlsx",
    ])

    assert labeled_paths[0][0] == "medium-wave"
    assert labeled_paths[0][1].name == "customer-a.xlsx"
    assert labeled_paths[1][0] == "workbook-2"
    assert labeled_paths[1][1].name == "customer-b.xlsx"


def test_render_text_is_sanitized():
    rendered = evidence.render_text([
        {
            "date": "2026-07-10T12:00:00+00:00",
            "branch": "feature/test",
            "commit": "abc1234",
            "workbook_label": "large-estate",
            "assignment_rows": 2500,
            "summary_parse_elapsed_seconds": 12.345,
            "threshold_seconds": 45.0,
            "result": "pass",
            "http_status": 200,
        }
    ])

    assert "large-estate" in rendered
    assert "2500" in rendered
    assert "customer" not in rendered.lower()
    assert ".xlsx" not in rendered
    assert "/private" not in rendered
