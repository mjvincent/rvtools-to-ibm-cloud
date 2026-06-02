import pandas as pd
import streamlit as st

from handoff import image_import_export
from preflight import (
    has_blockers,
    run_package_preflight,
)
from rvtools_parser import normalize_network_name, parse_rvtools_workbook
from streamlit_app.final_vms import build_final_vms
from streamlit_app.image_import import (
    build_image_import_rows,
    persist_image_import_edits,
)
from streamlit_app.package_builder import build_terraform_bundle
from streamlit_app.page_header import render_page_header
from streamlit_app.remediation import render_remediation_backlog_tab
from streamlit_app.settings import render_sidebar_settings
from ui import (
    DECISION_COLUMNS,
    DISABLED_COLS,
    apply_preflight_quick_fixes,
    build_table_config,
    merge_decision_edits,
    render_assessment_quality,
    render_estate_summary,
    render_network_planning,
    render_preflight_guidance,
    render_readiness_legend,
    render_readiness_triage,
    render_storage_planning,
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
        st.subheader("Estate Health")
        active_df = df_f[~df_f['Exclude?']]
        c1, c2, c3 = st.columns(3)
        c1.metric("Image Blocked", len(active_df[active_df["Image Readiness"] == "Blocked"]))
        c2.metric("Migration Blocked", len(active_df[active_df["Migration Readiness"] == "Blocked"]))
        c3.metric("Memory Blocked", len(active_df[active_df["Memory Readiness"] == "Blocked"]))
        st.subheader("Recommended Next Actions")
        st.write("1. Resolve Blocked readiness items before migration execution.")
        st.write("2. Validate Review items with workload owners and VMware administrators.")
        st.write("3. Confirm profile, storage tier, network, subnet, and security group overrides in VM Review.")
        st.write("4. Confirm Terraform deployment settings in Export and build the package.")
        render_assessment_quality(assessment_quality)

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
        st.subheader("Wave Planning")
        st.caption("Bulk assign waves, cutover groups, owners, and applications to active VMs.")

        # Prepare active VMs table
        active_df = edited_df[~edited_df['Exclude?']].copy()
        # Ensure wave planning columns exist
        for col in ["Wave", "Cutover Group", "Owner", "Application", "Priority", "Dependency Group"]:
            if col not in active_df.columns:
                active_df[col] = "" if col != "Priority" else "Medium"

        # Selection controls
        st.write("### Select VMs to assign")
        vm_options = active_df["VM Key"].tolist()
        selected = st.multiselect(
            "Select VMs (by VM Key)", vm_options,
            default=st.session_state.get("wave_selected_vms", [])
        )
        st.session_state["wave_selected_vms"] = selected

        c1, c2, c3 = st.columns([2, 2, 6])
        with c1:
            assign_wave_value = st.text_input("Quick Wave Value", "")
            if st.button("Assign All to Wave", use_container_width=True):
                if assign_wave_value:
                    edited_df.loc[~edited_df['Exclude?'], 'Wave'] = assign_wave_value
                    st.success(f"Assigned wave '{assign_wave_value}' to all active VMs")
                else:
                    st.warning("Enter a Wave value to assign to all active VMs.")
        with c2:
            if st.button("Assign Wave", use_container_width=True):
                st.session_state["show_assign_wave_form"] = True
        with c3:
            st.write("")

        # Bulk assign form
        if st.session_state.get("show_assign_wave_form"):
            with st.form("assign_wave_form"):
                st.write("Assign fields to selected VMs")
                f_wave = st.text_input("Wave")
                f_cut = st.text_input("Cutover Group")
                f_owner = st.text_input("Owner")
                f_app = st.text_input("Application")
                submitted = st.form_submit_button("Apply to Selected VMs")
                if submitted:
                    if not selected:
                        st.warning("No VMs selected for assignment.")
                    else:
                        for vmk in selected:
                            mask = edited_df['VM Key'] == vmk
                            if f_wave:
                                edited_df.loc[mask, 'Wave'] = f_wave
                            if f_cut:
                                edited_df.loc[mask, 'Cutover Group'] = f_cut
                            if f_owner:
                                edited_df.loc[mask, 'Owner'] = f_owner
                            if f_app:
                                edited_df.loc[mask, 'Application'] = f_app
                        st.success(f"Assigned fields to {len(selected)} VMs")
                        st.session_state["show_assign_wave_form"] = False

        # Configure columns for data editor using existing table_config where possible
        wave_table_cfg = dict(table_config)
        wave_table_cfg.update({
            "VM Key": st.column_config.TextColumn("VM Key", disabled=True),
            "VM Name": st.column_config.TextColumn("VM Name", disabled=True),
            "Wave": st.column_config.TextColumn("Wave"),
            "Cutover Group": st.column_config.TextColumn("Cutover Group"),
            "Owner": st.column_config.TextColumn("Owner"),
            "Application": st.column_config.TextColumn("Application"),
            "Priority": st.column_config.SelectboxColumn("Priority", options=["", "High", "Medium", "Low"]),
            "Dependency Group": st.column_config.TextColumn("Dependency Group"),
        })

        # Display editable grid
        display_cols = [
            "VM Key", "VM Name", "Wave", "Cutover Group", "Owner",
            "Application", "Priority", "Dependency Group"
        ]
        wave_editor = st.data_editor(
            active_df[display_cols],
            column_config=wave_table_cfg,
            hide_index=True,
            use_container_width=True,
            key="wave_planning_editor"
        )

        # Persist edits back to edited_df by VM Key
        if isinstance(wave_editor, pd.DataFrame):
            for row in wave_editor.to_dict('records'):
                vmk = row.get('VM Key')
                mask = edited_df['VM Key'] == vmk
                for col in ["Wave", "Cutover Group", "Owner", "Application", "Priority", "Dependency Group"]:
                    if col in row:
                        edited_df.loc[mask, col] = row.get(col)

        # Conflict detection
        st.write("### Conflict Detection")
        # Application vs Cutover Group
        app_conflicts = []
        apps = active_df.groupby('Application') if 'Application' in active_df.columns else []
        for app, group in apps:
            vals = set(group['Cutover Group'].dropna().astype(str).unique())
            vals = {v for v in vals if v}
            if len(vals) > 1:
                app_conflicts.append((app, vals))
        if app_conflicts:
            for app, vals in app_conflicts:
                st.warning(f"Application '{app}' has multiple Cutover Groups: {', '.join(vals)}")

        # Dependency Group vs Wave
        dep_conflicts = []
        deps = active_df.groupby('Dependency Group') if 'Dependency Group' in active_df.columns else []
        for dep, group in deps:
            vals = set(group['Wave'].dropna().astype(str).unique())
            vals = {v for v in vals if v}
            if len(vals) > 1:
                dep_conflicts.append((dep, vals))
        if dep_conflicts:
            for dep, vals in dep_conflicts:
                st.warning(f"Dependency Group '{dep}' spans multiple Waves: {', '.join(vals)}")

        # Completion status
        total = len(active_df)
        if total:
            required = ["Wave", "Cutover Group", "Owner", "Application"]
            complete = 0
            for _, r in edited_df[~edited_df['Exclude?']].iterrows():
                if all(r.get(c) not in (None, "") for c in required):
                    complete += 1
            if complete == total:
                st.success(f"Complete: {complete}/{total} VMs")
            else:
                st.info(f"Incomplete: {complete}/{total} VMs")

        # Expose advanced fields for audit
        with st.expander("Advanced wave planning data"):
            st.dataframe(edited_df[["VM Key", "VM Name", "Wave", "Cutover Group", "Owner", "Application", "Priority", "Dependency Group"]], hide_index=True, use_container_width=True)

    with networks:
        render_network_planning(edited_df, unique_nets)

    with storage:
        render_storage_planning(edited_df, processed_vms)

    with image_import:
        st.subheader("Image Import Planning")
        st.caption("Group active VMs by inferred source image and track import status.")

        # Initialize image import status storage
        if "image_import_status" not in st.session_state:
            st.session_state["image_import_status"] = {}

        df_images = build_image_import_rows(
            edited_df,
            st.session_state["image_import_status"],
        )

        if df_images.empty:
            st.info("No active VMs to plan image imports for.")
        else:
            col_cfg = {
                "Source Image": st.column_config.TextColumn("Source Image", disabled=True),
                "Count of VMs": st.column_config.NumberColumn("Count of VMs", disabled=True),
                "Owners": st.column_config.TextColumn("Owners", disabled=True),
                "Target Catalog ID": st.column_config.TextColumn("Target Catalog ID"),
                "Import Status": st.column_config.SelectboxColumn(
                    "Import Status",
                    options=["", "Pending", "Scheduled", "Imported", "Failed", "Review"],
                ),
                "Estimated Import Time": st.column_config.TextColumn("Estimated Import Time"),
                "Notes": st.column_config.TextColumn("Notes"),
            }

            edited_images = st.data_editor(
                df_images,
                column_config=col_cfg,
                hide_index=True,
                use_container_width=True,
                key="image_import_editor",
            )

            st.session_state["image_import_status"] = (
                persist_image_import_edits(
                    edited_images,
                    st.session_state["image_import_status"],
                )
            )

            st.write("---")
            st.subheader("Bulk Actions")
            image_options = df_images["Source Image"].tolist()
            selected_images = st.multiselect(
                "Select images to update",
                image_options,
                default=st.session_state.get("image_import_selected", []),
                key="image_import_multiselect",
            )
            st.session_state["image_import_selected"] = selected_images

            c1, c2 = st.columns([2, 6])
            with c1:
                bulk_status = st.selectbox(
                    "Set Import Status",
                    ["", "Pending", "Scheduled", "Imported", "Failed", "Review"],
                    key="bulk_image_status",
                )
                if st.button("Apply Status to Selected", use_container_width=True):
                    if not selected_images:
                        st.warning("No images selected.")
                    else:
                        for src in selected_images:
                            cur = st.session_state["image_import_status"].get(src, {})
                            cur["import_status"] = bulk_status
                            st.session_state["image_import_status"][src] = cur
                        st.success(f"Updated import status for {len(selected_images)} images.")

            with c2:
                if st.button("Generate Image Import Export", use_container_width=True):
                    csv_text = image_import_export(
                        build_final_vms(
                            edited_df, processed_vms, disk_details, nic_details
                        ),
                        st.session_state.get("image_import_status"),
                    )
                    st.session_state["last_image_import_csv"] = csv_text

                if st.session_state.get("last_image_import_csv"):
                    st.download_button(
                        label="Download Image Import CSV",
                        data=st.session_state.get("last_image_import_csv").encode("utf-8"),
                        file_name="image-import-plan.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="image_import_export_download",
                    )

    with export:
        st.subheader("Terraform Package")
        col1, col2 = st.columns(2)
        with col1:
            vpc_name = st.text_input("VPC Name", "migration-vpc")
            address_prefix_strategy = st.selectbox(
                "Address Prefix Strategy",
                ["manual", "auto"],
                index=0
            )
            deployment_target = st.selectbox(
                "Deployment Target",
                ["Plain CLI", "IBM Schematics"],
                index=0
            )
            ssh_source_cidr = st.text_input(
                "SSH Source CIDR",
                "",
                help=(
                    "Optional management CIDR for inbound SSH rules. "
                    "Leave blank to omit SSH access from generated security groups."
                ),
            )
        with col2:
            st.markdown("**Custom CIDRs per Subnet**")
            custom_cidrs = {}
            for idx, net in enumerate(unique_nets):
                net_name = net.get('name', 'unknown-net')
                default_cidr = net.get('cidr', '10.0.0.0/24')
                sanitized_name = normalize_network_name(net_name)
                net_key = f"{sanitized_name}_{idx}"
                net['cidr_key'] = net_key
                custom_cidrs[net_key] = st.text_input(
                    f"{net_name} CIDR",
                    default_cidr,
                    key=f"cidr_{net_key}"
                )

        in_scope = len(edited_df[~edited_df['Exclude?']])
        blockers = sum(
            len(edited_df[(~edited_df['Exclude?']) & (edited_df[column] == "Blocked")])
            for column in [
                "Image Readiness", "Migration Readiness", "Memory Readiness"
            ]
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("VMs In Package", in_scope)
        c2.metric("Blocker Signals", blockers)
        c3.metric("Networks", len(unique_nets))

        st.download_button(
            label="Download Business Case (CSV)",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name=f"{project_name}_proposal.csv",
            mime="text/csv",
            use_container_width=True
        )

        preview_vms = build_final_vms(
            edited_df, processed_vms, disk_details, nic_details
        )
        preview_findings = run_package_preflight(
            preview_vms,
            unique_nets,
            target_region,
            custom_cidrs=custom_cidrs,
            enable_security_groups=generate_security_groups,
            catalog_profiles=catalog_profiles,
            ssh_source_cidr=ssh_source_cidr,
        )
        render_preflight_guidance(preview_findings, edited_df)
        if st.button("Re-run package preflight", use_container_width=True):
            st.session_state["preflight_needs_rerun"] = False
            st.rerun()

        if st.button("Build Terraform Project", use_container_width=True):
            with st.status("Packaging Project...") as status:
                try:
                    final_vms = build_final_vms(
                        edited_df, processed_vms, disk_details, nic_details
                    )

                    preflight_findings = run_package_preflight(
                        final_vms,
                        unique_nets,
                        target_region,
                        custom_cidrs=custom_cidrs,
                        enable_security_groups=generate_security_groups,
                        catalog_profiles=catalog_profiles,
                        ssh_source_cidr=ssh_source_cidr,
                    )
                    if preflight_findings:
                        render_preflight_guidance(preflight_findings, edited_df)
                    if has_blockers(preflight_findings):
                        status.update(
                            label="Preflight blocked package build",
                            state="error",
                        )
                        st.session_state['build_done'] = False
                        st.error(
                            "Resolve package preflight blockers or exclude the "
                            "affected VMs before building the Terraform bundle."
                        )
                        st.stop()

                    st.session_state['zip_data'] = build_terraform_bundle(
                        final_vms,
                        unique_nets,
                        target_region,
                        target_zone,
                        generate_security_groups,
                        vpc_name,
                        custom_cidrs,
                        address_prefix_strategy,
                        deployment_target,
                        project_name,
                        ssh_source_cidr,
                        pricing_metadata,
                        assessment_quality,
                        pricing_catalog,
                        preflight_findings,
                        st.session_state.get("remediation_tracker", {}),
                        st.session_state.get("image_import_status", {}),
                    )
                    st.session_state['build_done'] = True
                    status.update(label="Complete!", state="complete")
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.get('build_done'):
            st.write("---")
            st.write("### Project Ready")
            st.download_button(
                label="Download Terraform Bundle",
                data=st.session_state['zip_data'],
                file_name=f"{project_name}.zip",
                mime="application/zip",
                use_container_width=True
            )
