import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError


TRACKER_KEY = "remediation_tracker"


def build_remediation_backlog_items(processed_vms, tracker):
    """Build editable remediation backlog rows from VM readiness findings."""
    backlog_items = []
    counter = 0
    for vm in processed_vms:
        findings = []
        findings.extend(getattr(vm, "readiness_findings", []) or [])
        findings.extend(getattr(vm, "network_readiness_findings", []) or [])
        findings.extend(
            getattr(vm, "migration", {}).findings
            if getattr(vm, "migration", None)
            else []
        )
        for finding in findings:
            blocker_id = f"{vm.vm_key}::{counter}"
            counter += 1
            desc = (
                finding.recommended_action
                or finding.evidence
                or finding.severity
                or ""
            )
            state_entry = tracker.get(blocker_id, {})
            backlog_items.append({
                "blocker_id": blocker_id,
                "VM Key": vm.vm_key,
                "VM Name": vm.vm_name,
                "Owner": vm.owner or "",
                "Blocker Type": finding.finding_type,
                "Blocker Description": desc,
                "Status": state_entry.get("status", "Open"),
                "Due Date": state_entry.get("due_date", ""),
                "Notes": state_entry.get("notes", ""),
            })
    return backlog_items


def persist_remediation_edits(edited_backlog, tracker):
    """Persist editable backlog fields into the session tracker mapping."""
    if not isinstance(edited_backlog, pd.DataFrame):
        return tracker

    updated = dict(tracker)
    for row in edited_backlog.to_dict("records"):
        blocker_id = row.get("blocker_id")
        if not blocker_id:
            continue
        updated[blocker_id] = {
            "status": row.get("Status", "Open"),
            "due_date": row.get("Due Date", ""),
            "notes": row.get("Notes", ""),
            "owner": row.get("Owner", ""),
        }
    return updated


def read_remediation_tracker_csv(uploaded_file):
    """Read a remediation tracker CSV into a dataframe."""
    try:
        return pd.read_csv(uploaded_file).fillna("")
    except (EmptyDataError, UnicodeDecodeError, ValueError):
        return pd.DataFrame()


def import_remediation_tracker(imported_df, current_backlog_rows, tracker):
    """Merge imported remediation CSV rows into tracker session state."""
    if not isinstance(imported_df, pd.DataFrame) or imported_df.empty:
        return tracker, {"applied": 0, "skipped": 0}

    backlog_lookup = {}
    for row in current_backlog_rows:
        key = (
            str(row.get("VM Key", "")),
            str(row.get("Blocker Type", "")),
            str(row.get("Blocker Description", "")),
        )
        backlog_lookup[key] = row.get("blocker_id")

    updated = dict(tracker)
    applied = 0
    skipped = 0
    for row in imported_df.to_dict("records"):
        blocker_id = row.get("blocker_id") or row.get("Blocker ID")
        if not blocker_id:
            key = (
                str(row.get("VM Key", "")),
                str(row.get("Blocker Type", "")),
                str(row.get("Blocker Description", "")),
            )
            blocker_id = backlog_lookup.get(key)
        if not blocker_id:
            skipped += 1
            continue

        updated[blocker_id] = {
            "status": row.get("Status", "Open") or "Open",
            "due_date": row.get("Due Date", ""),
            "notes": row.get("Notes", ""),
            "owner": row.get("Owner", ""),
        }
        applied += 1
    return updated, {"applied": applied, "skipped": skipped}


def render_remediation_backlog_tab(processed_vms):
    """Render the remediation backlog tab."""
    st.subheader("Remediation Backlog")
    st.caption("Track readiness blockers and remediation status.")

    st.info(
        "**Note:** Remediation tracker data is stored for this session only. "
        "To persist your tracking data across sessions, export the CSV below "
        "and re-import it by adding it back to the backlog."
    )

    if TRACKER_KEY not in st.session_state:
        st.session_state[TRACKER_KEY] = {}

    backlog_items = build_remediation_backlog_items(
        processed_vms,
        st.session_state[TRACKER_KEY],
    )
    if not backlog_items:
        st.info("No readiness blockers found.")
        return

    backlog_df = pd.DataFrame(backlog_items)

    with st.expander("Import saved remediation tracker"):
        uploaded_tracker = st.file_uploader(
            "Upload remediation backlog CSV",
            type=["csv"],
            key="remediation_tracker_import",
        )
        if st.button("Load Remediation CSV", use_container_width=True):
            if uploaded_tracker is None:
                st.warning("Choose a remediation CSV to load.")
            else:
                imported_df = read_remediation_tracker_csv(uploaded_tracker)
                st.session_state[TRACKER_KEY], result = (
                    import_remediation_tracker(
                        imported_df,
                        backlog_items,
                        st.session_state[TRACKER_KEY],
                    )
                )
                st.success(
                    "Loaded "
                    f"{result['applied']} remediation rows"
                    + (
                        f"; skipped {result['skipped']} unmatched rows."
                        if result["skipped"] else "."
                    )
                )
                backlog_items = build_remediation_backlog_items(
                    processed_vms,
                    st.session_state[TRACKER_KEY],
                )
                backlog_df = pd.DataFrame(backlog_items)

    col_cfg = {
        "blocker_id": st.column_config.TextColumn("ID", disabled=True),
        "VM Key": st.column_config.TextColumn("VM Key", disabled=True),
        "VM Name": st.column_config.TextColumn("VM Name", disabled=True),
        "Owner": st.column_config.TextColumn("Owner"),
        "Blocker Type": st.column_config.TextColumn(
            "Blocker Type", disabled=True
        ),
        "Blocker Description": st.column_config.TextColumn(
            "Blocker Description", disabled=True
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Open", "In Progress", "Resolved", "Deferred"],
        ),
        "Due Date": st.column_config.TextColumn("Due Date"),
        "Notes": st.column_config.TextColumn("Notes"),
    }

    edited_backlog = st.data_editor(
        backlog_df,
        column_config=col_cfg,
        hide_index=True,
        use_container_width=True,
        key="remediation_editor",
    )

    st.session_state[TRACKER_KEY] = persist_remediation_edits(
        edited_backlog,
        st.session_state[TRACKER_KEY],
    )

    st.write("---")
    st.subheader("Backlog Summary")
    df_for_summary = (
        edited_backlog
        if isinstance(edited_backlog, pd.DataFrame)
        else backlog_df
    )
    status_counts = (
        df_for_summary["Status"].value_counts().to_dict()
        if not df_for_summary.empty
        else {}
    )
    owner_counts = (
        df_for_summary["Owner"].fillna("").value_counts().to_dict()
        if not df_for_summary.empty
        else {}
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Open", int(status_counts.get("Open", 0)))
    c2.metric("In Progress", int(status_counts.get("In Progress", 0)))
    c3.metric("Resolved", int(status_counts.get("Resolved", 0)))

    st.write("### By Owner")
    if owner_counts:
        owner_df = pd.DataFrame([
            {"Owner": owner, "Count": count}
            for owner, count in owner_counts.items()
        ])
        st.dataframe(owner_df, use_container_width=True)
    else:
        st.write("No owners assigned yet.")

    try:
        due_parsed = pd.to_datetime(
            df_for_summary.get("Due Date", pd.Series([], dtype=object)),
            errors="coerce",
        )
        overdue = df_for_summary.loc[due_parsed < pd.Timestamp.now()]
        st.write(f"Overdue items: {len(overdue)}")
        if not overdue.empty:
            st.dataframe(
                overdue[[
                    "VM Key",
                    "VM Name",
                    "Owner",
                    "Blocker Type",
                    "Blocker Description",
                    "Status",
                    "Due Date",
                    "Notes",
                ]],
                use_container_width=True,
            )
    except Exception:
        pass

    csv_bytes = df_for_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export Remediation Backlog",
        data=csv_bytes,
        file_name="p4-remediation-backlog.csv",
        mime="text/csv",
        use_container_width=True,
        key="p4-tracker-export",
    )
