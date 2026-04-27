import streamlit as st
import pandas as pd
import shutil
from logic_engine import (
    map_vmware_to_ibm_vpc,
    create_terraform_structure,
    render_terraform_templates
)

st.set_page_config(page_title="IBM Cloud Terraform Generator", layout="wide")
st.title("🚀 RVTools to IBM Cloud VPC")

st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox(
    "Target IBM Region",
    ["us-south", "us-east", "eu-gb", "jp-tok"]
)
project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")

uploaded_file = st.sidebar.file_uploader("Upload RVTools XLSX", type=["xlsx"])

if uploaded_file:
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')
    st.success(f"Successfully loaded {len(df_vinfo)} VMs.")

    processed_vms = []
    for index, row in df_vinfo.iterrows():
        vm_name = row['VM']
        vm_disks = df_vdisk[df_vdisk['VM'] == vm_name]

        disk_list = []
        for d_idx, d_row in vm_disks.iterrows():
            disk_list.append({
                "label": d_row['Disk'],
                "capacity_gb": int(d_row['Capacity MiB'] / 1024)
            })

        mapping = map_vmware_to_ibm_vpc(
            row['CPUs'],
            row['Memory'],
            region=target_region
        )

        processed_vms.append({
            "VM Name": vm_name,
            "IBM Profile": mapping['profile'],
            "Zone": mapping['zone'],
            "Disks": disk_list
        })

    st.write("### Target IBM Cloud Configuration Preview")
    st.dataframe(pd.DataFrame(processed_vms).drop(columns=['Disks']))

    if st.button("Build Terraform Project"):
        selected_zone = processed_vms[0]['Zone'] if processed_vms else "zone-1"

        vsi_hcl, vpc_hcl, storage_hcl = render_terraform_templates(
            processed_vms,
            target_region,
            selected_zone
        )

        create_terraform_structure(
            project_name,
            vsi_hcl,
            vpc_hcl,
            storage_hcl
        )

        shutil.make_archive(project_name, 'zip', project_name)

        with open(f"{project_name}.zip", "rb") as fp:
            st.download_button(
                label="📥 Download Actionable Terraform Folder",
                data=fp,
                file_name=f"{project_name}.zip",
                mime="application/zip"
            )
        st.balloons()