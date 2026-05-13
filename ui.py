import streamlit as st

from sizing import get_catalog_profiles

STORAGE_TIERS = ["3iops-tier", "5iops-tier", "10iops-tier"]

DISABLED_COLS = [
    "VM Name", "Original Specs", "Data Status",
    "Total Storage GB", "Monthly Cost", "Right-Sized", "v_p_Ratio",
    "Ready_Pct", "Overall_MHz", "Power State", "Source IP",
    "Guest OS", "Disk Count", "Host", "Cluster", "Datacenter",
    "VM Key", "Data Disk Count", "NIC Count", "Primary Network",
    "Primary IP",
    "Image Readiness", "Readiness Reasons", "Firmware", "Boot Disk GB",
    "Guest Customization",
    "Migration Readiness", "Migration Readiness Reasons",
    "Snapshot Count", "Snapshot Size MiB", "VMware Tools Status",
    "Mounted Media", "USB Devices", "Health Warnings",
    "Memory Readiness", "Memory Readiness Reasons",
    "Configured Memory MiB", "Active Memory MiB", "Consumed Memory MiB",
    "Ballooned Memory MiB", "Swapped Memory MiB",
    "Memory Reservation MiB", "Memory Limit MiB", "Memory Hot Add",
    "Sizing Memory MiB", "Memory Sizing Basis",
    "Pricing Source", "Pricing Confidence", "Pricing Last Updated",
    "Profile Hourly",
    "Baseline Cost (Mo)", "Savings (Mo)"
]


def build_table_config(unique_nets=None, catalog_profiles=None):
    profile_options = [""] + get_catalog_profiles(catalog_profiles)
    network_options = [""] + [
        net.get('name', 'unknown-net') for net in (unique_nets or [])
    ]
    return {
        "Exclude?": st.column_config.CheckboxColumn("Exclude?"),
        "Compute (Mo)": st.column_config.NumberColumn("Compute (Mo)", format="$%.2f"),
        "Storage (Mo)": st.column_config.NumberColumn("Storage (Mo)", format="$%.2f"),
        "Baseline Cost (Mo)": st.column_config.NumberColumn("Baseline Cost (Mo)", format="$%.2f"),
        "Savings (Mo)": st.column_config.NumberColumn("Savings (Mo)", format="$%.2f"),
        "Total Monthly": st.column_config.NumberColumn("Total Monthly", format="$%.2f"),
        "Storage Tier": st.column_config.SelectboxColumn("Tier", options=STORAGE_TIERS),
        "Override Storage Tier": st.column_config.SelectboxColumn("Override Storage Tier", options=[""] + STORAGE_TIERS),
        "IBM Profile": st.column_config.SelectboxColumn("Profile", options=profile_options),
        "Override Profile": st.column_config.SelectboxColumn("Override Profile", options=profile_options),
        "Subnet": st.column_config.TextColumn("Subnet"),
        "Security Group": st.column_config.TextColumn("Security Group"),
        "Network": st.column_config.SelectboxColumn("Network", options=network_options),
        "Image Readiness": st.column_config.TextColumn("Image Readiness"),
        "Readiness Reasons": st.column_config.TextColumn("Readiness Reasons"),
        "Firmware": st.column_config.TextColumn("Firmware"),
        "Boot Disk GB": st.column_config.NumberColumn("Boot Disk GB", format="%.2f"),
        "Data Disk Count": st.column_config.NumberColumn("Data Disk Count"),
        "Guest Customization": st.column_config.TextColumn("Guest Customization"),
        "Migration Readiness": st.column_config.TextColumn("Migration Readiness"),
        "Migration Readiness Reasons": st.column_config.TextColumn("Migration Readiness Reasons"),
        "Snapshot Count": st.column_config.NumberColumn("Snapshot Count"),
        "Snapshot Size MiB": st.column_config.NumberColumn("Snapshot Size MiB", format="%.2f"),
        "VMware Tools Status": st.column_config.TextColumn("VMware Tools Status"),
        "Mounted Media": st.column_config.TextColumn("Mounted Media"),
        "USB Devices": st.column_config.NumberColumn("USB Devices"),
        "Health Warnings": st.column_config.NumberColumn("Health Warnings"),
        "Memory Readiness": st.column_config.TextColumn("Memory Readiness"),
        "Memory Readiness Reasons": st.column_config.TextColumn("Memory Readiness Reasons"),
        "Configured Memory MiB": st.column_config.NumberColumn("Configured Memory MiB"),
        "Active Memory MiB": st.column_config.NumberColumn("Active Memory MiB"),
        "Consumed Memory MiB": st.column_config.NumberColumn("Consumed Memory MiB"),
        "Ballooned Memory MiB": st.column_config.NumberColumn("Ballooned Memory MiB"),
        "Swapped Memory MiB": st.column_config.NumberColumn("Swapped Memory MiB"),
        "Memory Reservation MiB": st.column_config.NumberColumn("Memory Reservation MiB"),
        "Memory Limit MiB": st.column_config.NumberColumn("Memory Limit MiB"),
        "Memory Hot Add": st.column_config.TextColumn("Memory Hot Add"),
        "Sizing Memory MiB": st.column_config.NumberColumn("Sizing Memory MiB"),
        "Memory Sizing Basis": st.column_config.TextColumn("Memory Sizing Basis"),
        "Pricing Source": st.column_config.TextColumn("Pricing Source"),
        "Pricing Confidence": st.column_config.TextColumn("Pricing Confidence"),
        "Pricing Last Updated": st.column_config.TextColumn("Pricing Last Updated"),
        "Profile Hourly": st.column_config.NumberColumn("Profile Hourly", format="$%.4f"),
    }


def render_dashboard(df_f, df_vcluster, df_vhost, df_vcpu):
    t_mo = df_f[~df_f['Exclude?']]['Monthly Cost'].sum()
    t_savings = df_f[~df_f['Exclude?']]['Savings (Mo)'].sum()
    t_c_mhz = df_vcluster['TotalCpu'].sum()
    m_h_mhz = df_vhost['Speed'].max()
    t_v_mhz = df_vcpu['Overall'].sum()
    n_p_1 = (t_c_mhz - m_h_mhz) - t_v_mhz
    z_vms = len(df_f[df_f['Data Status'].str.contains("Zombie")])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total VMs", len(df_f))
    m2.metric("Monthly Spend", f"${t_mo:,.2f}")
    m3.metric("N+1 Headroom", f"{int(n_p_1):,} MHz")
    m4.metric("Potential Savings", f"${t_savings:,.2f}")
    m5.metric("Zombie VMs", z_vms)

    active_df = df_f[~df_f['Exclude?']]
    for prefix, column in [
        ("Image", "Image Readiness"),
        ("Migration", "Migration Readiness"),
        ("Memory", "Memory Readiness"),
    ]:
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{prefix} Ready", len(active_df[active_df[column] == "Ready"]))
        c2.metric(f"{prefix} Review", len(active_df[active_df[column] == "Review"]))
        c3.metric(f"{prefix} Blocked", len(active_df[active_df[column] == "Blocked"]))


def render_legend():
    st.write("---")
    st.write("### UI Legend & Logic Guide")
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
    st.markdown("**Image Readiness**")
    st.write("- **Ready:** No metadata blockers found for image planning.")
    st.write("- **Review:** Metadata or multi-disk items need validation.")
    st.write("- **Blocked:** Boot image exceeds IBM Cloud custom image limits.")
    st.markdown("**Migration Readiness**")
    st.write("- **Ready:** No migration blockers found in optional RVTools tabs.")
    st.write("- **Review:** Snapshots, tools, power state, or health items need owner validation.")
    st.write("- **Blocked:** Large snapshots, mounted media, USB devices, or severe health items should be remediated before migration.")
    st.markdown("**Memory Readiness**")
    st.write("- **Ready:** No memory pressure or constraints detected.")
    st.write("- **Review:** Reservations, hot-add, light pressure, or sizing reductions need validation.")
    st.write("- **Blocked:** Severe swapping/ballooning or memory limits should be remediated before resizing.")
