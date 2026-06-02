import streamlit as st

from ui import (
    DECISION_COLUMNS,
    DISABLED_COLS,
    apply_preflight_quick_fixes,
    merge_decision_edits,
)


def build_decision_input_columns(decision_table):
    return ["VM Key"] + [
        column for column in DECISION_COLUMNS
        if column in decision_table.columns
    ]


def build_decision_column_order(decision_table):
    return [
        column for column in DECISION_COLUMNS
        if column in decision_table.columns
    ]


def build_disabled_decision_columns(decision_input_columns):
    return [
        column for column in DISABLED_COLS
        if column in decision_input_columns
    ]


def render_vm_review_tab(df_table, table_config):
    st.subheader("VM Decisions")
    st.caption(
        "This view keeps the active decisions in front. Raw generated fields "
        "remain available below for audit and troubleshooting."
    )
    decision_table = apply_preflight_quick_fixes(
        df_table,
        st.session_state.get("preflight_quick_fixes", {}),
    )
    decision_input_columns = build_decision_input_columns(decision_table)
    edited_decisions = st.data_editor(
        decision_table[decision_input_columns],
        column_config=table_config,
        column_order=build_decision_column_order(decision_table),
        disabled=build_disabled_decision_columns(decision_input_columns),
        hide_index=True,
        use_container_width=True,
        key="vm_decision_editor",
    )
    edited_df = merge_decision_edits(decision_table, edited_decisions)
    with st.expander("Advanced generated fields"):
        st.dataframe(edited_df, hide_index=True, use_container_width=True)
    return edited_df
