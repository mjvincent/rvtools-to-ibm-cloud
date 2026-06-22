import csv
import io

import pandas as pd
import streamlit as st

from handoff.cutover_readiness import build_cutover_readiness_rows
from streamlit_app.final_vms import build_final_vms
from streamlit_app.image_import import build_image_import_rows
from streamlit_app.remediation import (
    TRACKER_KEY,
    build_remediation_backlog_items,
)
from streamlit_app.wave_planning import REQUIRED_WAVE_COLUMNS


RESOLVED_REMEDIATION_STATUSES = {"resolved", "closed", "complete", "completed"}
READINESS_COLUMNS = [
    "Image Readiness",
    "Migration Readiness",
    "Memory Readiness",
    "Network Readiness",
]
ACTION_PLAN_FIELDS = ["Action", "Count", "Impact", "Next Step"]
SAFE_DEFAULTS_BUTTON_LABEL = "Initialize Pending/Open Defaults"
SAFE_DEFAULTS_HELP = (
    "Sets blank image import statuses to Pending and creates Open "
    "remediation tracker rows for current readiness findings. It does not "
    "mark images Imported, exclude VMs, change profiles, change subnets, "
    "build Terraform, or migrate workloads."
)


def _active_df(df):
    if "Exclude?" not in df.columns:
        return df.copy()
    return df[df["Exclude?"] == False].copy()


def _blank(value):
    if value is None:
        return True
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def _source_image(row):
    return str(row.get("Original Specs") or row.get("VM Name") or "").strip()


def _readiness_blocker_count(active_df):
    blockers = set()
    for column in READINESS_COLUMNS:
        if column not in active_df.columns:
            continue
        matches = active_df[active_df[column].astype(str).str.lower() == "blocked"]
        for _, row in matches.iterrows():
            blockers.add(row.get("VM Key") or row.get("VM Name"))
    return len(blockers)


def _missing_wave_count(active_df):
    missing = 0
    for _, row in active_df.iterrows():
        if any(_blank(row.get(column)) for column in REQUIRED_WAVE_COLUMNS):
            missing += 1
    return missing


def _pending_image_count(edited_df, image_import_status):
    image_rows = build_image_import_rows(edited_df, image_import_status)
    if image_rows.empty:
        return 0
    pending = 0
    for _, row in image_rows.iterrows():
        status = str(row.get("Import Status") or "").strip()
        if status != "Imported":
            pending += 1
    return pending


def _open_remediation_count(backlog_rows):
    open_count = 0
    for row in backlog_rows:
        status = str(row.get("Status") or "Open").strip().lower()
        if status not in RESOLVED_REMEDIATION_STATUSES:
            open_count += 1
    return open_count


def _cutover_status_counts(cutover_rows):
    by_vm = {}
    for row in cutover_rows:
        vm_name = row.get("VM Name", "")
        by_vm.setdefault(vm_name, row.get("Cutover Status", "Review"))
    return {
        "ready": sum(1 for status in by_vm.values() if status == "Ready"),
        "review": sum(1 for status in by_vm.values() if status == "Review"),
        "blocked": sum(1 for status in by_vm.values() if status == "Blocked"),
    }


def hard_blocked_vm_names(edited_df):
    """Return active VMs with hard readiness blockers."""
    active = _active_df(edited_df)
    blocked = []
    for _, row in active.iterrows():
        statuses = [
            str(row.get(column) or "").strip().lower()
            for column in READINESS_COLUMNS
        ]
        if "blocked" in statuses:
            blocked.append(str(row.get("VM Name") or row.get("VM Key") or ""))
    return sorted(name for name in blocked if name)


def build_guided_checklist(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
    remediation_tracker=None,
    image_import_status=None,
):
    """Build first-run checklist rows from current migration planning state."""
    remediation_tracker = remediation_tracker or {}
    image_import_status = image_import_status or {}
    active = _active_df(edited_df)
    backlog_rows = build_remediation_backlog_items(
        processed_vms,
        remediation_tracker,
    )
    final_vms = build_final_vms(edited_df, processed_vms, disk_details, nic_details)
    cutover_rows = build_cutover_readiness_rows(
        final_vms,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    cutover_counts = _cutover_status_counts(cutover_rows)

    readiness_blockers = _readiness_blocker_count(active)
    open_remediation = _open_remediation_count(backlog_rows)
    missing_wave = _missing_wave_count(active)
    pending_images = _pending_image_count(edited_df, image_import_status)

    return [
        {
            "Step": "Review readiness blockers",
            "Status": "Done" if readiness_blockers == 0 else "Needs attention",
            "Count": readiness_blockers,
            "Next Action": "Open Readiness or Remediation Backlog.",
        },
        {
            "Step": "Track remediation work",
            "Status": "Done" if open_remediation == 0 else "Needs attention",
            "Count": open_remediation,
            "Next Action": "Assign owners, statuses, and due dates.",
        },
        {
            "Step": "Complete wave planning",
            "Status": "Done" if missing_wave == 0 else "Needs attention",
            "Count": missing_wave,
            "Next Action": "Fill Wave, Cutover Group, Owner, and Application.",
        },
        {
            "Step": "Update image import status",
            "Status": "Done" if pending_images == 0 else "Needs attention",
            "Count": pending_images,
            "Next Action": "Set each image group to Imported when ready.",
        },
        {
            "Step": "Review Migration Ops",
            "Status": (
                "Done"
                if cutover_counts["blocked"] == 0 and cutover_counts["review"] == 0
                else "Needs attention"
            ),
            "Count": cutover_counts["blocked"] + cutover_counts["review"],
            "Next Action": "Review cutover blockers by wave and group.",
        },
        {
            "Step": "Build Terraform bundle",
            "Status": (
                "Ready"
                if len(active) and readiness_blockers == 0
                else "Needs attention"
            ),
            "Count": len(active),
            "Next Action": "Use Export after preflight blockers are resolved.",
        },
    ]


def build_migration_action_plan(
    edited_df,
    processed_vms,
    remediation_tracker=None,
    image_import_status=None,
):
    """Build high-level assistive migration planning recommendations."""
    remediation_tracker = remediation_tracker or {}
    image_import_status = image_import_status or {}
    active = _active_df(edited_df)
    backlog_rows = build_remediation_backlog_items(
        processed_vms,
        remediation_tracker,
    )
    image_rows = build_image_import_rows(edited_df, image_import_status)
    missing_image_statuses = [
        row
        for row in image_rows.to_dict("records")
        if _blank(row.get("Import Status"))
    ]
    missing_wave = _missing_wave_count(active)
    hard_blocked = hard_blocked_vm_names(edited_df)
    missing_tracker_rows = [
        row for row in backlog_rows
        if row.get("blocker_id") not in remediation_tracker
    ]

    return [
        {
            "Action": "Initialize image import tracking",
            "Count": len(missing_image_statuses),
            "Impact": "Sets blank image import statuses to Pending.",
            "Next Step": "Review Image Import Planning and update statuses as imports complete.",
        },
        {
            "Action": "Create remediation tracker entries",
            "Count": len(missing_tracker_rows),
            "Impact": "Adds Open remediation rows for current readiness findings.",
            "Next Step": "Assign owners, due dates, and notes in Remediation Backlog.",
        },
        {
            "Action": "Complete missing wave planning fields",
            "Count": missing_wave,
            "Impact": "No automatic changes; fields require migration-team intent.",
            "Next Step": "Use Wave Planning to assign wave, cutover group, owner, and application.",
        },
        {
            "Action": "Review hard-blocked VMs for exclusion",
            "Count": len(hard_blocked),
            "Impact": "Optional separate action can queue Exclude? for hard-blocked VMs.",
            "Next Step": "Correct source data where possible; exclude only VMs not ready for this package.",
        },
    ]


def apply_safe_migration_defaults(
    edited_df,
    processed_vms,
    remediation_tracker=None,
    image_import_status=None,
):
    """Apply conservative planning defaults without changing scope or mappings."""
    remediation_tracker = dict(remediation_tracker or {})
    image_import_status = dict(image_import_status or {})
    applied = {
        "image_import_pending": 0,
        "remediation_entries": 0,
    }

    image_rows = build_image_import_rows(edited_df, image_import_status)
    for row in image_rows.to_dict("records"):
        source = row.get("Source Image")
        if not source:
            continue
        current = dict(image_import_status.get(source, {}))
        if _blank(current.get("import_status")):
            current["import_status"] = "Pending"
            image_import_status[source] = current
            applied["image_import_pending"] += 1

    for row in build_remediation_backlog_items(processed_vms, remediation_tracker):
        blocker_id = row.get("blocker_id")
        if not blocker_id or blocker_id in remediation_tracker:
            continue
        remediation_tracker[blocker_id] = {
            "status": "Open",
            "due_date": "",
            "notes": "",
            "owner": row.get("Owner", ""),
            "vm_key": row.get("VM Key", ""),
            "blocker_type": row.get("Blocker Type", ""),
            "blocker_description": row.get("Blocker Description", ""),
        }
        applied["remediation_entries"] += 1

    return remediation_tracker, image_import_status, applied


def queue_exclusions_for_hard_blockers(edited_df, existing_fixes=None):
    """Queue VM Review exclusions for active VMs with hard readiness blockers."""
    fixes = dict(existing_fixes or {})
    for vm_name in hard_blocked_vm_names(edited_df):
        vm_fixes = dict(fixes.get(vm_name, {}))
        vm_fixes["Exclude?"] = True
        fixes[vm_name] = vm_fixes
    return fixes


def action_plan_csv(action_rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ACTION_PLAN_FIELDS)
    writer.writeheader()
    for row in action_rows:
        writer.writerow(row)
    return output.getvalue()


def has_session_planning_state(
    edited_df,
    remediation_tracker=None,
    image_import_status=None,
):
    """Return True when the current session has planning data worth saving."""
    remediation_tracker = remediation_tracker or {}
    image_import_status = image_import_status or {}
    if remediation_tracker or image_import_status:
        return True
    active = _active_df(edited_df)
    if "Exclude?" in edited_df.columns and bool(edited_df["Exclude?"].any()):
        return True
    for _, row in active.iterrows():
        for column in REQUIRED_WAVE_COLUMNS:
            if not _blank(row.get(column)):
                return True
    return False


def render_guided_migration_assistant(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
):
    """Render a guided first-run checklist and assistive planning controls."""
    st.subheader("Guided Migration Assistant")
    st.caption(
        "Use this checklist to move from upload review to a migration-ready handoff."
    )
    st.info(
        "After applying safe defaults or making planning edits, use Export > "
        "Planning State to download a reloadable planning session before "
        "closing the app."
    )

    remediation_tracker = st.session_state.get(TRACKER_KEY, {})
    image_import_status = st.session_state.get("image_import_status", {})
    if has_session_planning_state(
        edited_df,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    ):
        st.warning(
            "This session has planning data. Use Export > Planning Downloads "
            "to download planning-state.json before closing or refreshing."
        )
    checklist_rows = build_guided_checklist(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    st.dataframe(
        pd.DataFrame(checklist_rows),
        hide_index=True,
        width="stretch",
    )

    action_rows = build_migration_action_plan(
        edited_df,
        processed_vms,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )

    with st.expander("Assist Migration Planning"):
        st.dataframe(
            pd.DataFrame(action_rows),
            hide_index=True,
            width="stretch",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                SAFE_DEFAULTS_BUTTON_LABEL,
                help=SAFE_DEFAULTS_HELP,
                width="stretch",
            ):
                remediation, images, applied = apply_safe_migration_defaults(
                    edited_df,
                    processed_vms,
                    remediation_tracker=remediation_tracker,
                    image_import_status=image_import_status,
                )
                st.session_state[TRACKER_KEY] = remediation
                st.session_state["image_import_status"] = images
                st.success(
                    "Initialized "
                    f"{applied['image_import_pending']} image statuses and "
                    f"{applied['remediation_entries']} remediation rows."
                )
                st.rerun()
        with c2:
            st.download_button(
                label="Download Migration Action Plan",
                data=action_plan_csv(action_rows).encode("utf-8"),
                file_name="migration-action-plan.csv",
                mime="text/csv",
                width="stretch",
                key="migration_action_plan_download",
            )

        hard_blocked = hard_blocked_vm_names(edited_df)
        if hard_blocked:
            st.warning(
                f"{len(hard_blocked)} active VMs have hard readiness blockers. "
                "Exclusion is optional and should be used only when those VMs "
                "are not part of the current package."
            )
            if st.button(
                "Queue Exclusions for Hard-Blocked VMs",
                width="stretch",
            ):
                st.session_state["preflight_quick_fixes"] = (
                    queue_exclusions_for_hard_blockers(
                        edited_df,
                        st.session_state.get("preflight_quick_fixes", {}),
                    )
                )
                st.success(
                    "Queued exclusions in VM Review. Revisit VM Review and "
                    "Export preflight before building."
                )
                st.rerun()
