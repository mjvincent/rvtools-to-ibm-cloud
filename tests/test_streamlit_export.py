import pandas as pd

from streamlit_app.export import (
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
