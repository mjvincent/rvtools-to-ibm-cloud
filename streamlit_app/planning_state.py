import pandas as pd
import streamlit as st

from handoff import (
    extract_image_import_status,
    extract_remediation_tracker,
    generate_planning_state_json,
    load_planning_state_json,
)
from streamlit_app.final_vms import build_final_vms


WAVE_STATE_COLUMNS = [
    "Wave",
    "Cutover Group",
    "Owner",
    "Application",
    "Priority",
    "Dependency Group",
]

DECISION_STATE_COLUMNS = [
    "Exclude?",
    "Override Profile",
    "Override Storage Tier",
    "Network",
    "Subnet",
    "Security Group",
]


def _is_blank(value):
    return value is None or pd.isna(value) or str(value).strip() == ""


def _apply_rows_by_vm_key(updated, rows, columns):
    applied = 0
    skipped = 0
    for row in rows or []:
        vm_key = row.get("VM Key")
        if not vm_key or "VM Key" not in updated.columns:
            skipped += 1
            continue
        mask = updated["VM Key"] == vm_key
        if not mask.any():
            skipped += 1
            continue
        for column in columns:
            if column in row and column in updated.columns:
                updated.loc[mask, column] = row.get(column, "")
        applied += 1
    return updated, applied, skipped


def apply_planning_state_to_dataframe(df, state):
    """Apply saved decisions and wave rows from planning-state to a dataframe."""
    if not isinstance(df, pd.DataFrame):
        return df, {
            "applied": 0,
            "skipped": 0,
            "wave_applied": 0,
            "wave_skipped": 0,
            "decision_applied": 0,
            "decision_skipped": 0,
        }

    updated = df.copy()
    for column in WAVE_STATE_COLUMNS:
        if column not in updated.columns:
            updated[column] = ""
    for column in DECISION_STATE_COLUMNS:
        if column not in updated.columns and column == "Exclude?":
            updated[column] = False

    updated, decision_applied, decision_skipped = _apply_rows_by_vm_key(
        updated,
        state.get("vm_decisions", []),
        DECISION_STATE_COLUMNS,
    )
    updated, wave_applied, wave_skipped = _apply_rows_by_vm_key(
        updated,
        state.get("wave_planning", []),
        WAVE_STATE_COLUMNS,
    )
    return updated, {
        "applied": wave_applied,
        "skipped": wave_skipped,
        "wave_applied": wave_applied,
        "wave_skipped": wave_skipped,
        "decision_applied": decision_applied,
        "decision_skipped": decision_skipped,
    }


def apply_planning_state_to_session(state):
    """Restore planning-state tracker data into Streamlit session state."""
    remediation_tracker = extract_remediation_tracker(state)
    image_import_status = extract_image_import_status(state)
    st.session_state["remediation_tracker"] = remediation_tracker
    st.session_state["image_import_status"] = image_import_status
    return {
        "remediation_items": len(remediation_tracker),
        "image_groups": len(image_import_status),
    }


def summarize_current_planning_state(
    edited_df,
    remediation_tracker=None,
    image_import_status=None,
):
    """Summarize planning-state content before export."""
    if "Exclude?" in edited_df:
        active_df = edited_df[edited_df["Exclude?"] == False]
    else:
        active_df = edited_df
    complete_wave_rows = 0
    for _, row in active_df.iterrows():
        if all(not _is_blank(row.get(column)) for column in WAVE_STATE_COLUMNS[:4]):
            complete_wave_rows += 1
    return {
        "VM Decisions": len(edited_df),
        "Active VMs": len(active_df),
        "Complete Wave Rows": complete_wave_rows,
        "Remediation Rows": len(remediation_tracker or {}),
        "Image Groups": len(image_import_status or {}),
    }


def build_session_safety_rows():
    """Describe what planning state restores and what remains session-only."""
    return [
        {
            "Area": "Restored by planning-state.json",
            "What It Covers": (
                "VM decisions, wave planning, remediation tracker, image import "
                "status, and project metadata."
            ),
            "Recommended Action": (
                "Download planning state before closing, refreshing, switching "
                "machines, or handing work to another teammate."
            ),
        },
        {
            "Area": "Not saved in planning-state.json",
            "What It Covers": (
                "Uploaded RVTools workbook, generated ZIP bytes after closing, "
                "live Streamlit session state, Terraform execution state, and "
                "imported IBM Cloud images."
            ),
            "Recommended Action": (
                "Keep the source RVTools workbook and downloaded Terraform ZIP "
                "in an approved storage location."
            ),
        },
        {
            "Area": "Resume workflow",
            "What It Covers": (
                "Upload the same RVTools workbook, then import planning-state.json "
                "from Export > Planning Downloads."
            ),
            "Recommended Action": (
                "Review the restore summary for applied and skipped rows before "
                "continuing planning."
            ),
        },
    ]


def render_session_safety_guidance():
    """Render planning-state session safety guidance."""
    st.write("### Session Safety")
    st.info(
        "Planning edits live in the current Streamlit session until you "
        "download planning-state.json. The app does not autosave to disk or "
        "cloud storage."
    )
    st.dataframe(
        pd.DataFrame(build_session_safety_rows()),
        hide_index=True,
        width="stretch",
    )


def build_planning_state_restore_summary(
    state,
    dataframe_result=None,
    session_result=None,
):
    """Build human-readable restore summary rows for a loaded state bundle."""
    dataframe_result = dataframe_result or {}
    session_result = session_result or {}
    return [
        {
            "Restored Area": "VM decisions",
            "Applied": dataframe_result.get("decision_applied", 0),
            "Skipped": dataframe_result.get("decision_skipped", 0),
        },
        {
            "Restored Area": "Wave planning",
            "Applied": dataframe_result.get("wave_applied", 0),
            "Skipped": dataframe_result.get("wave_skipped", 0),
        },
        {
            "Restored Area": "Remediation tracker",
            "Applied": session_result.get("remediation_items", 0),
            "Skipped": 0,
        },
        {
            "Restored Area": "Image import status",
            "Applied": session_result.get("image_groups", 0),
            "Skipped": 0,
        },
    ]


def render_planning_state_restore_summary():
    """Render the most recent planning-state restore summary if available."""
    summary = st.session_state.get("planning_state_restore_summary")
    if not summary:
        return
    st.success("Planning state restored.")
    st.dataframe(
        pd.DataFrame(summary),
        hide_index=True,
        width="stretch",
    )


def render_planning_state_controls(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
    project_name,
    target_region,
    target_zone,
):
    """Render planning-state export/import controls."""
    st.write("### Planning State")
    st.info(
        "Save planning state when you need to pause and resume work later. "
        "Reload it after uploading the same RVTools workbook to restore VM "
        "decisions, wave fields, remediation tracking, and image import status."
    )
    render_session_safety_guidance()
    render_planning_state_restore_summary()

    final_vms = build_final_vms(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
    )
    planning_state_json = generate_planning_state_json(
        final_vms,
        remediation_tracker=st.session_state.get("remediation_tracker", {}),
        image_import_status=st.session_state.get("image_import_status", {}),
        metadata={
            "project_name": project_name,
            "target_region": target_region,
            "target_zone": target_zone,
        },
        decision_records=edited_df.to_dict("records"),
    )
    summary = summarize_current_planning_state(
        edited_df,
        st.session_state.get("remediation_tracker", {}),
        st.session_state.get("image_import_status", {}),
    )
    st.dataframe(
        pd.DataFrame([summary]),
        hide_index=True,
        width="stretch",
    )
    st.download_button(
        label="Download Planning State",
        data=planning_state_json.encode("utf-8"),
        file_name=f"{project_name}-planning-state.json",
        mime="application/json",
        width="stretch",
        key="planning_state_download",
    )

    with st.expander("Import planning state"):
        uploaded_state = st.file_uploader(
            "Upload planning-state.json",
            type=["json"],
            key="planning_state_import",
        )
        if st.button("Load Planning State", width="stretch"):
            if uploaded_state is None:
                st.warning("Choose a planning-state JSON file to load.")
            else:
                try:
                    state = load_planning_state_json(uploaded_state)
                    session_result = apply_planning_state_to_session(state)
                    st.session_state["pending_planning_state"] = state
                    st.session_state["planning_state_session_result"] = (
                        session_result
                    )
                    st.session_state["planning_state_import_message"] = (
                        "Loaded planning state with "
                        f"{session_result['remediation_items']} remediation "
                        "items and "
                        f"{session_result['image_groups']} image groups."
                    )
                    st.rerun()
                except (ValueError, TypeError) as exc:
                    st.error(f"Could not load planning state: {exc}")
