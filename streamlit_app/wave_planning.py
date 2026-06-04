import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError


WAVE_PLANNING_COLUMNS = [
    "Wave",
    "Cutover Group",
    "Owner",
    "Application",
    "Priority",
    "Dependency Group",
]

WAVE_DISPLAY_COLUMNS = [
    "VM Key",
    "VM Name",
    "Wave",
    "Cutover Group",
    "Owner",
    "Application",
    "Priority",
    "Dependency Group",
]

REQUIRED_WAVE_COLUMNS = ["Wave", "Cutover Group", "Owner", "Application"]


def active_wave_dataframe(df):
    """Return active VMs with wave planning columns available."""
    active_df = df[~df["Exclude?"]].copy()
    for column in WAVE_PLANNING_COLUMNS:
        if column not in active_df.columns:
            active_df[column] = "" if column != "Priority" else "Medium"
    return active_df


def apply_wave_fields(df, selected_vms, assignments):
    """Apply non-empty wave planning assignments to selected VM keys."""
    updated = df.copy()
    for vm_key in selected_vms:
        mask = updated["VM Key"] == vm_key
        for column, value in assignments.items():
            if value:
                updated.loc[mask, column] = value
    return updated


def persist_wave_editor_edits(df, wave_editor):
    """Persist editable wave planning rows back to the full decision table."""
    if not isinstance(wave_editor, pd.DataFrame):
        return df

    updated = df.copy()
    for row in wave_editor.to_dict("records"):
        vm_key = row.get("VM Key")
        mask = updated["VM Key"] == vm_key
        for column in WAVE_PLANNING_COLUMNS:
            if column in row:
                updated.loc[mask, column] = row.get(column)
    return updated


def build_wave_planning_export(df):
    """Return active VM wave planning rows for CSV export."""
    active_df = active_wave_dataframe(df)
    return active_df[WAVE_DISPLAY_COLUMNS].copy()


def read_wave_planning_csv(uploaded_file):
    """Read a saved wave planning CSV into a dataframe."""
    try:
        return pd.read_csv(uploaded_file).fillna("")
    except (EmptyDataError, UnicodeDecodeError, ValueError):
        return pd.DataFrame()


def import_wave_planning_csv(df, imported_df):
    """Apply saved wave planning rows to the current decision dataframe."""
    if not isinstance(imported_df, pd.DataFrame) or imported_df.empty:
        return df, {"applied": 0, "skipped": 0}

    updated = df.copy()
    for column in WAVE_PLANNING_COLUMNS:
        if column not in updated.columns:
            updated[column] = ""

    applied = 0
    skipped = 0
    for row in imported_df.to_dict("records"):
        vm_key = row.get("VM Key")
        if not vm_key or "VM Key" not in updated.columns:
            skipped += 1
            continue
        mask = updated["VM Key"] == vm_key
        if not mask.any():
            skipped += 1
            continue
        for column in WAVE_PLANNING_COLUMNS:
            if column in row:
                updated.loc[mask, column] = row.get(column, "")
        applied += 1
    return updated, {"applied": applied, "skipped": skipped}


def detect_app_cutover_conflicts(active_df):
    """Return applications mapped to more than one cutover group."""
    if "Application" not in active_df.columns:
        return []

    conflicts = []
    for application, group in active_df.groupby("Application"):
        values = set(group["Cutover Group"].dropna().astype(str).unique())
        values = {value for value in values if value}
        if len(values) > 1:
            conflicts.append((application, sorted(values)))
    return conflicts


def detect_dependency_wave_conflicts(active_df):
    """Return dependency groups mapped to more than one wave."""
    if "Dependency Group" not in active_df.columns:
        return []

    conflicts = []
    for dependency, group in active_df.groupby("Dependency Group"):
        values = set(group["Wave"].dropna().astype(str).unique())
        values = {value for value in values if value}
        if len(values) > 1:
            conflicts.append((dependency, sorted(values)))
    return conflicts


def wave_completion_status(df):
    """Return completion counts for required wave planning fields."""
    active_df = df[~df["Exclude?"]]
    total = len(active_df)
    complete = 0
    for _, row in active_df.iterrows():
        if all(row.get(column) not in (None, "") for column in REQUIRED_WAVE_COLUMNS):
            complete += 1
    return {
        "total": total,
        "complete": complete,
        "incomplete": total - complete,
        "status": "Complete" if total and complete == total else "Incomplete",
    }


def _wave_column_config(table_config):
    wave_table_cfg = dict(table_config)
    wave_table_cfg.update({
        "VM Key": st.column_config.TextColumn("VM Key", disabled=True),
        "VM Name": st.column_config.TextColumn("VM Name", disabled=True),
        "Wave": st.column_config.TextColumn("Wave"),
        "Cutover Group": st.column_config.TextColumn("Cutover Group"),
        "Owner": st.column_config.TextColumn("Owner"),
        "Application": st.column_config.TextColumn("Application"),
        "Priority": st.column_config.SelectboxColumn(
            "Priority", options=["", "High", "Medium", "Low"]
        ),
        "Dependency Group": st.column_config.TextColumn("Dependency Group"),
    })
    return wave_table_cfg


def render_wave_planning_tab(edited_df, table_config):
    """Render Wave Planning and return the edited decision dataframe."""
    st.subheader("Wave Planning")
    st.caption(
        "Bulk assign waves, cutover groups, owners, and applications to active VMs."
    )

    active_df = active_wave_dataframe(edited_df)

    st.write("### Select VMs to assign")
    vm_options = active_df["VM Key"].tolist()
    selected = st.multiselect(
        "Select VMs (by VM Key)",
        vm_options,
        default=st.session_state.get("wave_selected_vms", []),
        help="Choose active VMs that should receive the same wave planning values.",
    )
    st.session_state["wave_selected_vms"] = selected

    c1, c2, c3 = st.columns([2, 2, 6])
    with c1:
        assign_wave_value = st.text_input(
            "Quick Wave Value",
            "",
            help="Wave label to apply to every active VM, such as Wave 1 or Pilot.",
        )
        if st.button("Assign All to Wave", use_container_width=True):
            if assign_wave_value:
                edited_df = apply_wave_fields(
                    edited_df,
                    active_df["VM Key"].tolist(),
                    {"Wave": assign_wave_value},
                )
                st.success(
                    f"Assigned wave '{assign_wave_value}' to all active VMs"
                )
            else:
                st.warning("Enter a Wave value to assign to all active VMs.")
    with c2:
        if st.button("Assign Wave", use_container_width=True):
            st.session_state["show_assign_wave_form"] = True
    with c3:
        st.write("")

    if st.session_state.get("show_assign_wave_form"):
        with st.form("assign_wave_form"):
            st.write("Assign fields to selected VMs")
            field_wave = st.text_input(
                "Wave",
                help="Migration wave or sprint label used to group VMs for planning.",
            )
            field_cutover = st.text_input(
                "Cutover Group",
                help="Operational cutover batch, often smaller than a wave and aligned to an application or dependency group.",
            )
            field_owner = st.text_input(
                "Owner",
                help="Person, team, or application owner accountable for validating this VM before migration.",
            )
            field_application = st.text_input(
                "Application",
                help="Application or service name used to group related workloads for migration review.",
            )
            submitted = st.form_submit_button("Apply to Selected VMs")
            if submitted:
                if not selected:
                    st.warning("No VMs selected for assignment.")
                else:
                    edited_df = apply_wave_fields(
                        edited_df,
                        selected,
                        {
                            "Wave": field_wave,
                            "Cutover Group": field_cutover,
                            "Owner": field_owner,
                            "Application": field_application,
                        },
                    )
                    st.success(f"Assigned fields to {len(selected)} VMs")
                    st.session_state["show_assign_wave_form"] = False

    with st.expander("Import or export wave planning CSV"):
        wave_export_df = build_wave_planning_export(edited_df)
        st.download_button(
            label="Download Wave Planning CSV",
            data=wave_export_df.to_csv(index=False).encode("utf-8"),
            file_name="wave-planning.csv",
            mime="text/csv",
            use_container_width=True,
            key="wave_planning_csv_download",
        )
        uploaded_wave = st.file_uploader(
            "Upload wave planning CSV",
            type=["csv"],
            key="wave_planning_csv_import",
        )
        if st.button("Load Wave Planning CSV", use_container_width=True):
            if uploaded_wave is None:
                st.warning("Choose a wave planning CSV to load.")
            else:
                imported_df = read_wave_planning_csv(uploaded_wave)
                edited_df, result = import_wave_planning_csv(
                    edited_df,
                    imported_df,
                )
                st.success(
                    "Loaded wave planning for "
                    f"{result['applied']} VMs"
                    + (
                        f"; skipped {result['skipped']} unmatched rows."
                        if result["skipped"] else "."
                    )
                )
                active_df = active_wave_dataframe(edited_df)

    wave_editor = st.data_editor(
        active_df[WAVE_DISPLAY_COLUMNS],
        column_config=_wave_column_config(table_config),
        hide_index=True,
        use_container_width=True,
        key="wave_planning_editor",
    )
    edited_df = persist_wave_editor_edits(edited_df, wave_editor)

    st.write("### Conflict Detection")
    for application, values in detect_app_cutover_conflicts(active_df):
        st.warning(
            f"Application '{application}' has multiple Cutover Groups: "
            f"{', '.join(values)}"
        )

    for dependency, values in detect_dependency_wave_conflicts(active_df):
        st.warning(
            f"Dependency Group '{dependency}' spans multiple Waves: "
            f"{', '.join(values)}"
        )

    completion = wave_completion_status(edited_df)
    if completion["total"]:
        if completion["complete"] == completion["total"]:
            st.success(
                f"Complete: {completion['complete']}/{completion['total']} VMs"
            )
        else:
            st.info(
                f"Incomplete: {completion['complete']}/{completion['total']} VMs"
            )

    with st.expander("Advanced wave planning data"):
        st.dataframe(
            edited_df[WAVE_DISPLAY_COLUMNS],
            hide_index=True,
            use_container_width=True,
        )

    return edited_df
