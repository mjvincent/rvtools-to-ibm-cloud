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


def apply_planning_state_to_dataframe(df, state):
    """Apply wave planning rows from a planning-state bundle to a dataframe."""
    if not isinstance(df, pd.DataFrame):
        return df, {"applied": 0, "skipped": 0}

    updated = df.copy()
    for column in WAVE_STATE_COLUMNS:
        if column not in updated.columns:
            updated[column] = ""

    applied = 0
    skipped = 0
    for row in state.get("wave_planning", []) or []:
        vm_key = row.get("VM Key")
        if not vm_key or "VM Key" not in updated.columns:
            skipped += 1
            continue
        mask = updated["VM Key"] == vm_key
        if not mask.any():
            skipped += 1
            continue
        for column in WAVE_STATE_COLUMNS:
            if column in row:
                updated.loc[mask, column] = row.get(column, "")
        applied += 1
    return updated, {"applied": applied, "skipped": skipped}


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
    )
    st.download_button(
        label="Download Planning State",
        data=planning_state_json.encode("utf-8"),
        file_name=f"{project_name}-planning-state.json",
        mime="application/json",
        use_container_width=True,
        key="planning_state_download",
    )

    with st.expander("Import planning state"):
        uploaded_state = st.file_uploader(
            "Upload planning-state.json",
            type=["json"],
            key="planning_state_import",
        )
        if st.button("Load Planning State", use_container_width=True):
            if uploaded_state is None:
                st.warning("Choose a planning-state JSON file to load.")
            else:
                try:
                    state = load_planning_state_json(uploaded_state)
                    session_result = apply_planning_state_to_session(state)
                    st.session_state["pending_planning_state"] = state
                    st.session_state["planning_state_import_message"] = (
                        "Loaded planning state with "
                        f"{session_result['remediation_items']} remediation "
                        "items and "
                        f"{session_result['image_groups']} image groups."
                    )
                    st.rerun()
                except (ValueError, TypeError) as exc:
                    st.error(f"Could not load planning state: {exc}")
