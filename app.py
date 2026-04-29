import io
import zipfile
import streamlit as st
import pandas as pd
from logic_engine import (
    map_vmware_to_ibm_vpc,
    render_terraform_templates,
    generate_variables_hcl,
    generate_tfvars
)

# --- Table Configuration ---
TABLE_CONFIG = {
    "Exclude?": st.column_config.CheckboxColumn("Exclude?"),
    "Compute (Mo)": st.column_config.NumberColumn("Compute (Mo)",
                                                  format="$%.2f"),
    "Storage (Mo)": st.column_config.NumberColumn("Storage (Mo)",
                                                  format="$%.2f"),
    "Total Monthly": st.column_config.NumberColumn("Total Monthly",
                                                   format="$%.2f"),
    "Storage Tier": st.column_config.SelectboxColumn(
        "Tier", options=["3iops-tier", "5iops-tier", "10iops-tier"]
    )
}

# Added 'Monthly Cost' and 'Right-Sized' to disabled list
DISABLED_COLS = [
    "VM Name", "Original Specs", "IBM Profile",
    "Data Status", "Total Storage GB", "Monthly Cost", "Right-Sized"
]

st.set_page_config(page_title="IBM Cloud Terraform Generator", layout="wide")
st.title("🚀 RVTools to IBM Cloud VPC")

# --- Sidebar ---
st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox(
    "Target IBM Region", ["us-south", "us-east", "eu-gb", "jp-tok"]
)

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

        # Storage Calculation
        total_gb = round(disk_summary.get(vm_name, 0) / 1024, 2)

        # Telemetry Health
        is_un_cpu = (usage is None or pd.isna(usage))
        is_un_disk = (total_gb <= 0.5)

        status_parts = []
        if is_un_cpu:
            status_parts.append("Missing CPU")
        if is_un_disk:
            status_parts.append("Missing Storage")
        status_msg = " + ".join(status_parts) if status_parts else "Healthy"

        # Storage Tiering Logic
        is_db = any(x in vm_name.upper() for x in ['SQL', 'DB', 'PROD', 'SAP'])
        if is_db:
            suggested_tier = '10iops-tier'
        elif not is_un_cpu and usage > 70:
            suggested_tier = '5iops-tier'
        else:
            suggested_tier = '3iops-tier'

        calc_usage = 100 if is_un_cpu else usage

        # Mapping Logic
        mapping = map_vmware_to_ibm_vpc(
            orig_cpu,
            orig_ram,
            calc_usage,
            target_region,
            utilization_threshold,
            total_gb,        # New Argument 6
            suggested_tier   # New Argument 7
        )

        processed_vms.append({
            'Exclude?': p_state == 'poweredOff',
            'VM Name': vm_name,
            'Original Specs': f"{orig_cpu}v / {orig_ram}M",
            'IBM Profile': mapping['profile'],
            'Compute (Mo)': mapping['compute_cost'],  # New Column
            'Storage (Mo)': mapping['storage_cost'],  # New Column
            'Monthly Cost': mapping['monthly'],
            'Right-Sized': "✅" if mapping['is_rightsized'] else "❌",
            'Storage Tier': suggested_tier,
            'Total Storage GB': total_gb,
            'Data Status': status_msg,
            'Usage': calc_usage
        })

    # --- 1. Display Metrics (Only once!) ---
    df_final = pd.DataFrame(processed_vms)

    total_vms = len(df_final)
    active_vms = df_final[~df_final['Exclude?']]
    total_monthly = active_vms['Monthly Cost'].sum()

    # Calculate baseline for the 'delta' (savings) display
    extracted_cpus = df_final['Original Specs'].str.extract(r'(\d+)')
    baseline_cpu_total = extracted_cpus.astype(int)[0].sum()
    baseline_total = baseline_cpu_total * 30  # Baseline estimate
    savings = baseline_total - total_monthly

    m1, m2, m3 = st.columns(3)
    m1.metric("Total VMs", total_vms)

    m2.metric(
        label="Total Monthly Spend",
        value=f"${total_monthly:,.2f}",
        delta=f"-${savings:,.2f} vs Baseline"
    )

    # For the Average metric, we only average VMs that HAVE data
    # so the 100% "safety" values don't skew the results.
    real_usage = df_final[df_final['Data Status'] == "Healthy"]['Usage']
    avg_cpu_val = int(real_usage.mean()) if not real_usage.empty else 0
    m3.metric("Avg Fleet Utilization", f"{avg_cpu_val}%")

    # --- 2. Display the Table (Crucial: Must be ABOVE the button) ---
    edited_df = st.data_editor(
        df_final.drop(columns=['Usage']),
        column_config=TABLE_CONFIG,
        disabled=DISABLED_COLS,
        hide_index=True,
        use_container_width=True
    )

    # 1. Prepare the data
    csv_proposal = edited_df.to_csv(index=False).encode('utf-8')

    # 2. Create the Download Button in the Sidebar or main area
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download Business Case (CSV)",
        data=csv_proposal,
        file_name=f"{project_name}_proposal.csv",
        mime="text/csv",
        help="Download the full right-sized mapping with broken-down costs."
    )

    # Build Button Area
    if st.button("Build Terraform Project"):
        with st.status("🏗️ Packaging Terraform Project...") as status:
            try:
                # 1. Filter out excluded VMs
                final_vms = [
                    v for v in edited_df.to_dict('records')
                    if not v['Exclude?']
                ]

                # 2. Generate the actual Terraform content strings
                z_name = f"{target_region}-1"
                vsi, vpc, stor = render_terraform_templates(
                    final_vms, target_region, z_name
                )
                var = generate_variables_hcl()
                tfv = generate_tfvars(target_region, z_name, project_name)

                # 3. Create an in-memory buffer for the zip file
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(
                    zip_buffer, "a", zipfile.ZIP_DEFLATED, False
                ) as zip_file:
                    files_to_add = {
                        "main.tf": vpc,
                        "variables.tf": var,
                        "terraform.tfvars": tfv,
                        "modules/vsi/main.tf": vsi,
                        "modules/storage/main.tf": stor
                    }

                    for f_path, content in files_to_add.items():
                        zip_file.writestr(f_path, content)

                # Store the zip in session state so it persists
                st.session_state.zip_data = zip_buffer.getvalue()
                status.update(label="Bundle Created!", state="complete")
                st.snow()
            except Exception as e:
                st.error(f"Packaging Failed: {e}")

    # 4. Display Persistent Download Button Outside the IF and STATUS blocks
    if "zip_data" in st.session_state:
        st.success("✅ Terraform Project is ready!")
        st.download_button(
            label="💾 Download Terraform Bundle (.zip)",
            data=st.session_state.zip_data,
            file_name=f"{project_name}.zip",
            mime="application/zip",
            use_container_width=True
        )

    # UI Legend
    st.write("---")
    st.write("### 🧭 UI Legend & Logic Guide")
    l_col1, l_col2, l_col3 = st.columns(3)

    with l_col1:
        st.markdown("**Status Icons**")
        st.write("✅ : VM is right-sized (IBM Spec < Original).")
        st.write("❌ : No right-sizing possible (Safety Match).")

    with l_col2:
        st.markdown("**Storage Tiering (IOPS)**")
        st.write("- **10 IOPS:** Triggered by 'DB', 'SQL', or 'SAP' keywords.")
        st.write("- **5 IOPS:** Triggered by high CPU utilization (>70%).")
        st.write("- **3 IOPS:** Standard tier for general workloads.")

    with l_col3:
        st.markdown("**Baseline Savings Math**")
        st.write("- **On-Prem Cost:** Estimated at $30/vCPU monthly.")
        st.write("  *(Includes power, cooling, hardware, and licensing)*")
        st.write("- **IBM Cost:** Actual VSI price + Tiered Storage.")
