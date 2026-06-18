import pandas as pd

from streamlit_app.export import (
    build_bundle_contents_preview_rows,
    build_terraform_validation_guidance,
    calculate_package_summary,
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
