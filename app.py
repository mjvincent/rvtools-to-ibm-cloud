import io
import zipfile
import streamlit as st
import pandas as pd
from logic_engine import (
    IBM_VPC_CATALOG,
    get_catalog_profiles,
    map_vmware_to_ibm_vpc,
    render_terraform_templates,
    generate_tfvars
)

PROFILE_OPTIONS = [""] + get_catalog_profiles()
STORAGE_TIERS = ["3iops-tier", "5iops-tier", "10iops-tier"]

# --- Table Configuration ---
TABLE_CONFIG = {
    "Exclude?": st.column_config.CheckboxColumn("Exclude?"),
    "Compute (Mo)": st.column_config.NumberColumn(
        "Compute (Mo)", format="$%.2f"
    ),
    "Storage (Mo)": st.column_config.NumberColumn(
        "Storage (Mo)", format="$%.2f"
    ),
    "Baseline Cost (Mo)": st.column_config.NumberColumn(
        "Baseline Cost (Mo)", format="$%.2f"
    ),
    "Savings (Mo)": st.column_config.NumberColumn(
        "Savings (Mo)", format="$%.2f"
    ),
    "Total Monthly": st.column_config.NumberColumn(
        "Total Monthly", format="$%.2f"
    ),
    "Storage Tier": st.column_config.SelectboxColumn(
        "Tier", options=STORAGE_TIERS
    ),
    "Override Storage Tier": st.column_config.SelectboxColumn(
        "Override Storage Tier", options=[""] + STORAGE_TIERS
    ),
    "IBM Profile": st.column_config.SelectboxColumn(
        "Profile", options=PROFILE_OPTIONS
    ),
    "Override Profile": st.column_config.SelectboxColumn(
        "Override Profile", options=[""] + PROFILE_OPTIONS
    ),
    "Subnet": st.column_config.TextColumn("Subnet"),
    "Security Group": st.column_config.TextColumn("Security Group")
}

DISABLED_COLS = [
    "VM Name", "Original Specs", "Data Status",
    "Total Storage GB", "Monthly Cost", "Right-Sized", "v_p_Ratio",
    "Ready_Pct", "Overall_MHz",
    "Baseline Cost (Mo)", "Savings (Mo)"
]

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

generate_security_groups = st.sidebar.checkbox(
    "Generate Security Groups", value=True
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Override Controls**: Edit any VM row below to customize the target profile, storage tier, subnet, or security group mapping for Terraform generation."
)


def normalize_network_name(name):
    cleaned = str(name).strip()
    if not cleaned or cleaned.lower() == 'nan':
        cleaned = 'unknown'
    return cleaned.lower().replace(" ", "_").replace("-", "_")

uploaded_file = st.sidebar.file_uploader("Upload RVTools", type=["xlsx"])

if uploaded_file is not None:
    # 1. LOAD TABS
    df_vinfo = pd.read_excel(uploaded_file, sheet_name='vInfo')
    df_vdisk = pd.read_excel(uploaded_file, sheet_name='vDisk')
    df_vcpu = pd.read_excel(uploaded_file, sheet_name='vCPU')
    df_vhost = pd.read_excel(uploaded_file, sheet_name='vHost')
    df_vcluster = pd.read_excel(uploaded_file, sheet_name='vCluster')
    df_vnetwork = pd.read_excel(uploaded_file, sheet_name='vNetwork')

    # 2. CLEAN COLUMN NAMES
    for df in [df_vinfo, df_vdisk, df_vcpu, df_vhost,
               df_vcluster, df_vnetwork]:
        df.columns = df.columns.str.strip()

    # 3. NETWORKING EXTRACTION
    unique_nets = []
    v_net_cols = df_vnetwork.columns.tolist()

    n_col = 'Network' if 'Network' in v_net_cols else v_net_cols[0]
    v_col = 'VLAN ID' if 'VLAN ID' in v_net_cols else None
    ip_col = 'IPv4 Address' if 'IPv4 Address' in v_net_cols else None

    pull_cols = [n_col]
    if v_col:
        pull_cols.append(v_col)
    if ip_col:
        pull_cols.append(ip_col)

    net_subset = df_vnetwork[pull_cols].drop_duplicates()

    for _, row in net_subset.iterrows():
        n_name = str(row[n_col])
        vlan = str(row.get(v_col, '')) if v_col else ''
        raw_ip = str(row.get(ip_col, '10.0.0.1')) if ip_col else '10.0.0.1'

        try:
            p = raw_ip.split('.')
            if len(p) == 4:
                d_cidr = f"{p[0]}.{p[1]}.{p[2]}.0/24"
            else:
                d_cidr = f"10.0.{len(unique_nets) + 1}.0/24"
        except Exception:
            d_cidr = f"10.0.{len(unique_nets) + 1}.0/24"

        unique_nets.append({'name': n_name, 'vlan': vlan, 'cidr': d_cidr})

    # Update TABLE_CONFIG with dynamic Network options
    TABLE_CONFIG["Network"] = st.column_config.SelectboxColumn(
        "Network", options=[""] + [net.get('name', 'unknown-net') for net in unique_nets]
    )
    TABLE_CONFIG["Subnet"] = st.column_config.TextColumn("Subnet")
    TABLE_CONFIG["Security Group"] = st.column_config.TextColumn("Security Group")

    # 4. STORAGE SUMMARY
    cap_c = next((c for c in df_vdisk.columns if 'Capacity' in c), None)
    vm_c = next((c for c in df_vdisk.columns if 'VM' in c), 'VM')
    disk_sum = {}
    if cap_c:
        disk_sum = df_vdisk.groupby(vm_c)[cap_c].sum().to_dict()

    # 5. VCPU PERFORMANCE
    vcpu_m = {}
    for _, v_r in df_vcpu.iterrows():
        name = v_r.get('VM')
        vcpu_m[name] = {
            'ready': v_r.get('CPU ready %', 0),
            'stop': v_r.get('CPU co-stop', 0),
            'mhz': v_r.get('Overall', 0),
            'limit': v_r.get('Limit', 0)
        }

    # 6. HOST CAPACITY
    h_cap = {}
    for _, h_r in df_vhost.iterrows():
        h_n = h_r.get('Host')
        h_cap[h_n] = {
            'speed': h_r.get('Speed', 0),
            'cores': h_r.get('# Cores', 1)
        }

    # 7. PROCESS VMS
    processed_vms = []
    vinfo_cols = df_vinfo.columns.tolist()
    vi_net_c = next(
        (c for c in vinfo_cols if "Network" in c or "Port" in c),
        None
    )

    for _, row in df_vinfo.iterrows():
        vm_n = row.get('VM', 'Unknown')
        usage = row.get('CPU Usage %')
        p_st = row.get('Powerstate', 'poweredOn')
        o_cpu, o_ram = row.get('CPUs', 1), row.get('Memory', 1024)
        h_n = row.get('Host', 'Unknown')
        raw_vm_net = row.get(vi_net_c, None) if vi_net_c else None
        vm_net = str(raw_vm_net).strip() if raw_vm_net is not None and not pd.isna(raw_vm_net) else 'unknown'

        perf = vcpu_m.get(vm_n, {'ready': 0, 'stop': 0, 'mhz': 0, 'limit': 0})
        host = h_cap.get(h_n, {'cores': 1, 'speed': 0})

        starve = perf['ready'] > 5.0 or perf['stop'] > 3.0
        throt = perf['limit'] > 0 and perf['mhz'] >= (perf['limit'] * 0.95)

        h_matches = df_vinfo['Host'] == h_n
        t_vcpus = df_vinfo[h_matches]['CPUs'].sum()
        vp_ratio = round(t_vcpus / host['cores'], 1)

        t_gb = round(disk_sum.get(vm_n, 0) / 1024, 2)
        is_db = any(x in vm_n.upper() for x in ['SQL', 'DB', 'PROD', 'SAP'])
        s_tier = '10iops-tier' if is_db else (
            '5iops-tier' if usage and usage > 70 else '3iops-tier'
        )

        is_un_c = (usage is None or pd.isna(usage))
        stat_p = []
        if is_un_c:
            stat_p.append("Missing CPU")
        if t_gb <= 0.5:
            stat_p.append("Missing Storage")
        if starve:
            stat_p.append("High Contention")
        if throt:
            stat_p.append("CPU Throttled")
        if not is_un_c and usage < 5 and perf['mhz'] < 100:
            stat_p.append("Zombie VM")

        stat_m = " + ".join(stat_p) if stat_p else "Healthy"
        c_use = 100 if (is_un_c or starve or throt) else usage

        mapping = map_vmware_to_ibm_vpc(
            o_cpu, o_ram, c_use, target_region,
            utilization_threshold, t_gb, s_tier
        )

        baseline = map_vmware_to_ibm_vpc(
            o_cpu, o_ram, 100, target_region,
            100, t_gb, s_tier
        )
        savings = round(max(0.0, baseline['monthly'] - mapping['monthly']), 2)
        normalized_net = normalize_network_name(vm_net or 'unknown-net')
        default_subnet = f"module.networking.{normalized_net}_id"
        default_sg = (
            f"module.networking.{normalized_net}_sg_id"
            if generate_security_groups else "N/A"
        )

        processed_vms.append({
            'Exclude?': p_st == 'poweredOff',
            'VM Name': vm_n,
            'Original Specs': f"{o_cpu}v / {o_ram}M",
            'IBM Profile': mapping['profile'],
            'Override Profile': "",
            'Compute (Mo)': mapping['compute_cost'],
            'Storage (Mo)': mapping['storage_cost'],
            'Baseline Cost (Mo)': baseline['monthly'],
            'Savings (Mo)': savings,
            'Monthly Cost': mapping['monthly'],
            'Subnet': default_subnet,
            'Security Group': default_sg,
            'Override Storage Tier': "",
            'Right-Sized': "✅" if mapping['is_rightsized'] else "❌",
            'Storage Tier': s_tier,
            'Total Storage GB': t_gb,
            'Data Status': stat_m,
            'v_p_Ratio': vp_ratio,
            'Ready_Pct': perf['ready'],
            'Overall_MHz': perf['mhz'],
            'Network': vm_net
        })

    # --- 8. DASHBOARD ---
    df_f = pd.DataFrame(processed_vms)
    t_mo = df_f[~df_f['Exclude?']]['Monthly Cost'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total VMs", len(df_f))
    m2.metric("Monthly Spend", f"${t_mo:,.2f}")

    t_c_mhz = df_vcluster['TotalCpu'].sum()
    m_h_mhz = df_vhost['Speed'].max()
    t_v_mhz = df_vcpu['Overall'].sum()
    n_p_1 = (t_c_mhz - m_h_mhz) - t_v_mhz

    t_savings = df_f[~df_f['Exclude?']]['Savings (Mo)'].sum()

    m3.metric("N+1 Headroom", f"{int(n_p_1):,} MHz")
    m4.metric("Potential Savings", f"${t_savings:,.2f}")
    z_vms = len(df_f[df_f['Data Status'].str.contains("Zombie")])
    m5.metric("Zombie VMs", z_vms)

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
            # Custom CIDR inputs for each network
            st.markdown("**Custom CIDRs per Subnet**")
            custom_cidrs = {}
            for net in unique_nets:
                net_name = net.get('name', 'unknown-net')
                default_cidr = net.get('cidr', '10.0.0.0/24')
                custom_cidrs[net_name] = st.text_input(
                    f"{net_name} CIDR", 
                    default_cidr,
                    key=f"cidr_{net_name}"
                )

    # --- 9. DATA TABLE ---
    edited_df = st.data_editor(
        df_f,
        column_config=TABLE_CONFIG,
        disabled=DISABLED_COLS,
        hide_index=True,
        use_container_width=True,
        key="main_data_editor"
    )

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download Business Case (CSV)",
        data=edited_df.to_csv(index=False).encode('utf-8'),
        file_name=f"{project_name}_proposal.csv",
        mime="text/csv"
    )

    # --- 10. BUILD ACTION ---
    if st.button("Build Terraform Project"):
        with st.status("🏗️ Packaging Project...") as status:
            try:
                final_vms = [
                    v for v in edited_df.to_dict('records')
                    if not v['Exclude?']
                ]

                vsi, root_main, stor, net, root_vars, root_out, net_vars, net_out, vsi_vars, vsi_out, stor_vars, stor_out = render_terraform_templates(
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

                zip_b = io.BytesIO()
                with zipfile.ZipFile(zip_b, "a") as zf:
                    zf.writestr("main.tf", root_main)
                    zf.writestr("variables.tf", root_vars)
                    zf.writestr("outputs.tf", root_out)
                    zf.writestr("terraform.tfvars", generate_tfvars(target_region, target_zone, project_name))
                    zf.writestr("modules/networking/main.tf", net)
                    zf.writestr("modules/networking/variables.tf", net_vars)
                    zf.writestr("modules/networking/outputs.tf", net_out)
                    zf.writestr("modules/vsi/main.tf", vsi)
                    zf.writestr("modules/vsi/variables.tf", vsi_vars)
                    zf.writestr("modules/vsi/outputs.tf", vsi_out)
                    zf.writestr("modules/storage/main.tf", stor)
                    zf.writestr("modules/storage/variables.tf", stor_vars)
                    zf.writestr("modules/storage/outputs.tf", stor_out)

                st.session_state['zip_data'] = zip_b.getvalue()
                st.session_state['build_done'] = True
                status.update(label="Complete!", state="complete")
                st.snow()
            except Exception as e:
                st.error(f"Error: {e}")

    # --- 11. DOWNLOAD ---
    if st.session_state.get('build_done'):
        st.write("---")
        st.write("### 📦 Project Ready")
        st.download_button(
            label="💾 Download Terraform Bundle",
            data=st.session_state['zip_data'],
            file_name=f"{project_name}.zip",
            mime="application/zip",
            use_container_width=True
        )

    # --- 12. UI LEGENDS ---
    st.write("---")
    st.write("### 🧭 UI Legend & Logic Guide")
    l1, l2, l3 = st.columns(3)
    with l1:
        st.markdown("**Performance Logic**")
        st.write("- **Safety Match:** Disabled if Ready % > 5.")
        st.write("- **Zombie:** Usage < 5% and MHz < 100.")
    with l2:
        st.markdown("**Storage Tiering**")
        st.write("- **10 IOPS:** DB keywords (SQL, SAP, etc).")
        st.write("- **5 IOPS:** High CPU utilization.")
    with l3:
        st.markdown("**Infrastructure Resilience**")
        st.write("- **N+1 Calculation:** (Cluster MHz - Max Host) - Demand.")
