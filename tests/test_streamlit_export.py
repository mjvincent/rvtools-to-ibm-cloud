import pandas as pd

from streamlit_app.export import calculate_package_summary


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
