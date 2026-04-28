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
    # Read both tabs
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')

    # Group the disks by VM Name to get total capacity
    # Note: Column names in RVTools are usually 'VM' and 'Capacity MB'
    disk_summary = df_vdisk.groupby('VM')['Capacity MB'].sum().to_dict()

    raw_data = []
    for index, row in df_vinfo.iterrows():
        vm_name = row.get('VM', 'Unknown')

        # Pull the total disk capacity for this specific VM
        total_capacity_mb = disk_summary.get(vm_name, 0)
        total_capacity_gb = round(total_capacity_mb / 1024, 2)

        raw_data.append({
            'VM Name': vm_name,
            'vCPUs': row.get('CPUs', 1),
            'RAM': row.get('Memory', 1024),
            'CPU Usage': row.get('CPU Usage %', 100),
            'Total Storage GB': total_capacity_gb,
            'Storage Tier': '10iops-tier'  # Default to high-perf
        })

    # 2. Process with Global Threshold and CPU Validation
    processed_vms = []
    cpu_warning_triggered = False

    for vm in raw_data:
        usage = vm.get('CPU Usage')
        is_unknown = (usage == 100 or pd.isna(usage))

        if is_unknown:
            cpu_warning_triggered = True
            # Force Like-for-Like
            mapping = map_vmware_to_ibm_vpc(
                vm['vCPUs'], vm['RAM'], 100, target_region, 100
            )
            status_icon = "⚠️ No Data"
        else:
            mapping = map_vmware_to_ibm_vpc(
                vm['vCPUs'], vm['RAM'], usage,
                target_region, utilization_threshold
            )
            status_icon = "✅" if mapping['is_rightsized'] else "❌"

        vm.update({
            "IBM Profile": mapping['profile'],
            "Right-Sized": status_icon,
            "Override": False
        })
        processed_vms.append(vm)

    if cpu_warning_triggered:
        st.warning(
            "**Note:** Some VMs are missing CPU data. "
            "The tool defaulted to **Like-for-Like** sizing."
        )

    st.write("### Review Migration Plan & Manual Overrides")

    # 3. Interactive Table
    edited_df = st.data_editor(
        pd.DataFrame(processed_vms),
        column_config={
            "Override": st.column_config.CheckboxColumn("Keep Original?"),
            "Total Storage GB": st.column_config.NumberColumn(
                "Storage (GB)", help="Total aggregated disk capacity",
                format="%d"
            ),
            "Storage Tier": st.column_config.SelectboxColumn(
                "IBM Storage Tier",
                options=["5iops-tier", "10iops-tier", "general-purpose"],
                help="Select the IOPS performance tier for migration"
            )
        },
        disabled=["VM Name", "IBM Profile", "Right-Sized", "Total Storage GB"],
        hide_index=True
    )

    # 4. Build Button
    if st.button("Build Terraform Project"):
        final_vms = edited_df.to_dict('records')

        for vm in final_vms:
            if vm['Override']:
                orig_mapping = map_vmware_to_ibm_vpc(
                    vm['vCPUs'], vm['RAM'], 100, target_region, 100
                )
                vm['IBM Profile'] = orig_mapping['profile']

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
                    project_name,
                    vsi_h,
                    vpc_h,
                    stor_h,
                    var_h,
                    tfvars_h
                )
                status.update(label="Build Complete!", state="complete")
                st.success(f"Project '{project_name}' created!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("Please upload an RVTools XLSX file to begin.")
