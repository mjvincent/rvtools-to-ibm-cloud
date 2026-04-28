import streamlit as st
import pandas as pd
from logic_engine import (
    map_vmware_to_ibm_vpc,
    create_terraform_structure,
    render_terraform_templates,
    generate_variables_hcl,
    generate_tfvars
)

st.set_page_config(page_title="IBM Cloud Terraform Generator", layout="wide")
st.title("🚀 RVTools to IBM Cloud VPC")

# --- Sidebar Configuration ---
st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox(
    "Target IBM Region",
    ["us-south", "us-east", "eu-gb", "jp-tok"]
)

st.sidebar.header("Right-Sizing Settings")
modes = [
    "Conservative (30%)", "IBM Standard (40%)",
    "Moderate (50%)", "Aggressive (70%)", "Custom"
]
threshold_mode = st.sidebar.selectbox("Standard Thresholds", modes)

if threshold_mode == "Custom":
    utilization_threshold = st.sidebar.slider(
        "Custom CPU Threshold (%)", 1, 100, 40
    )
else:
    utilization_threshold = int(
        ''.join(filter(str.isdigit, threshold_mode))
    )

project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")
uploaded_file = st.sidebar.file_uploader("Upload RVTools XLSX", type=["xlsx"])

# --- Main Logic Block ---
if uploaded_file is not None:
    # 1. Load the data
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')

    # Identify columns dynamically
    cap_col = next((c for c in df_vdisk.columns if 'Capacity' in c), None)
    vm_col = next((c for c in df_vdisk.columns if 'VM' in c), 'VM')

    disk_summary = {}
    if cap_col:
        disk_summary = df_vdisk.groupby(vm_col)[cap_col].sum().to_dict()

    # 2. Process with Validation and Comparative Logic
    processed_vms = []
    data_warning_triggered = False

    for index, row in df_vinfo.iterrows():
        vm_name = row.get('VM', 'Unknown')
        usage = row.get('CPU Usage %', 100)
        orig_cpu = row.get('CPUs', 1)
        orig_ram = row.get('Memory', 1024)

        # Storage check
        total_mb = disk_summary.get(vm_name, 0)
        total_gb = round(total_mb / 1024, 2)

        # Validation: Check for missing CPU or tiny/missing storage
        is_unknown_cpu = (usage == 100 or pd.isna(usage))
        is_unknown_disk = (total_gb <= 0.5)  # Flag < 512MB as "No Data"

        if is_unknown_cpu or is_unknown_disk:
            data_warning_triggered = True
            mapping = map_vmware_to_ibm_vpc(
                orig_cpu, orig_ram, 100, target_region, 100
            )
            status_icon = "⚠️ No Data"
        else:
            mapping = map_vmware_to_ibm_vpc(
                orig_cpu, orig_ram, usage,
                target_region, utilization_threshold
            )
            status_icon = "✅" if mapping['is_rightsized'] else "❌"

        processed_vms.append({
            'VM Name': vm_name,
            'Original Specs': f"{orig_cpu}v / {orig_ram}M",
            'IBM Proposed': mapping['profile'],
            'Right-Sized': status_icon,
            'Storage (GB)': total_gb,
            'Storage Tier': '10iops-tier',
            'Override': False
        })

    if data_warning_triggered:
        st.warning(
            "**Note:** Some VMs are missing telemetry. "
            "Reverting to **Like-for-Like** for those entries."
        )

    st.write("### Review Migration Plan & Manual Overrides")

    # 3. Interactive Table
    edited_df = st.data_editor(
        pd.DataFrame(processed_vms),
        column_config={
            "Override": st.column_config.CheckboxColumn("Keep Original?"),
            "Storage Tier": st.column_config.SelectboxColumn(
                "IBM Storage Tier",
                options=["5iops-tier", "10iops-tier", "general-purpose"]
            )
        },
        disabled=[
            "VM Name", "Original Specs", "IBM Proposed",
            "Right-Sized", "Storage (GB)"
        ],
        hide_index=True
    )

    # 4. Build Button
    if st.button("Build Terraform Project"):
        final_vms = edited_df.to_dict('records')
        with st.status("Generating Migration Files...") as status:
            try:
                selected_zone = f"{target_region}-1"
                vsi_h, vpc_h, stor_h = render_terraform_templates(
                    final_vms, target_region, selected_zone
                )
                var_h = generate_variables_hcl()
                tfvars_h = generate_tfvars(
                    target_region, selected_zone, project_name
                )
                create_terraform_structure(
                    project_name, vsi_h, vpc_h, stor_h, var_h, tfvars_h
                )
                status.update(label="Build Complete!", state="complete")
                st.success(f"Project '{project_name}' created!")
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("Please upload an RVTools XLSX file to begin.")
