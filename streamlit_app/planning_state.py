import json
from datetime import datetime

import pandas as pd
import streamlit as st

from handoff import (
    extract_image_import_status,
    extract_remediation_tracker,
    generate_planning_state_json,
    load_planning_state_json,
)
from streamlit_app.final_vms import build_final_vms

try:
    from prototype.api import persistence
except ImportError:
    persistence = None


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


def database_persistence_available():
    """Return True when database-backed project state can be used."""
    if persistence is None:
        return False
    return persistence.persistence_enabled()


def database_persistence_status():
    """Return database persistence status and an optional diagnostic message."""
    if persistence is None:
        return "unavailable", "Persistence helpers are not importable."
    if not persistence.persistence_enabled():
        return "not_configured", "DATABASE_URL is not configured."
    try:
        persistence.initialize_schema()
        return "ready", ""
    except Exception as exc:
        return "error", str(exc)


def _render_database_save_unavailable(status, message):
    """Explain why database save is unavailable without hiding the action."""
    st.button(
        "Save To Database",
        width="stretch",
        disabled=True,
        help="Requires the Docker Compose stack or a running Postgres DATABASE_URL.",
    )
    if status == "not_configured":
        st.info(
            "Database save is not enabled in this running app session because "
            "`DATABASE_URL` is not configured."
        )
        st.caption("Use one of these database-backed launch paths:")
        st.code("docker compose up --build --detach", language="bash")
        st.caption(
            "Then open http://localhost:8501. If you are running Streamlit "
            "from the local virtualenv, start it with:"
        )
        st.code(
            "DATABASE_URL=postgresql://rvtools:rvtools@localhost:5432/rvtools \\\n"
            "ARTIFACT_STORAGE_PATH=.local-artifacts \\\n"
            "venv/bin/python -m streamlit run app.py",
            language="bash",
        )
    else:
        st.error("Database save is configured but unavailable.")
        st.caption(message)
        st.warning(
            "To avoid losing progress: download planning-state.json now, "
            "keep the source RVTools workbook, restart the database or "
            "Docker Compose stack, then upload the same workbook and import "
            "planning-state.json."
        )


def build_current_planning_state_json(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
    project_name,
    target_region,
    target_zone,
):
    """Build planning-state JSON for the current Streamlit planning view."""
    final_vms = build_final_vms(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
    )
    return generate_planning_state_json(
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


def _save_planning_state_to_database(
    planning_state_json,
    project_name,
    target_region,
    target_zone,
    save_name=None,
    description="",
    project_id=None,
):
    state = json.loads(planning_state_json)
    if project_id:
        saved_project_id = project_id
    else:
        project = persistence.create_project(
            (save_name or project_name).strip(),
            description.strip(),
        )
        saved_project_id = project["id"]
    persistence.save_project_state(
        saved_project_id,
        state,
        target_region=target_region,
        target_zone=target_zone,
        project_name=project_name,
    )
    return saved_project_id


def _project_options(projects):
    return {
        f"{project['name']} ({project['id'][:8]})": project["id"]
        for project in projects
    }


def _load_database_project_state(project_id):
    state_row = persistence.get_project_state(project_id)
    if not state_row:
        st.warning("This project does not have saved planning state yet.")
        return
    state = state_row.get("planning_state_json") or {}
    session_result = apply_planning_state_to_session(state)
    st.session_state["pending_planning_state"] = state
    st.session_state["planning_state_session_result"] = session_result
    st.session_state["planning_state_import_message"] = (
        "Loaded database project with "
        f"{session_result['remediation_items']} remediation items and "
        f"{session_result['image_groups']} image groups."
    )
    st.rerun()


def render_database_project_controls(
    planning_state_json,
    project_name,
    target_region,
    target_zone,
):
    """Render optional database save/load controls for Streamlit projects."""
    st.write("### Database Project Save/Load")
    if not database_persistence_available():
        st.info(
            "Database project save/load is disabled. Set DATABASE_URL and "
            "ARTIFACT_STORAGE_PATH, or run the Docker Compose stack, to save "
            "planning state to Postgres."
        )
        return

    try:
        persistence.initialize_schema()
        projects = persistence.list_projects()
    except Exception as exc:
        st.error(f"Could not connect to project database: {exc}")
        return

    st.info(
        "Database save stores planning-state JSON and project metadata. "
        "Upload the same RVTools workbook before loading a saved project so "
        "VM decisions and wave rows can be matched back to the current data."
    )
    with st.expander("Save current planning state to database"):
        save_name = st.text_input(
            "Project name",
            value=project_name,
            key="db_project_save_name",
        )
        save_description = st.text_area(
            "Description",
            value="",
            key="db_project_save_description",
        )
        existing_options = _project_options(projects)
        save_mode = st.radio(
            "Save target",
            ["Create new project", "Update existing project"],
            horizontal=True,
            key="db_project_save_mode",
        )
        selected_save_project = None
        if save_mode == "Update existing project":
            if existing_options:
                selected_label = st.selectbox(
                    "Existing project",
                    list(existing_options),
                    key="db_project_save_existing",
                )
                selected_save_project = existing_options[selected_label]
            else:
                st.warning("No saved projects are available to update.")
        if st.button("Save Planning State To Database", width="stretch"):
            if not save_name.strip():
                st.warning("Enter a project name before saving.")
            elif save_mode == "Update existing project" and not selected_save_project:
                st.warning("Choose an existing project to update.")
            else:
                try:
                    project_id = _save_planning_state_to_database(
                        planning_state_json,
                        project_name,
                        target_region=target_region,
                        target_zone=target_zone,
                        save_name=save_name,
                        description=save_description,
                        project_id=(
                            selected_save_project
                            if save_mode == "Update existing project"
                            else None
                        ),
                    )
                    st.session_state["active_database_project_id"] = project_id
                    st.success("Planning state saved to the project database.")
                except Exception as exc:
                    st.error(f"Could not save project: {exc}")

    with st.expander("Load planning state from database"):
        if not projects:
            st.info("No saved projects are available yet.")
            return
        options = _project_options(projects)
        selected_label = st.selectbox(
            "Saved project",
            list(options),
            key="db_project_load_existing",
        )
        selected_project_id = options[selected_label]
        selected_project = next(
            project for project in projects
            if project["id"] == selected_project_id
        )
        st.caption(
            "Created "
            f"{selected_project.get('created_at')} | Updated "
            f"{selected_project.get('updated_at')}"
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Load Project Planning State", width="stretch"):
                try:
                    _load_database_project_state(selected_project_id)
                except Exception as exc:
                    st.error(f"Could not load project: {exc}")
        with c2:
            if st.button("Delete Saved Project", width="stretch"):
                try:
                    persistence.delete_project(selected_project_id)
                    st.success("Saved project deleted.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete project: {exc}")


def render_sidebar_save_progress(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
    project_name,
    target_region,
    target_zone,
):
    """Render persistent sidebar progress-save controls after workbook upload."""
    planning_state_json = build_current_planning_state_json(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        project_name,
        target_region,
        target_zone,
    )
    st.sidebar.markdown("---")
    with st.sidebar.expander("Save Progress", expanded=True):
        st.caption("Planning edits are not automatically saved.")
        st.download_button(
            label="Download Planning State",
            data=planning_state_json.encode("utf-8"),
            file_name=f"{project_name}-planning-state.json",
            mime="application/json",
            width="stretch",
            key="sidebar_planning_state_download",
            help=(
                "Universal fallback for saving progress. Upload the same "
                "RVTools workbook, then import this file to resume."
            ),
        )

        status, message = database_persistence_status()
        if status == "ready":
            st.success("Database save available.")
            save_name = st.text_input(
                "Database project name",
                value=project_name,
                key="sidebar_db_project_name",
            )
            if st.button("Save To Database", width="stretch"):
                try:
                    project_id = _save_planning_state_to_database(
                        planning_state_json,
                        project_name,
                        target_region,
                        target_zone,
                        save_name=save_name,
                        project_id=st.session_state.get(
                            "active_database_project_id"
                        ),
                    )
                    st.session_state["active_database_project_id"] = project_id
                    st.session_state["last_database_save_at"] = (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    st.success(
                        "Progress saved to database. Keep the source RVTools "
                        "workbook; restore after uploading the same workbook."
                    )
                except Exception as exc:
                    st.error(f"Could not save to database: {exc}")
                    st.warning(
                        "To avoid losing progress: download planning-state.json "
                        "now, keep the source RVTools workbook, restart the "
                        "database or Docker Compose stack, then upload the same "
                        "workbook and import planning-state.json."
                    )
            if st.session_state.get("last_database_save_at"):
                st.caption(
                    "Last database save: "
                    f"{st.session_state['last_database_save_at']}"
                )
        elif status == "not_configured":
            _render_database_save_unavailable(status, message)
        else:
            _render_database_save_unavailable(status, message)


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

    planning_state_json = build_current_planning_state_json(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        project_name,
        target_region,
        target_zone,
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
    render_database_project_controls(
        planning_state_json,
        project_name,
        target_region,
        target_zone,
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
