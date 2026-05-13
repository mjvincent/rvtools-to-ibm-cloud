import io
import zipfile

import pandas as pd
import streamlit as st

from catalog_pricing import get_pricing_catalog, pricing_status_summary
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
from sizing import get_catalog_profiles
from terraform_renderer import generate_tfvars, render_terraform_templates
from ui import DISABLED_COLS, build_table_config, render_dashboard, render_legend


st.set_page_config(
    page_title="IBM Cloud Terraform Generator",
    layout="wide"
)

# --- Header Section ---
col1, col2 = st.columns([1, 8])
with col1:
    logo = (
        "https://upload.wikimedia.org/wikipedia/commons/5/51/"
        "IBM_logo.svg"
    )
    st.image(logo, width=80)
with col2:
    st.title("RVTools to IBM Cloud VPC")

# --- Sidebar ---
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
st.sidebar.markdown(
    "**Override Controls**: Edit any VM row below to customize the target "
    "profile, storage tier, subnet, or security group mapping for Terraform "
    "generation."
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

    df_f = pd.DataFrame([vm.to_record() for vm in processed_vms])
    df_table = df_f.drop(
        columns=["Disk Details", "Network Details", "Readiness Findings"],
        errors="ignore"
    )

    render_dashboard(
        df_f,
        parsed.df_vcluster,
        parsed.df_vhost,
        parsed.df_vcpu,
    )

    # --- TERRAFORM OVERRIDES ---
    with st.expander("Terraform Overrides"):
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

    # --- DATA TABLE ---
    edited_df = st.data_editor(
        df_table,
        column_config=build_table_config(unique_nets, catalog_profiles),
        disabled=DISABLED_COLS,
        hide_index=True,
        use_container_width=True,
        key="main_data_editor"
    )

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="Download Business Case (CSV)",
        data=edited_df.to_csv(index=False).encode('utf-8'),
        file_name=f"{project_name}_proposal.csv",
        mime="text/csv"
    )

    # --- BUILD ACTION ---
    if st.button("Build Terraform Project"):
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
                st.snow()
            except Exception as e:
                st.error(f"Error: {e}")

    # --- DOWNLOAD ---
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

    render_legend()
