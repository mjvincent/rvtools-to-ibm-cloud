import streamlit as st
import pandas as pd
from logic_engine import (
    map_vmware_to_ibm_vpc,
    create_terraform_structure,
    render_terraform_templates,
    generate_variables_hcl,
    generate_tfvars
)

# --- Table Configuration Constants ---
TABLE_CONFIG = {
    "Exclude?": st.column_config.CheckboxColumn("Exclude?"),
    "High Perf?": st.column_config.CheckboxColumn("High Perf?"),
    "Storage Tier": st.column_config.SelectboxColumn(
        "Tier",
        options=["3iops-tier", "5iops-tier", "10iops-tier"]
    ),
    "State": st.column_config.TextColumn("vCenter State")
}

DISABLED_COLS = [
    "VM Name", "Original Specs", "IBM Profile",
    "Data Status", "Total Storage GB", "State"
]

st.set_page_config(page_title="IBM Cloud Terraform Generator", layout="wide")
st.title("🚀 RVTools to IBM Cloud VPC")

# --- Sidebar ---
st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox(
    "Target IBM Region", ["us-south", "us-east", "eu-gb", "jp-tok"]
)
# RE-IMPLEMENTED: Right-Sizing Slider Block
st.sidebar.header("Right-Sizing Settings")
modes = [
    "Conservative (30%)",
    "IBM Standard (40%)",
    "Moderate (50%)",
    "Aggressive (70%)",
    "Custom"
]
threshold_mode = st.sidebar.selectbox("Standard Thresholds", modes, index=1)

if threshold_mode == "Custom":
    utilization_threshold = st.sidebar.slider(
        "Custom CPU Threshold (%)", 1, 100, 40
    )
else:
    # Extracts the integer from the string (e.g., "40")
    utilization_threshold = int(''.join(filter(str.isdigit, threshold_mode)))
project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")
uploaded_file = st.sidebar.file_uploader("Upload RVTools", type=["xlsx"])

if uploaded_file is not None:
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')

    cap_col = next((c for c in df_vdisk.columns if 'Capacity' in c), None)
    vm_col = next((c for c in df_vdisk.columns if 'VM' in c), 'VM')
    disk_summary = {}
    if cap_col:
        disk_summary = df_vdisk.groupby(vm_col)[cap_col].sum().to_dict()

    processed_vms = []
    for index, row in df_vinfo.iterrows():
        vm_name = row.get('VM', 'Unknown')
        usage = row.get('CPU Usage %')
        p_state = row.get('Powerstate', 'poweredOn')
        orig_cpu = row.get('CPUs', 1)
        orig_ram = row.get('Memory', 1024)

        total_gb = round(disk_summary.get(vm_name, 0) / 1024, 2)

        # 1. Telemetry Health Logic - Fixed E701 (No Colons on same line)
        is_un_cpu = (usage is None or pd.isna(usage))
        is_un_disk = (total_gb <= 0.5)

        status_parts = []
        if is_un_cpu:
            status_parts.append("Missing CPU")
        if is_un_disk:
            status_parts.append("Missing Storage")
        status_msg = " + ".join(status_parts) if status_parts else "Healthy"

        # 2. Storage Tier Logic (Tightened for 3 IOPS)
        is_db = any(x in vm_name.upper() for x in ['SQL', 'DB', 'PROD', 'SAP'])

        if is_db:
            suggested_tier = '10iops-tier'
        elif not is_un_cpu and usage > 70:
            suggested_tier = '5iops-tier'
        else:
            suggested_tier = '3iops-tier'

        # 3. Mapping Call using the dynamic threshold from Sidebar
        calc_usage = 100 if is_un_cpu else usage

        # We pass utilization_threshold here instead of a hardcoded 40
        mapping = map_vmware_to_ibm_vpc(
            orig_cpu,
            orig_ram,
            calc_usage,
            target_region,
            utilization_threshold
        )

        # Fixed E501: Vertical dictionary list
        processed_vms.append({
            'Exclude?': p_state == 'poweredOff',
            'VM Name': vm_name,
            'State': p_state,
            'Original Specs': f"{orig_cpu}v / {orig_ram}M",
            'IBM Profile': mapping['profile'],
            'Storage Tier': suggested_tier,
            'High Perf?': is_db,
            'Data Status': status_msg,
            'Total Storage GB': total_gb,
            'CPU Usage': usage if usage is not None else 0,
            'Right-Sized': "⚠️" if (is_un_cpu or is_un_disk) else "✅"
        })

    # Display Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total VMs", len(processed_vms))
    ex_count = len([v for v in processed_vms if v['Exclude?']])
    m2.metric("Excluded", ex_count)
    cpu_df = pd.DataFrame(processed_vms)
    avg_cpu_val = int(cpu_df['CPU Usage'].mean())
    m3.metric("Avg CPU %", f"{avg_cpu_val}%")

    edited_df = st.data_editor(
        pd.DataFrame(processed_vms),
        column_config=TABLE_CONFIG,
        disabled=DISABLED_COLS,
        hide_index=True
    )

    # 4. Build Button Area
    if st.button("Build Terraform Project"):
        final_vms = [
            v for v in edited_df.to_dict('records') if not v['Exclude?']
        ]
        with st.status("🏗️ Building...") as status:
            try:
                z = f"{target_region}-1"
                vsi, vpc, stor = render_terraform_templates(
                    final_vms, target_region, z
                )
                var = generate_variables_hcl()
                tfv = generate_tfvars(target_region, z, project_name)
                create_terraform_structure(
                    project_name, vsi, vpc, stor, var, tfv
                )
                status.update(label="Success!", state="complete")
                st.snow()
            except Exception as e:
                st.error(f"Build Failed: {e}")

    # 5. UI Legend (Move this OUTSIDE the button block)
    st.write("---")
    st.write("### 🧭 UI Legend & Logic Guide")
    l_col1, l_col2, l_col3 = st.columns(3)

    with l_col1:
        st.markdown("**Status Icons**")
        st.write("✅ : VM is correctly right-sized.")
        st.write("❌ : Profile matches original specs (No savings).")
        st.write("⚠️ : Missing data; reverted to Like-for-Like.")

    with l_col2:
        st.markdown("**Storage Tiering**")
        st.write("- **10 IOPS:** DB/PROD keywords found.")
        st.write("- **5 IOPS:** CPU utilization > 70%.")
        st.write("- **3 IOPS:** Default for cost optimization.")

    with l_col3:
        st.markdown("**Exclusion Rules**")
        st.write("VMs with state `poweredOff` are auto-checked for exclusion.")
