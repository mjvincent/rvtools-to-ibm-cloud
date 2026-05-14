import pandas as pd

from ui import merge_decision_edits


def test_merge_decision_edits_handles_duplicate_vm_keys_by_row_order():
    df_table = pd.DataFrame([
        {"VM Key": "app-01", "Exclude?": False, "Override Profile": ""},
        {"VM Key": "app-01", "Exclude?": False, "Override Profile": ""},
    ])
    edited_decisions = pd.DataFrame([
        {"VM Key": "app-01", "Exclude?": True, "Override Profile": "bx2-2x8"},
        {"VM Key": "app-01", "Exclude?": False, "Override Profile": "cx2-2x4"},
    ])

    merged = merge_decision_edits(df_table, edited_decisions)

    assert merged["Exclude?"].tolist() == [True, False]
    assert merged["Override Profile"].tolist() == ["bx2-2x8", "cx2-2x4"]
