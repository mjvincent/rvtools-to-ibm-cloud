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

DISABLED_COLS = [
    "VM Name", "Original Specs", "IBM Profile",
    "Data Status", "Total Storage GB", "Monthly Cost", "Right-Sized",
    "v_p_Ratio", "Ready_Pct", "Overall_MHz"
]

st.set_page_config(page_title="IBM Cloud Terraform Generator", layout="wide")

# --- Header Section with Logo and Title ---
col1, col2 = st.columns([1, 8])

with col1:
    # Defining the URL as a variable keeps the st.image call short and clean
    ibm_logo_url = (
        "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg"
    )
    st.image(ibm_logo_url, width=80)

with col2:
    st.title("RVTools to IBM Cloud VPC")

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
    # 1. LOAD TABS
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')
    df_vcpu = pd.read_excel(uploaded_file, sheet_name='vCPU')
    df_vhost = pd.read_excel(uploaded_file, sheet_name='vHost')
    df_vcluster = pd.read_excel(uploaded_file, sheet_name='vCluster')

    # 2. CLEAN COLUMN NAMES
    for df in [df_vinfo, df_vdisk, df_vcpu, df_vhost, df_vcluster]:
        df.columns = df.columns.str.strip()

    # 3. STORAGE SUMMARY (vDisk)
    cap_col = next((c for c in df_vdisk.columns if 'Capacity' in c), None)
    vm_col = next((c for c in df_vdisk.columns if 'VM' in c), 'VM')
    disk_summary = {}
    if cap_col:
        disk_summary = df_vdisk.groupby(vm_col)[cap_col].sum().to_dict()

    # 4. VCPU PERFORMANCE MAP
    vcpu_metrics = {}
    for _, v_row in df_vcpu.iterrows():
        name = v_row.get('VM')
        vcpu_metrics[name] = {
            'ready_pct': v_row.get('CPU ready %', 0),
            'co_stop': v_row.get('CPU co-stop', 0),
            'usage_mhz': v_row.get('Overall', 0),
            'limit_mhz': v_row.get('Limit', 0)
        }

    # 5. HOST CAPACITY MAP
    host_capacity = {}
    for _, h_row in df_vhost.iterrows():
        h_name = h_row.get('Host')
        host_capacity[h_name] = {
            'total_mhz': h_row.get('Speed', 0),
            'p_cores': h_row.get('# Cores', 1),
            'mhz_used_pct': h_row.get('CPU usage %', 0)
        }

    # 6. PROCESS INDIVIDUAL VMS
    processed_vms = []
    for index, row in df_vinfo.iterrows():
        vm_name = row.get('VM', 'Unknown')
        usage = row.get('CPU Usage %')
        p_state = row.get('Powerstate', 'poweredOn')
        orig_cpu = row.get('CPUs', 1)
        orig_ram = row.get('Memory', 1024)
        host_name = row.get('Host', 'Unknown')

        # Pull Metrics
        perf = vcpu_metrics.get(
            vm_name,
            {'ready_pct': 0, 'co_stop': 0, 'usage_mhz': 0, 'limit_mhz': 0}
        )
        h_cap = host_capacity.get(
            host_name,
            {'p_cores': 1, 'total_mhz': 0}
        )

        # Logic: Performance & Contention
        is_starving = perf['ready_pct'] > 5.0 or perf['co_stop'] > 3.0
        is_throttled = (
            perf['limit_mhz'] > 0 and
            perf['usage_mhz'] >= (perf['limit_mhz'] * 0.95)
        )

        # Logic: Host Density
        total_vcpus_on_host = df_vinfo[
            df_vinfo['Host'] == host_name
        ]['CPUs'].sum()
        v_to_p_ratio = round(total_vcpus_on_host / h_cap['p_cores'], 1)

        # Logic: Storage & Tiering
        total_gb = round(disk_summary.get(vm_name, 0) / 1024, 2)
        is_db = any(x in vm_name.upper() for x in ['SQL', 'DB', 'PROD', 'SAP'])
        if is_db:
            suggested_tier = '10iops-tier'
        elif (usage is not None and usage > 70) or is_throttled:
            suggested_tier = '5iops-tier'
        else:
            suggested_tier = '3iops-tier'

        # Logic: Telemetry Health
        is_un_cpu = (usage is None or pd.isna(usage))
        is_un_disk = (total_gb <= 0.5)

        status_parts = []
        if is_un_cpu:
            status_parts.append("Missing CPU")
        if is_un_disk:
            status_parts.append("Missing Storage")
        if is_starving:
            status_parts.append("High Contention")
        if is_throttled:
            status_parts.append("CPU Throttled")

        is_zombie = (not is_un_cpu and usage < 5 and perf['usage_mhz'] < 100)
        if is_zombie:
            status_parts.append("Zombie VM")

        status_msg = " + ".join(status_parts) if status_parts else "Healthy"

        # Smart Decision: Safety Override
        calc_usage = 100 if (is_un_cpu or is_starving or
                             is_throttled) else usage

        mapping = map_vmware_to_ibm_vpc(
            orig_cpu, orig_ram, calc_usage, target_region,
            utilization_threshold, total_gb, suggested_tier
        )

        processed_vms.append({
            'Exclude?': p_state == 'poweredOff',
            'VM Name': vm_name,
            'Original Specs': f"{orig_cpu}v / {orig_ram}M",
            'IBM Profile': mapping['profile'],
            'Compute (Mo)': mapping['compute_cost'],
            'Storage (Mo)': mapping['storage_cost'],
            'Monthly Cost': mapping['monthly'],
            'Right-Sized': "✅" if mapping['is_rightsized'] else "❌",
            'Storage Tier': suggested_tier,
            'Total Storage GB': total_gb,
            'Data Status': status_msg,
            'v_p_Ratio': v_to_p_ratio,
            'Ready_Pct': perf['ready_pct'],
            'Overall_MHz': perf['usage_mhz']
        })

    # --- 7. POST-PROCESSING & METRICS ---
    df_final = pd.DataFrame(processed_vms)

    # Calculate Fleet-wide Density
    total_vcpus_all = df_vinfo['CPUs'].sum()
    total_p_cores_all = df_vhost['# Cores'].sum()
    fleet_ratio = round(
        total_vcpus_all / total_p_cores_all, 1
    ) if total_p_cores_all > 0 else 0

    # Calculate Savings
    total_monthly = df_final[~df_final['Exclude?']]['Monthly Cost'].sum()
    extracted_cpus = df_final['Original Specs'].str.extract(r'(\d+)')
    baseline_total = extracted_cpus.astype(int)[0].sum() * 30
    savings = baseline_total - total_monthly

    # Infrastructure Resilience (N+1)
    total_cluster_mhz = df_vcluster['TotalCpu'].sum()
    max_host_mhz = df_vhost['Speed'].max()
    total_vm_demand_mhz = df_vcpu['Overall'].sum()
    n_plus_1 = (total_cluster_mhz - max_host_mhz) - total_vm_demand_mhz

    # --- 8. DASHBOARD DISPLAY ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total VMs", len(df_final))
    m2.metric(
        label="Monthly Spend",
        value=f"${total_monthly:,.2f}",
        delta=f"-${savings:,.2f} vs Baseline"
    )
    m3.metric(
        "N+1 Headroom",
        f"{int(n_plus_1):,} MHz",
        delta=f"{fleet_ratio}:1 Density",
        delta_color="normal" if fleet_ratio < 6 else "inverse",
        help="Capacity if largest host fails. Density is total vCPU/pCore."
    )
    zombies = len(df_final[df_final['Data Status'].str.contains("Zombie")])
    m4.metric(
        "Zombie VMs", zombies,
        delta_color="inverse",
        delta="Clear" if zombies == 0 else f"{zombies} Review"
    )

    # --- 9. DATA TABLE & ACTIONS ---
    edited_df = st.data_editor(
        df_final,
        column_config=TABLE_CONFIG,
        disabled=DISABLED_COLS,
        hide_index=True,
        use_container_width=True
    )

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download Business Case (CSV)",
        data=edited_df.to_csv(index=False).encode('utf-8'),
        file_name=f"{project_name}_proposal.csv",
        mime="text/csv"
    )

    if st.button("Build Terraform Project"):
        with st.status("🏗️ Packaging Project...") as status:
            try:
                final_vms = [
                    v for v in edited_df.to_dict('records')
                    if not v['Exclude?']
                ]
                z_name = f"{target_region}-1"
                vsi, vpc, stor = render_terraform_templates(
                    final_vms, target_region, z_name
                )
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a") as zf:
                    zf.writestr("main.tf", vpc)
                    zf.writestr("variables.tf", generate_variables_hcl())
                    zf.writestr("terraform.tfvars", generate_tfvars(
                        target_region, z_name, project_name
                    ))
                    zf.writestr("modules/vsi/main.tf", vsi)
                    zf.writestr("modules/storage/main.tf", stor)
                st.session_state.zip_data = zip_buffer.getvalue()
                status.update(label="Complete!", state="complete")
                st.snow()
            except Exception as e:
                st.error(f"Error: {e}")

    if "zip_data" in st.session_state:
        st.download_button(
            label="💾 Download Terraform Bundle",
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
        st.markdown("**Performance Logic**")
        st.write("- **Safety Match:** Disabled if Ready % > 5 or Co-stop > 3.")
        st.write("- **Zombie:** Flagged if Usage < 5% and MHz < 100.")
    with l_col2:
        st.markdown("**Storage Tiering**")
        st.write("- **10 IOPS:** DB keywords (SQL, SAP, etc).")
        st.write("- **5 IOPS:** High CPU utilization or throttling.")
    with l_col3:
        st.markdown("**Infrastructure Resilience**")
        st.write("- **N+1 Calculation:** (Cluster MHz - Max Host) - Demand.")
        st.write("- **Density:** Healthy target is under 6:1 (vCPU:pCore).")
