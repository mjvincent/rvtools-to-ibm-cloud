import pandas as pd
import streamlit as st

from preflight import has_blockers, run_package_preflight
from rvtools_parser import normalize_network_name
from streamlit_app.final_vms import build_final_vms
from streamlit_app.image_import import build_image_import_rows
from streamlit_app.package_builder import build_terraform_bundle
from streamlit_app.planning_state import render_planning_state_controls
from streamlit_app.wave_planning import REQUIRED_WAVE_COLUMNS
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
        vpc_name = st.text_input(
            "VPC Name",
            "migration-vpc",
            help="Name assigned to the generated IBM Cloud VPC resource.",
        )
        address_prefix_strategy = st.selectbox(
            "Address Prefix Strategy",
            ["manual", "auto"],
            index=0,
            help="Manual preserves planned CIDRs from the app; auto lets IBM Cloud allocate address prefixes.",
        )
    with col2:
        deployment_target = st.selectbox(
            "Deployment Target",
            ["Plain CLI", "IBM Schematics"],
            index=0,
            help="Plain CLI emits a local Terraform project. IBM Schematics adds handoff context for Schematics-based deployment.",
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
            help="Target subnet CIDR for this discovered source network. Adjust only after confirming the target VPC IP plan.",
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


def build_bundle_contents_preview_rows():
    """Return major Terraform ZIP contents and their intended reviewers."""
    return [
        {
            "File Or Folder": "README.md",
            "Purpose": "Terraform operator instructions and package checklist.",
            "Primary Owner": "Terraform operator",
        },
        {
            "File Or Folder": "Root Terraform files",
            "Purpose": "Provider, variables, outputs, and module wiring.",
            "Primary Owner": "Terraform operator",
        },
        {
            "File Or Folder": "modules/networking/",
            "Purpose": "Generated VPC, subnet, address prefix, and security group resources.",
            "Primary Owner": "Cloud network reviewer",
        },
        {
            "File Or Folder": "modules/storage/",
            "Purpose": "Generated block volume resources and attachment inputs.",
            "Primary Owner": "Storage reviewer",
        },
        {
            "File Or Folder": "modules/vsi/",
            "Purpose": "Generated VSI resources, NIC references, volumes, and image variables.",
            "Primary Owner": "Terraform operator",
        },
        {
            "File Or Folder": "vm-mapping.csv",
            "Purpose": "Source VM to target VSI planning map.",
            "Primary Owner": "Migration team",
        },
        {
            "File Or Folder": "nic-mapping.csv",
            "Purpose": "Per-NIC source-to-target network interface mapping.",
            "Primary Owner": "Network reviewer",
        },
        {
            "File Or Folder": "disk-mapping.csv",
            "Purpose": "Per-disk boot/data volume mapping and storage tier review.",
            "Primary Owner": "Storage reviewer",
        },
        {
            "File Or Folder": "readiness-findings.csv",
            "Purpose": "Migration readiness findings and remediation actions.",
            "Primary Owner": "Migration team",
        },
        {
            "File Or Folder": "preflight-report.csv/json",
            "Purpose": "Package blockers, warnings, fix categories, and evidence.",
            "Primary Owner": "Migration lead",
        },
        {
            "File Or Folder": "pricing-diagnostics.csv/json",
            "Purpose": "Pricing source, confidence, fallback, and catalog diagnostics.",
            "Primary Owner": "Solution architect",
        },
        {
            "File Or Folder": "cutover-readiness.csv",
            "Purpose": "Cutover readiness by VM, wave, group, owner, and blocker.",
            "Primary Owner": "Migration lead",
        },
        {
            "File Or Folder": "planning-state.json",
            "Purpose": "Reloadable app planning state for later sessions.",
            "Primary Owner": "Planning owner",
        },
        {
            "File Or Folder": "image-import-variables.tfvars.example",
            "Purpose": "Template for custom image IDs after image import.",
            "Primary Owner": "Image import owner",
        },
        {
            "File Or Folder": "migration-manifest.json",
            "Purpose": "Structured handoff manifest for tools and audit review.",
            "Primary Owner": "Migration team",
        },
        {
            "File Or Folder": "migration-runbook.md",
            "Purpose": "Operational runbook for handoff review and migration execution.",
            "Primary Owner": "Migration team",
        },
    ]


def render_bundle_contents_preview():
    """Render a read-only preview of major Terraform ZIP contents."""
    st.markdown("### Bundle Contents Preview")
    st.caption(
        "This preview explains major files before build. It does not inspect "
        "or change the generated ZIP."
    )
    st.dataframe(
        build_bundle_contents_preview_rows(),
        hide_index=True,
        width="stretch",
    )


def _is_blank(value):
    return value is None or pd.isna(value) or str(value).strip() == ""


def build_export_readiness_checklist(
    edited_df,
    image_import_status=None,
    remediation_tracker=None,
    preflight_findings=None,
):
    """Return non-blocking readiness checklist rows for Export users."""
    image_import_status = image_import_status or {}
    remediation_tracker = remediation_tracker or {}
    preflight_findings = preflight_findings or []
    active_df = edited_df[~edited_df["Exclude?"]].copy()

    blocker_count = 0
    for column in READINESS_BLOCKER_COLUMNS:
        if column in active_df.columns:
            blocker_count += len(active_df[active_df[column] == "Blocked"])

    missing_wave_rows = 0
    for _, row in active_df.iterrows():
        if any(_is_blank(row.get(column)) for column in REQUIRED_WAVE_COLUMNS):
            missing_wave_rows += 1

    image_rows = build_image_import_rows(edited_df, image_import_status)
    pending_images = 0
    if not image_rows.empty:
        pending_images = len(
            image_rows[
                image_rows["Import Status"].fillna("").astype(str) != "Imported"
            ]
        )

    preflight_blockers = sum(
        1 for finding in preflight_findings
        if getattr(finding, "severity", "") == "blocker"
    )
    preflight_warnings = sum(
        1 for finding in preflight_findings
        if getattr(finding, "severity", "") == "warning"
    )

    return [
        {
            "Area": "Readiness blockers",
            "Status": "Blocked" if blocker_count else "Ready",
            "Signal": f"{blocker_count} blocker signal(s)",
            "Recommended Next Action": (
                "Resolve readiness blockers or exclude affected VMs."
                if blocker_count else
                "Continue to preflight and package review."
            ),
        },
        {
            "Area": "Wave planning",
            "Status": "Review" if missing_wave_rows else "Ready",
            "Signal": f"{missing_wave_rows} active VM(s) missing required wave fields",
            "Recommended Next Action": (
                "Complete Wave, Cutover Group, Owner, and Application."
                if missing_wave_rows else
                "Review Migration Ops by wave and cutover group."
            ),
        },
        {
            "Area": "Image import status",
            "Status": "Review" if pending_images else "Ready",
            "Signal": f"{pending_images} image group(s) not marked Imported",
            "Recommended Next Action": (
                "Update Image Import Planning as imports complete."
                if pending_images else
                "Confirm image IDs before Terraform plan/apply."
            ),
        },
        {
            "Area": "Planning state",
            "Status": "Review" if len(active_df) else "Ready",
            "Signal": (
                f"{len(active_df)} active VM(s), "
                f"{len(remediation_tracker)} remediation item(s)"
            ),
            "Recommended Next Action": (
                "Download planning-state.json before closing or handing off work."
                if len(active_df) else
                "Include at least one VM before saving package planning state."
            ),
        },
        {
            "Area": "Package preflight",
            "Status": (
                "Blocked" if preflight_blockers
                else "Review" if preflight_warnings
                else "Ready"
            ),
            "Signal": (
                f"{preflight_blockers} blocker(s), "
                f"{preflight_warnings} warning(s)"
            ),
            "Recommended Next Action": (
                "Resolve preflight blockers before building."
                if preflight_blockers else
                "Review warnings; they will be included in the package report."
                if preflight_warnings else
                "Build when package settings and planning are reviewed."
            ),
        },
    ]


def summarize_export_readiness_statuses(rows):
    """Count checklist rows by display status."""
    summary = {"Ready": 0, "Review": 0, "Blocked": 0}
    for row in rows or []:
        status = row.get("Status", "Review")
        summary[status] = summary.get(status, 0) + 1
    return summary


def render_build_readiness_checklist(
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
    """Render a non-blocking checklist before package build."""
    st.markdown("### Build Readiness Checklist")
    preview_vms = build_final_vms(
        edited_df, processed_vms, disk_details, nic_details
    )
    preflight_findings = run_package_preflight(
        preview_vms,
        unique_nets,
        target_region,
        custom_cidrs=custom_cidrs,
        enable_security_groups=generate_security_groups,
        catalog_profiles=catalog_profiles,
        ssh_source_cidr=ssh_source_cidr,
    )
    st.caption(
        "This checklist is informational. Package preflight remains the build gate."
    )
    checklist_rows = build_export_readiness_checklist(
        edited_df,
        image_import_status=st.session_state.get("image_import_status", {}),
        remediation_tracker=st.session_state.get("remediation_tracker", {}),
        preflight_findings=preflight_findings,
    )
    status_summary = summarize_export_readiness_statuses(checklist_rows)
    c1, c2, c3 = st.columns(3)
    c1.metric("Ready", status_summary.get("Ready", 0))
    c2.metric("Review", status_summary.get("Review", 0))
    c3.metric("Blocked", status_summary.get("Blocked", 0))
    st.dataframe(
        checklist_rows,
        hide_index=True,
        width="stretch",
    )


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
        width="stretch",
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
    if st.button("Re-run package preflight", width="stretch"):
        st.session_state["preflight_needs_rerun"] = False
        st.rerun()


def build_terraform_validation_guidance():
    """Return Terraform validation guidance rows for the Export tab."""
    return [
        {
            "Mode": "Package Preflight",
            "When To Use": "Before ZIP build in the app",
            "Command Or Action": "Review Preflight Review and Build Terraform Project",
            "Purpose": "Blocks unsafe packages before download.",
        },
        {
            "Mode": "Offline Format Check",
            "When To Use": "Local or offline package review",
            "Command Or Action": (
                "python scripts/validate_terraform_package.py or "
                "terraform fmt -check -recursive"
            ),
            "Purpose": "Checks Terraform formatting without provider downloads.",
        },
        {
            "Mode": "Strict Init Validate",
            "When To Use": "CI, release checks, or connected operator review",
            "Command Or Action": (
                "python scripts/validate_terraform_package.py --init-validate"
            ),
            "Purpose": "Runs provider-backed init and validate; fails on registry issues.",
        },
        {
            "Mode": "Local Provider Download Tolerance",
            "When To Use": "Local VPN, proxy, DNS, or offline provider download issues",
            "Command Or Action": (
                "python scripts/validate_terraform_package.py --init-validate "
                "--allow-provider-download-failure"
            ),
            "Purpose": "Allows only recognized provider download failures locally.",
        },
    ]


def render_terraform_validation_guidance():
    """Render validation mode guidance without executing Terraform."""
    st.markdown("### Terraform Validation Guidance")
    st.info(
        "The app does not execute Terraform or contact provider registries. "
        "Use these checks after downloading and extracting the Terraform bundle."
    )
    st.dataframe(
        build_terraform_validation_guidance(),
        hide_index=True,
        width="stretch",
    )


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
    if st.button("Build Terraform Project", width="stretch"):
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
        st.info(
            "The Terraform bundle includes a root README.md with operator "
            "instructions, required review files, image ID steps, and "
            "deployment-target notes."
        )
        st.download_button(
            label="Download Terraform Bundle",
            data=st.session_state["zip_data"],
            file_name=f"{project_name}.zip",
            mime="application/zip",
            width="stretch",
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
    render_bundle_contents_preview()
    render_build_readiness_checklist(
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
    render_terraform_validation_guidance()
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
