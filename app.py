import io
import zipfile

import pandas as pd
import streamlit as st

from catalog_pricing import get_pricing_catalog, pricing_status_summary
from assessment_quality import (
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
)
from handoff import (
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_memory_readiness_csv,
    generate_migration_manifest,
    generate_migration_runbook,
    generate_nic_mapping_csv,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
)
from models import MigrationVm
from rvtools_parser import normalize_network_name, parse_rvtools_workbook
from terraform_renderer import generate_tfvars, render_terraform_templates
from ui import (
    DECISION_COLUMNS,
    DISABLED_COLS,
    build_table_config,
    merge_decision_edits,
    render_assessment_quality,
    render_estate_summary,
    render_network_planning,
    render_readiness_legend,
    render_readiness_triage,
    render_storage_planning,
)


st.set_page_config(
    page_title="IBM Cloud Terraform Generator",
    layout="wide"
)

col1, col2 = st.columns([1, 8])
with col1:
    logo = (
        "https://upload.wikimedia.org/wikipedia/commons/5/51/"
        "IBM_logo.svg"
    )
    st.image(logo, width=80)
with col2:
    st.title("RVTools to IBM Cloud VPC")

st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox(
    "Target IBM Region", ["us-south", "us-east", "eu-gb", "jp-tok"]
)

st.sidebar.header("Right-Sizing Settings")
modes = [
    "Conservative (30%)", "IBM Standard (40%)",
    "Moderate (50%)", "Aggressive (70%)", "Custom"
]
threshold_mode = st.sidebar.selectbox("Standard Thresholds", modes, index=1)
if threshold_mode == "Custom":
    utilization_threshold = st.sidebar.slider(
        "Custom CPU Threshold (%)", 1, 100, 40
    )
else:
    utilization_threshold = int(''.join(filter(
        str.isdigit, threshold_mode
    )))

project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")
region_zones = {
    "us-south": ["us-south-1", "us-south-2", "us-south-3"],
    "us-east": ["us-east-1", "us-east-2", "us-east-3"],
    "eu-gb": ["eu-gb-1"],
    "jp-tok": ["jp-tok-1"]
}
target_zone = st.sidebar.selectbox(
    "Target IBM Zone",
    region_zones.get(target_region, [f"{target_region}-1"])
)

st.sidebar.header("Pricing Settings")
pricing_mode_label = st.sidebar.selectbox(
    "Pricing Mode",
    ["Static fallback", "Cached IBM catalog", "Live IBM profile discovery"],
    index=0
)
pricing_mode_map = {
    "Static fallback": "static",
    "Cached IBM catalog": "cached",
    "Live IBM profile discovery": "live",
}
pricing_catalog = get_pricing_catalog(
    pricing_mode_map[pricing_mode_label],
    region=target_region
)
pricing_metadata = pricing_catalog.get("metadata", {})
catalog_profiles = pricing_catalog.get("profiles", [])
storage_tier_rates = pricing_catalog.get("storage_tier_rates")
st.sidebar.caption(pricing_status_summary(pricing_catalog))
if pricing_metadata.get("status"):
    st.sidebar.info(pricing_metadata["status"])

generate_security_groups = st.sidebar.checkbox(
    "Generate Security Groups", value=True
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Upload RVTools, review blockers first, adjust only the decisions that "
    "need human intent, then build the Terraform handoff package."
)
uploaded_file = st.sidebar.file_uploader("Upload RVTools", type=["xlsx"])

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
        columns=["Disk Details", "Network Details", "Readiness Findings"],
        errors="ignore"
    )
    table_config = build_table_config(unique_nets, catalog_profiles)

    render_estate_summary(df_f)

    overview, readiness, vm_review, networks, storage, export = st.tabs([
        "Overview", "Readiness", "VM Review", "Networks", "Storage", "Export"
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

    with vm_review:
        st.subheader("VM Decisions")
        st.caption("This view keeps the active decisions in front. Raw generated fields remain available below for audit and troubleshooting.")
        decision_input_columns = ["VM Key"] + [
            column for column in DECISION_COLUMNS if column in df_table.columns
        ]
        edited_decisions = st.data_editor(
            df_table[decision_input_columns],
            column_config=table_config,
            column_order=[
                column for column in DECISION_COLUMNS if column in df_table.columns
            ],
            disabled=[
                column for column in DISABLED_COLS
                if column in decision_input_columns
            ],
            hide_index=True,
            use_container_width=True,
            key="vm_decision_editor"
        )
        edited_df = merge_decision_edits(df_table, edited_decisions)
        with st.expander("Advanced generated fields"):
            st.dataframe(edited_df, hide_index=True, use_container_width=True)

    with networks:
        render_network_planning(edited_df, unique_nets)

    with storage:
        render_storage_planning(edited_df)

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

        if st.button("Build Terraform Project", use_container_width=True):
            with st.status("Packaging Project...") as status:
                try:
                    final_vm_records = [
                        v for v in edited_df.to_dict('records')
                        if not v['Exclude?']
                    ]
                    final_vms = []
                    for vm in final_vm_records:
                        vm["Disk Details"] = disk_details.get(vm.get("VM Key"), [])
                        vm["Network Details"] = nic_details.get(
                            vm.get("VM Key"), []
                        )
                        vm["Readiness Findings"] = next(
                            (
                                source.get("Readiness Findings", [])
                                for source in processed_vms
                                if source.get("VM Key") == vm.get("VM Key")
                            ),
                            []
                        )
                        final_vms.append(MigrationVm.from_record(vm))

                    terraform_files = render_terraform_templates(
                        final_vms,
                        unique_nets,
                        target_region,
                        target_zone,
                        generate_security_groups,
                        vpc_name,
                        custom_cidrs,
                        address_prefix_strategy,
                        deployment_target,
                        project_name
                    )
                    (
                        vsi, root_main, stor, net, root_vars, root_out,
                        net_vars, net_out, vsi_vars, vsi_out, stor_vars,
                        stor_out
                    ) = terraform_files

                    migration_context = {
                        'project_name': project_name,
                        'target_region': target_region,
                        'target_zone': target_zone,
                        'vpc_name': vpc_name,
                        'address_prefix_strategy': address_prefix_strategy,
                        'deployment_target': deployment_target,
                        'generate_security_groups': generate_security_groups,
                        'pricing_mode': pricing_metadata.get('mode'),
                        'pricing_source': pricing_metadata.get('source'),
                        'pricing_confidence': pricing_metadata.get('confidence'),
                        'pricing_last_updated': pricing_metadata.get(
                            'last_updated'
                        ),
                        'assessment_quality': assessment_quality,
                    }

                    zip_b = io.BytesIO()
                    with zipfile.ZipFile(zip_b, "a") as zf:
                        zf.writestr("main.tf", root_main)
                        zf.writestr("variables.tf", root_vars)
                        zf.writestr("outputs.tf", root_out)
                        zf.writestr(
                            "terraform.tfvars",
                            generate_tfvars(
                                target_region, target_zone, project_name
                            )
                        )
                        zf.writestr("modules/networking/main.tf", net)
                        zf.writestr("modules/networking/variables.tf", net_vars)
                        zf.writestr("modules/networking/outputs.tf", net_out)
                        zf.writestr("modules/vsi/main.tf", vsi)
                        zf.writestr("modules/vsi/variables.tf", vsi_vars)
                        zf.writestr("modules/vsi/outputs.tf", vsi_out)
                        zf.writestr("modules/storage/main.tf", stor)
                        zf.writestr("modules/storage/variables.tf", stor_vars)
                        zf.writestr("modules/storage/outputs.tf", stor_out)
                        zf.writestr(
                            "migration-manifest.json",
                            generate_migration_manifest(final_vms, migration_context)
                        )
                        zf.writestr(
                            "assessment-quality.json",
                            generate_assessment_quality_json(assessment_quality)
                        )
                        zf.writestr(
                            "assessment-quality.csv",
                            generate_assessment_quality_csv(assessment_quality)
                        )
                        zf.writestr(
                            "vm-mapping.csv",
                            generate_vm_mapping_csv(final_vms)
                        )
                        zf.writestr(
                            "disk-mapping.csv",
                            generate_disk_mapping_csv(final_vms)
                        )
                        zf.writestr(
                            "nic-mapping.csv",
                            generate_nic_mapping_csv(
                                final_vms, generate_security_groups
                            )
                        )
                        zf.writestr(
                            "memory-readiness.csv",
                            generate_memory_readiness_csv(final_vms)
                        )
                        zf.writestr(
                            "readiness-findings.csv",
                            generate_readiness_findings_csv(final_vms)
                        )
                        zf.writestr(
                            "image-import-variables.tfvars.example",
                            generate_image_import_tfvars(final_vms)
                        )
                        zf.writestr(
                            "migration-runbook.md",
                            generate_migration_runbook(migration_context)
                        )

                    st.session_state['zip_data'] = zip_b.getvalue()
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
