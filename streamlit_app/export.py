import streamlit as st

from preflight import has_blockers, run_package_preflight
from rvtools_parser import normalize_network_name
from streamlit_app.final_vms import build_final_vms
from streamlit_app.package_builder import build_terraform_bundle
from streamlit_app.planning_state import render_planning_state_controls
from ui import render_preflight_guidance


READINESS_BLOCKER_COLUMNS = [
    "Image Readiness",
    "Migration Readiness",
    "Memory Readiness",
]


def calculate_package_summary(edited_df, unique_nets):
    """Return package summary metrics for the Export tab."""
    in_scope = len(edited_df[~edited_df["Exclude?"]])
    blockers = sum(
        len(
            edited_df[
                (~edited_df["Exclude?"])
                & (edited_df[column] == "Blocked")
            ]
        )
        for column in READINESS_BLOCKER_COLUMNS
    )
    return in_scope, blockers, len(unique_nets)


def render_package_settings():
    """Render package-level Terraform settings."""
    st.markdown("### Package Settings")
    col1, col2 = st.columns(2)
    with col1:
        vpc_name = st.text_input("VPC Name", "migration-vpc")
        address_prefix_strategy = st.selectbox(
            "Address Prefix Strategy",
            ["manual", "auto"],
            index=0,
        )
    with col2:
        deployment_target = st.selectbox(
            "Deployment Target",
            ["Plain CLI", "IBM Schematics"],
            index=0,
        )
        ssh_source_cidr = st.text_input(
            "SSH Source CIDR",
            "",
            help=(
                "Optional management CIDR for inbound SSH rules. "
                "Leave blank to omit SSH access from generated security groups."
            ),
        )
    return (
        vpc_name,
        address_prefix_strategy,
        deployment_target,
        ssh_source_cidr,
    )


def render_subnet_cidr_inputs(unique_nets):
    """Render custom CIDR inputs for discovered networks."""
    st.markdown("### Subnet CIDRs")
    custom_cidrs = {}
    for idx, net in enumerate(unique_nets):
        net_name = net.get("name", "unknown-net")
        default_cidr = net.get("cidr", "10.0.0.0/24")
        sanitized_name = normalize_network_name(net_name)
        net_key = f"{sanitized_name}_{idx}"
        net["cidr_key"] = net_key
        custom_cidrs[net_key] = st.text_input(
            f"{net_name} CIDR",
            default_cidr,
            key=f"cidr_{net_key}",
        )
    return custom_cidrs


def render_package_summary(edited_df, unique_nets):
    """Render package summary metrics."""
    st.markdown("### Package Summary")
    in_scope, blockers, network_count = calculate_package_summary(
        edited_df, unique_nets
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("VMs In Package", in_scope)
    c2.metric("Blocker Signals", blockers)
    c3.metric("Networks", network_count)


def render_planning_downloads(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
    project_name,
    target_region,
    target_zone,
):
    """Render business case and planning-state download controls."""
    st.markdown("### Planning Downloads")
    st.info(
        "Downloaded CSV, planning-state, and Terraform package files may "
        "contain sensitive infrastructure and migration planning data."
    )
    st.download_button(
        label="Download Business Case (CSV)",
        data=edited_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{project_name}_proposal.csv",
        mime="text/csv",
        use_container_width=True,
    )

    render_planning_state_controls(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        project_name,
        target_region,
        target_zone,
    )


def render_preflight_review(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
    unique_nets,
    target_region,
    custom_cidrs,
    generate_security_groups,
    catalog_profiles,
    ssh_source_cidr,
):
    """Render package preflight guidance and rerun control."""
    st.markdown("### Preflight Review")
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


def render_build_and_download(
    edited_df,
    processed_vms,
    disk_details,
    nic_details,
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
    catalog_profiles,
):
    """Render Terraform build and ZIP download controls."""
    st.markdown("### Build And Download")
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
                    st.session_state["build_done"] = False
                    st.error(
                        "Resolve package preflight blockers or exclude the "
                        "affected VMs before building the Terraform bundle."
                    )
                    st.stop()

                st.session_state["zip_data"] = build_terraform_bundle(
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
                st.session_state["build_done"] = True
                status.update(label="Complete!", state="complete")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.get("build_done"):
        st.write("---")
        st.write("### Project Ready")
        st.download_button(
            label="Download Terraform Bundle",
            data=st.session_state["zip_data"],
            file_name=f"{project_name}.zip",
            mime="application/zip",
            use_container_width=True,
        )


def render_export_tab(
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
):
    """Render Terraform package controls and download actions."""
    st.subheader("Terraform Package")
    (
        vpc_name,
        address_prefix_strategy,
        deployment_target,
        ssh_source_cidr,
    ) = render_package_settings()
    custom_cidrs = render_subnet_cidr_inputs(unique_nets)
    render_package_summary(edited_df, unique_nets)
    render_planning_downloads(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        project_name,
        target_region,
        target_zone,
    )
    render_preflight_review(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
        unique_nets,
        target_region,
        custom_cidrs=custom_cidrs,
        generate_security_groups=generate_security_groups,
        catalog_profiles=catalog_profiles,
        ssh_source_cidr=ssh_source_cidr,
    )
    render_build_and_download(
        edited_df,
        processed_vms,
        disk_details,
        nic_details,
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
        catalog_profiles,
    )
