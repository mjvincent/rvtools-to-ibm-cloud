import pandas as pd

from preflight import PreflightFinding
from streamlit_app.export import (
    build_bundle_contents_preview_rows,
    build_export_readiness_checklist,
    build_terraform_validation_guidance,
    calculate_package_summary,
    summarize_export_readiness_statuses,
)


def test_calculate_package_summary_counts_active_vms_and_blockers():
    edited_df = pd.DataFrame(
        [
            {
                "Exclude?": False,
                "Image Readiness": "Blocked",
                "Migration Readiness": "Ready",
                "Memory Readiness": "Review",
            },
            {
                "Exclude?": False,
                "Image Readiness": "Ready",
                "Migration Readiness": "Blocked",
                "Memory Readiness": "Blocked",
            },
            {
                "Exclude?": True,
                "Image Readiness": "Blocked",
                "Migration Readiness": "Blocked",
                "Memory Readiness": "Blocked",
            },
        ]
    )

    summary = calculate_package_summary(
        edited_df,
        [{"name": "VM Network"}, {"name": "App Network"}],
    )

    assert summary == (2, 3, 2)


def test_terraform_validation_guidance_lists_expected_modes():
    rows = build_terraform_validation_guidance()

    modes = [row["Mode"] for row in rows]

    assert modes == [
        "Package Preflight",
        "Offline Format Check",
        "Strict Init Validate",
        "Local Provider Download Tolerance",
    ]
    assert "does not execute" not in str(rows).lower()
    assert any("--init-validate" in row["Command Or Action"] for row in rows)
    assert any(
        "--allow-provider-download-failure" in row["Command Or Action"]
        for row in rows
    )


def test_bundle_contents_preview_includes_terraform_files_and_modules():
    text = " ".join(
        f"{row['File Or Folder']} {row['Purpose']} {row['Primary Owner']}"
        for row in build_bundle_contents_preview_rows()
    )

    assert "README.md" in text
    assert "Root Terraform files" in text
    assert "modules/networking/" in text
    assert "modules/storage/" in text
    assert "modules/vsi/" in text


def test_bundle_contents_preview_includes_handoff_reports():
    text = " ".join(
        f"{row['File Or Folder']} {row['Purpose']}"
        for row in build_bundle_contents_preview_rows()
    )

    assert "vm-mapping.csv" in text
    assert "nic-mapping.csv" in text
    assert "disk-mapping.csv" in text
    assert "readiness-findings.csv" in text
    assert "preflight-report.csv/json" in text
    assert "pricing-diagnostics.csv/json" in text
    assert "cutover-readiness.csv" in text


def test_bundle_contents_preview_includes_resume_and_operator_files():
    text = " ".join(
        f"{row['File Or Folder']} {row['Purpose']}"
        for row in build_bundle_contents_preview_rows()
    )

    assert "planning-state.json" in text
    assert "image-import-variables.tfvars.example" in text
    assert "migration-manifest.json" in text
    assert "migration-runbook.md" in text
    assert "Reloadable app planning state" in text


def _readiness_df(**overrides):
    row = {
        "Exclude?": False,
        "VM Name": "app-01",
        "Original Specs": "rhel-template",
        "Image Readiness": "Ready",
        "Migration Readiness": "Ready",
        "Memory Readiness": "Ready",
        "Wave": "wave-01",
        "Cutover Group": "cg-app",
        "Owner": "app-team",
        "Application": "orders",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _by_area(rows):
    return {row["Area"]: row for row in rows}


def test_export_readiness_checklist_has_stable_columns():
    rows = build_export_readiness_checklist(_readiness_df())

    assert list(rows[0]) == [
        "Area",
        "Status",
        "Signal",
        "Recommended Next Action",
    ]


def test_export_readiness_checklist_blocks_on_readiness_blockers():
    rows = build_export_readiness_checklist(
        _readiness_df(**{"Image Readiness": "Blocked"}),
    )

    readiness = _by_area(rows)["Readiness blockers"]

    assert readiness["Status"] == "Blocked"
    assert readiness["Signal"] == "1 blocker signal(s)"


def test_export_readiness_checklist_reviews_missing_wave_fields():
    rows = build_export_readiness_checklist(
        _readiness_df(Wave=""),
    )

    wave = _by_area(rows)["Wave planning"]

    assert wave["Status"] == "Review"
    assert "1 active VM" in wave["Signal"]


def test_export_readiness_checklist_reviews_non_imported_images():
    rows = build_export_readiness_checklist(
        _readiness_df(),
        image_import_status={
            "rhel-template": {"import_status": "Pending"},
        },
    )

    image = _by_area(rows)["Image import status"]

    assert image["Status"] == "Review"
    assert image["Signal"] == "1 image group(s) not marked Imported"


def test_export_readiness_checklist_marks_complete_planning_ready():
    rows = build_export_readiness_checklist(
        _readiness_df(),
        image_import_status={
            "rhel-template": {"import_status": "Imported"},
        },
        preflight_findings=[],
    )
    by_area = _by_area(rows)

    assert by_area["Readiness blockers"]["Status"] == "Ready"
    assert by_area["Wave planning"]["Status"] == "Ready"
    assert by_area["Image import status"]["Status"] == "Ready"
    assert by_area["Package preflight"]["Status"] == "Ready"


def test_export_readiness_checklist_reports_preflight_findings():
    rows = build_export_readiness_checklist(
        _readiness_df(),
        preflight_findings=[
            PreflightFinding(
                "blocker",
                "cidr",
                "app-net",
                "Invalid CIDR",
            ),
            PreflightFinding(
                "warning",
                "custom_image",
                "app-01",
                "Image placeholder",
            ),
        ],
    )

    preflight = _by_area(rows)["Package preflight"]

    assert preflight["Status"] == "Blocked"
    assert preflight["Signal"] == "1 blocker(s), 1 warning(s)"


def test_export_readiness_status_summary_counts_display_states():
    rows = [
        {"Status": "Ready"},
        {"Status": "Ready"},
        {"Status": "Review"},
        {"Status": "Blocked"},
        {"Status": "Unexpected"},
    ]

    assert summarize_export_readiness_statuses(rows) == {
        "Ready": 2,
        "Review": 1,
        "Blocked": 1,
        "Unexpected": 1,
    }
