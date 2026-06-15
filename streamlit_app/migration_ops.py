import pandas as pd
import streamlit as st

from handoff.cutover_readiness import (
    build_cutover_readiness_rows,
    generate_cutover_readiness_csv,
    summarize_cutover_readiness,
)
from streamlit_app.final_vms import build_final_vms


def _summary_dataframe(rows, group_field):
    return pd.DataFrame(summarize_cutover_readiness(rows, group_field))


def render_migration_ops_tab(edited_df, processed_vms, disk_details, nic_details):
    """Render the Migration Ops cutover readiness dashboard."""
    st.subheader("Migration Ops")
    st.caption(
        "Track cutover readiness across waves, remediation, and image imports."
    )

    remediation_tracker = st.session_state.get("remediation_tracker", {})
    image_import_status = st.session_state.get("image_import_status", {})
    final_vms = build_final_vms(edited_df, processed_vms, disk_details, nic_details)
    rows = build_cutover_readiness_rows(
        final_vms,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )

    if not rows:
        st.info("No active VMs to assess for cutover readiness.")
        return

    detail_df = pd.DataFrame(rows)
    vm_status = detail_df.groupby("VM Name")["Cutover Status"].first()
    status_counts = vm_status.value_counts().to_dict()
    blockers = detail_df[detail_df["Blocker Category"] != "Ready"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ready", int(status_counts.get("Ready", 0)))
    c2.metric("Review", int(status_counts.get("Review", 0)))
    c3.metric("Blocked", int(status_counts.get("Blocked", 0)))
    c4.metric("Open Blockers", int(len(blockers)))

    st.write("### By Wave")
    wave_df = _summary_dataframe(rows, "Wave")
    if wave_df.empty:
        st.info("No wave planning data is available yet.")
    else:
        st.dataframe(wave_df, hide_index=True, width="stretch")

    st.write("### By Cutover Group")
    cutover_df = _summary_dataframe(rows, "Cutover Group")
    if cutover_df.empty:
        st.info("No cutover group data is available yet.")
    else:
        st.dataframe(cutover_df, hide_index=True, width="stretch")

    st.write("### Cutover Readiness Detail")
    st.dataframe(detail_df, hide_index=True, width="stretch")

    csv_text = generate_cutover_readiness_csv(
        final_vms,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    st.download_button(
        label="Download Cutover Readiness CSV",
        data=csv_text.encode("utf-8"),
        file_name="cutover-readiness.csv",
        mime="text/csv",
        width="stretch",
        key="cutover_readiness_export_download",
    )
