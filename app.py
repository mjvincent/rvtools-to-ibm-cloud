import pandas as pd
import streamlit as st

from rvtools_parser import parse_rvtools_workbook
from streamlit_app.export import render_export_tab
from streamlit_app.image_import import render_image_import_tab
from streamlit_app.network_storage import (
    render_network_planning,
    render_storage_planning,
)
from streamlit_app.overview_readiness import (
    render_estate_summary,
    render_overview_tab,
    render_readiness_legend,
    render_readiness_triage,
)
from streamlit_app.page_header import render_page_header
from streamlit_app.remediation import render_remediation_backlog_tab
from streamlit_app.settings import render_sidebar_settings
from streamlit_app.wave_planning import render_wave_planning_tab
from ui import (
    DECISION_COLUMNS,
    DISABLED_COLS,
    apply_preflight_quick_fixes,
    build_table_config,
    merge_decision_edits,
)


st.set_page_config(
    page_title="IBM Cloud Terraform Generator",
    layout="wide"
)

render_page_header()
settings, uploaded_file = render_sidebar_settings()
target_region = settings.target_region
utilization_threshold = settings.utilization_threshold
project_name = settings.project_name
target_zone = settings.target_zone
pricing_catalog = settings.pricing_catalog
pricing_metadata = settings.pricing_metadata
catalog_profiles = settings.catalog_profiles
storage_tier_rates = settings.storage_tier_rates
generate_security_groups = settings.generate_security_groups

if uploaded_file is not None:
    parsed = parse_rvtools_workbook(
        uploaded_file,
        target_region,
        utilization_threshold,
        generate_security_groups,
        catalog_profiles=catalog_profiles,
        storage_tier_rates=storage_tier_rates,
        pricing_metadata=pricing_metadata,
    )

    processed_vms = parsed.processed_vms
    unique_nets = parsed.unique_nets
    disk_details = parsed.disk_details
    nic_details = parsed.nic_details
    assessment_quality = parsed.assessment_quality

    df_f = pd.DataFrame([vm.to_record() for vm in processed_vms])
    df_table = df_f.drop(
        columns=[
            "Disk Details", "Partition Details", "Network Details",
            "Readiness Findings"
        ],
        errors="ignore"
    )
    table_config = build_table_config(unique_nets, catalog_profiles)

    render_estate_summary(df_f)

    overview, readiness, remediation_backlog, vm_review, wave_planning, image_import, networks, storage, export = st.tabs([
        "Overview", "Readiness", "Remediation Backlog", "VM Review", "Wave Planning", "Image Import Planning", "Networks", "Storage", "Export"
    ])

    edited_df = df_table.copy()

    with overview:
        render_overview_tab(df_f, assessment_quality)

    with readiness:
        render_readiness_legend()
        render_readiness_triage(df_f)

    with remediation_backlog:
        render_remediation_backlog_tab(processed_vms)

    with vm_review:
        st.subheader("VM Decisions")
        st.caption("This view keeps the active decisions in front. Raw generated fields remain available below for audit and troubleshooting.")
        decision_table = apply_preflight_quick_fixes(
            df_table,
            st.session_state.get("preflight_quick_fixes", {}),
        )
        decision_input_columns = ["VM Key"] + [
            column for column in DECISION_COLUMNS
            if column in decision_table.columns
        ]
        edited_decisions = st.data_editor(
            decision_table[decision_input_columns],
            column_config=table_config,
            column_order=[
                column for column in DECISION_COLUMNS
                if column in decision_table.columns
            ],
            disabled=[
                column for column in DISABLED_COLS
                if column in decision_input_columns
            ],
            hide_index=True,
            use_container_width=True,
            key="vm_decision_editor"
        )
        edited_df = merge_decision_edits(decision_table, edited_decisions)
        with st.expander("Advanced generated fields"):
            st.dataframe(edited_df, hide_index=True, use_container_width=True)

    with wave_planning:
        edited_df = render_wave_planning_tab(edited_df, table_config)

    with networks:
        render_network_planning(edited_df, unique_nets)

    with storage:
        render_storage_planning(edited_df, processed_vms)

    with image_import:
        render_image_import_tab(
            edited_df, processed_vms, disk_details, nic_details
        )

    with export:
        render_export_tab(
            edited_df,
            processed_vms,
            disk_details,
            nic_details,
            unique_nets,
            target_region,
            target_zone,
            generate_security_groups,
            project_name,
            pricing_metadata,
            assessment_quality,
            pricing_catalog,
            catalog_profiles,
        )
