import pandas as pd

from streamlit_app.overview_readiness import (
    calculate_estate_summary,
    calculate_overview_blockers,
)
from ui import calculate_estate_summary as ui_calculate_estate_summary


def test_calculate_estate_summary_counts_active_costs_and_readiness_signals():
    df = pd.DataFrame(
        [
            {
                "Exclude?": False,
                "Monthly Cost": 100.0,
                "Savings (Mo)": 25.0,
                "Image Readiness": "Blocked",
                "Migration Readiness": "Review",
                "Memory Readiness": "Ready",
                "Network Readiness": "Ready",
            },
            {
                "Exclude?": False,
                "Monthly Cost": 50.0,
                "Savings (Mo)": 10.0,
                "Image Readiness": "Ready",
                "Migration Readiness": "Blocked",
                "Memory Readiness": "Review",
                "Network Readiness": "Blocked",
            },
            {
                "Exclude?": True,
                "Monthly Cost": 999.0,
                "Savings (Mo)": 999.0,
                "Image Readiness": "Blocked",
                "Migration Readiness": "Blocked",
                "Memory Readiness": "Blocked",
                "Network Readiness": "Blocked",
            },
        ]
    )

    summary = calculate_estate_summary(df)

    assert summary == {
        "in_scope": 2,
        "excluded": 1,
        "monthly": 150.0,
        "savings": 35.0,
        "blocked": 3,
        "review": 2,
    }
    assert ui_calculate_estate_summary(df) == summary


def test_calculate_overview_blockers_matches_overview_metrics():
    df = pd.DataFrame(
        [
            {
                "Exclude?": False,
                "Image Readiness": "Blocked",
                "Migration Readiness": "Ready",
                "Memory Readiness": "Blocked",
            },
            {
                "Exclude?": False,
                "Image Readiness": "Ready",
                "Migration Readiness": "Blocked",
                "Memory Readiness": "Review",
            },
            {
                "Exclude?": True,
                "Image Readiness": "Blocked",
                "Migration Readiness": "Blocked",
                "Memory Readiness": "Blocked",
            },
        ]
    )

    assert calculate_overview_blockers(df) == {
        "image": 1,
        "migration": 1,
        "memory": 1,
    }
