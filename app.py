import pandas as pd
import streamlit as st

from rvtools_parser import parse_rvtools_workbook
from streamlit_app.export import render_export_tab
from streamlit_app.guided_migration import render_guided_migration_assistant
from streamlit_app.image_import import render_image_import_tab
from streamlit_app.migration_ops import render_migration_ops_tab
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
from streamlit_app.planning_state import (
    apply_planning_state_to_dataframe,
    build_planning_state_restore_summary,
    render_sidebar_save_progress,
)
from streamlit_app.remediation import render_remediation_backlog_tab
from streamlit_app.settings import render_sidebar_settings
from streamlit_app.vm_review import render_vm_review_tab
from streamlit_app.wave_planning import render_wave_planning_tab
from ui import build_table_config


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

    (
        overview, readiness, remediation_backlog, vm_review, wave_planning,
        image_import, migration_ops, networks, storage, export,
    ) = st.tabs([
        "Overview", "Readiness", "Remediation Backlog", "VM Review",
        "Wave Planning", "Image Import Planning", "Migration Ops",
        "Networks", "Storage", "Export",
    ])

    edited_df = df_table.copy()

    if st.session_state.get("pending_planning_state"):
        pending_state = st.session_state["pending_planning_state"]
        edited_df, state_result = apply_planning_state_to_dataframe(
            edited_df,
            pending_state,
        )
        session_result = st.session_state.get(
            "planning_state_session_result",
            {},
        )
        st.session_state["planning_state_restore_summary"] = (
            build_planning_state_restore_summary(
                pending_state,
                state_result,
                session_result,
            )
        )
        st.session_state["planning_state_wave_result"] = state_result
        del st.session_state["pending_planning_state"]
        st.session_state.pop("planning_state_session_result", None)

    with overview:
        render_overview_tab(df_f, assessment_quality)
        st.write("---")
        render_guided_migration_assistant(
            edited_df,
            processed_vms,
            disk_details,
            nic_details,
        )

    with readiness:
        render_readiness_legend()
        render_readiness_triage(df_f)

    with remediation_backlog:
        render_remediation_backlog_tab(processed_vms)

    with vm_review:
        edited_df = render_vm_review_tab(edited_df, table_config)

    with wave_planning:
        if st.session_state.get("planning_state_import_message"):
            st.success(st.session_state.pop("planning_state_import_message"))
        if st.session_state.get("planning_state_wave_result"):
            result = st.session_state.pop("planning_state_wave_result")
            st.info(
                "Restored wave planning for "
                f"{result['applied']} VMs"
                + (
                    f"; skipped {result['skipped']} unmatched rows."
                    if result["skipped"] else "."
                )
            )
        edited_df = render_wave_planning_tab(edited_df, table_config)

    with networks:
        render_network_planning(edited_df, unique_nets)

    with storage:
        render_storage_planning(edited_df, processed_vms)

    with image_import:
        render_image_import_tab(
            edited_df, processed_vms, disk_details, nic_details
        )

    with migration_ops:
        render_migration_ops_tab(
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

    render_sidebar_save_progress(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        project_name,
        target_region,
        target_zone,
    )
