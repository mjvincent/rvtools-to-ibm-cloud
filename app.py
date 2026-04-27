import streamlit as st
import pandas as pd
import shutil
import os
# Import your custom logic from parser.py
from logic_engine import map_vmware_to_ibm_vpc, create_terraform_structure, render_terraform_templates

st.set_page_config(page_title="IBM Cloud Terraform Generator", layout="wide")
st.title("🚀 RVTools to IBM Cloud VPC")

# Sidebar Configuration
st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox("Target IBM Region", ["us-south", "us-east", "eu-gb", "jp-tok"])
project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")

uploaded_file = st.sidebar.file_uploader("Upload RVTools XLSX", type=["xlsx"])

if uploaded_file:
    # 1. Read both tabs
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')
    
    st.success(f"Loaded {len(df_vinfo)} VMs and their disk metadata.")
    
    processed_vms = []
    for index, row in df_vinfo.iterrows():
        vm_name = row['VM']
        
        # 2. Filter vDisk tab to find disks belonging to THIS VM
        vm_disks = df_vdisk[df_vdisk['VM'] == vm_name]
        
        # Calculate total capacity or get individual disk sizes
        # RVTools usually reports in MiB, so we convert to GB
        disk_list = []
        for d_index, d_row in vm_disks.iterrows():
            disk_list.append({
                "label": d_row['Disk'],
                "capacity_gb": int(d_row['Capacity MiB'] / 1024)
            })
            
        mapping = map_vmware_to_ibm_vpc(row['CPUs'], row['Memory'], region=target_region)
        
        processed_vms.append({
            "VM Name": vm_name,
            "IBM Profile": mapping['profile'],
            "Zone": mapping['zone'],
            "Disks": disk_list  # Now we have the actual sizes!
        })

    # 3. Generate and Zip
    if st.button("Build Terraform Project"):
        # Notice we are now passing target_region and the zone from the first VM
        selected_zone = processed_vms[0]['Zone'] if processed_vms else "us-south-1"
        
        vsi_hcl, vpc_hcl, storage_hcl = render_terraform_templates(
            processed_vms, 
            target_region, 
            selected_zone
        )
        
        create_terraform_structure(project_name, vsi_hcl, vpc_hcl, storage_hcl)
        
        # 3. Zip it up
        shutil.make_archive(project_name, 'zip', project_name)
        
        # ... (Download button code follows)
        
        with open(f"{project_name}.zip", "rb") as fp:
            st.download_button(
                label="📥 Download Actionable Terraform Folder",
                data=fp,
                file_name=f"{project_name}.zip",
                mime="application/zip"
            )
        st.balloons()