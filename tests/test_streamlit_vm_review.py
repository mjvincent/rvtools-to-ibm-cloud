import pandas as pd

from streamlit_app.vm_review import (
    build_decision_column_order,
    build_decision_input_columns,
    build_disabled_decision_columns,
)


def test_build_decision_input_columns_keeps_vm_key_and_available_decisions():
    decision_table = pd.DataFrame(
        columns=[
            "VM Key",
            "VM Name",
            "Exclude?",
            "Power State",
            "Override Profile",
            "Unexpected",
        ]
    )

    assert build_decision_input_columns(decision_table) == [
        "VM Key",
        "Exclude?",
        "VM Name",
        "Power State",
        "Override Profile",
    ]


def test_build_decision_column_order_uses_decision_columns_only():
    decision_table = pd.DataFrame(
        columns=[
            "VM Key",
            "VM Name",
            "Exclude?",
            "Power State",
            "Override Profile",
            "Unexpected",
        ]
    )

    assert build_decision_column_order(decision_table) == [
        "Exclude?",
        "VM Name",
        "Power State",
        "Override Profile",
    ]


def test_build_disabled_decision_columns_filters_visible_columns():
    assert build_disabled_decision_columns(
        ["VM Key", "Exclude?", "VM Name", "Override Profile"]
    ) == ["VM Name", "VM Key"]
