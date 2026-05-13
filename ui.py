import streamlit as st
import pandas as pd

from sizing import get_catalog_profiles

STORAGE_TIERS = ["3iops-tier", "5iops-tier", "10iops-tier"]

DISABLED_COLS = [
    "VM Name", "Original Specs", "Data Status",
    "Total Storage GB", "Monthly Cost", "Right-Sized", "v_p_Ratio",
    "Ready_Pct", "Overall_MHz", "Power State", "Source IP",
    "Guest OS", "Disk Count", "Host", "Cluster", "Datacenter",
    "VM Key", "Data Disk Count", "NIC Count", "Primary Network",
    "Primary IP",
    "Partition Count", "Unmatched Partition Count",
    "Image Readiness", "Readiness Reasons", "Firmware", "Boot Disk GB",
    "Guest Customization",
    "Migration Readiness", "Migration Readiness Reasons",
    "Snapshot Count", "Snapshot Size MiB", "VMware Tools Status",
    "Mounted Media", "USB Devices", "Health Warnings",
    "Memory Readiness", "Memory Readiness Reasons",
    "Network Readiness", "Network Readiness Reasons",
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
        "Network Readiness": st.column_config.TextColumn("Network Readiness"),
        "Network Readiness Reasons": st.column_config.TextColumn("Network Readiness Reasons"),
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
        ("Network", "Network Readiness"),
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
    st.markdown("**Network Readiness**")
    st.write("- **Ready:** Connected NICs have usable network metadata and matched switch/port evidence when available.")
    st.write("- **Review:** Missing, ambiguous, disconnected, or incomplete switch/port context needs validation.")
    st.write("- **Blocked:** Explicit unusable port or switch-capacity evidence should be remediated before migration.")


DECISION_COLUMNS = [
    "Exclude?", "VM Name", "Power State", "Data Status",
    "Image Readiness", "Migration Readiness", "Memory Readiness",
    "Network Readiness",
    "IBM Profile", "Override Profile", "Storage Tier",
    "Override Storage Tier", "Network", "Subnet", "Security Group",
    "Monthly Cost", "Savings (Mo)"
]

READINESS_COLUMNS = [
    "VM Name", "Power State", "Image Readiness", "Readiness Reasons",
    "Migration Readiness", "Migration Readiness Reasons",
    "Memory Readiness", "Memory Readiness Reasons",
    "Network Readiness", "Network Readiness Reasons", "Data Status"
]

NETWORK_COLUMNS = [
    "VM Name", "NIC Count", "Primary Network", "Primary IP", "Network",
    "Network Readiness", "Network Readiness Reasons", "Subnet",
    "Security Group"
]

STORAGE_COLUMNS = [
    "VM Name", "Disk Count", "Data Disk Count", "Total Storage GB",
    "Storage Tier", "Override Storage Tier", "Image Readiness",
    "Boot Disk GB", "Partition Count", "Unmatched Partition Count"
]


def _active_df(df_f):
    return df_f[~df_f['Exclude?']]


def _count_status(df, column, status):
    return len(df[df[column] == status])


def render_estate_summary(df_f):
    active_df = _active_df(df_f)
    excluded = len(df_f) - len(active_df)
    monthly = active_df['Monthly Cost'].sum()
    savings = active_df['Savings (Mo)'].sum()
    blocked = sum(
        _count_status(active_df, column, "Blocked")
        for column in [
            "Image Readiness", "Migration Readiness", "Memory Readiness",
            "Network Readiness"
        ]
    )
    review = sum(
        _count_status(active_df, column, "Review")
        for column in [
            "Image Readiness", "Migration Readiness", "Memory Readiness",
            "Network Readiness"
        ]
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("In Scope", len(active_df))
    c2.metric("Excluded", excluded)
    c3.metric("Monthly Estimate", f"${monthly:,.2f}")
    c4.metric("Potential Savings", f"${savings:,.2f}")
    c5.metric("Readiness Blockers", blocked)

    if blocked:
        st.warning(
            f"{blocked} blocker signal(s) need remediation before export, "
            "replication, image import, or cutover planning."
        )
    elif review:
        st.info(
            f"{review} review signal(s) should be validated with workload "
            "owners before migration waves are finalized."
        )
    else:
        st.success("No readiness blockers or review signals were detected for in-scope VMs.")


def render_assessment_quality(report):
    summary = (report or {}).get("summary", {})
    tabs = (report or {}).get("tabs", [])
    required_present = summary.get("required_tabs_present", 0)
    required_total = summary.get("required_tabs_total", 0)
    optional_present = summary.get("optional_readiness_tabs_present", 0)
    optional_total = summary.get("optional_readiness_tabs_total", 0)
    optional_network_present = summary.get(
        "optional_network_detail_tabs_present", 0
    )
    optional_network_total = summary.get("optional_network_detail_tabs_total", 0)

    st.subheader("Assessment Quality")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall Confidence", summary.get("overall_confidence", "Low"))
    c2.metric("Required Tabs", f"{required_present}/{required_total}")
    c3.metric("Optional Readiness Tabs", f"{optional_present}/{optional_total}")
    c4.metric(
        "Network Detail Tabs",
        f"{optional_network_present}/{optional_network_total}"
    )
    c5.metric("Missing or Empty Tabs", summary.get("missing_or_empty_tabs", 0))

    confidence = summary.get("overall_confidence", "Low")
    if confidence == "High":
        st.success("RVTools coverage supports high-confidence planning signals.")
    elif confidence == "Medium":
        st.info("RVTools coverage is usable, with some fallback or partial confidence signals.")
    else:
        st.warning("RVTools coverage is limited. Review missing or empty tabs before relying on planning outputs.")

    with st.expander("Worksheet coverage details"):
        if tabs:
            st.dataframe(
                pd.DataFrame(tabs),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.write("No worksheet quality data is available.")


def render_readiness_triage(df_f):
    active_df = _active_df(df_f)
    st.caption("Blocked and Review items are shown first so planning effort starts where it matters most.")
    for label, column, reason_column in [
        ("Image", "Image Readiness", "Readiness Reasons"),
        ("Migration", "Migration Readiness", "Migration Readiness Reasons"),
        ("Memory", "Memory Readiness", "Memory Readiness Reasons"),
        ("Network", "Network Readiness", "Network Readiness Reasons"),
    ]:
        st.subheader(f"{label} Readiness")
        c1, c2, c3 = st.columns(3)
        c1.metric("Blocked", _count_status(active_df, column, "Blocked"))
        c2.metric("Review", _count_status(active_df, column, "Review"))
        c3.metric("Ready", _count_status(active_df, column, "Ready"))
        ordered = active_df.copy()
        ordered["_status_order"] = ordered[column].map({
            "Blocked": 0,
            "Review": 1,
            "Ready": 2,
        }).fillna(3)
        view = ordered.sort_values(["_status_order", "VM Name"])[
            ["VM Name", column, reason_column, "Power State", "Data Status"]
        ]
        st.dataframe(view, hide_index=True, use_container_width=True)


def render_network_planning(df_f, unique_nets):
    c1, c2, c3 = st.columns(3)
    c1.metric("Discovered Networks", len(unique_nets))
    c2.metric("VMs With Multi-NIC", len(df_f[df_f["NIC Count"] > 1]))
    c3.metric("Unknown Networks", len(df_f[df_f["Network"].astype(str).str.contains("unknown", case=False, na=False)]))
    st.subheader("Subnet Defaults")
    st.dataframe(unique_nets, hide_index=True, use_container_width=True)
    st.subheader("VM Network Placement")
    st.dataframe(
        df_f[[col for col in NETWORK_COLUMNS if col in df_f.columns]],
        hide_index=True,
        use_container_width=True,
    )
    network_rows = build_network_planning_rows(df_f)
    if network_rows:
        st.subheader("NIC Source Switch/Port Context")
        st.dataframe(
            pd.DataFrame(network_rows),
            hide_index=True,
            use_container_width=True,
        )


def _record(value):
    return value.to_record() if hasattr(value, "to_record") else value


def build_network_planning_rows(vms):
    rows = []
    records = vms.to_dict("records") if hasattr(vms, "to_dict") else (vms or [])
    for vm in records:
        record = _record(vm)
        for nic in record.get("Network Details", []) or []:
            rows.append({
                "VM Name": record.get("VM Name", ""),
                "NIC Label": nic.get("label", ""),
                "Connected": nic.get("connected", True),
                "Planned": nic.get("planned", True),
                "Source Network": nic.get("network", ""),
                "Switch": nic.get("switch", ""),
                "Switch Type": nic.get("switch_type", ""),
                "Port Group": nic.get("port_group", ""),
                "VLAN / Segment": nic.get("vlan", ""),
                "Port Key": nic.get("port_key", ""),
                "Port Status": nic.get("port_status", ""),
                "Backing Source Tab": nic.get("backing_source_tab", ""),
                "Match Confidence": nic.get("match_confidence", ""),
                "Network Readiness": record.get("Network Readiness", ""),
            })
    return rows


def build_partition_planning_rows(vms):
    rows = []
    for vm in vms or []:
        record = _record(vm)
        vm_name = record.get("VM Name", "")
        for disk in record.get("Disk Details", []) or []:
            disk_name = disk.get("disk", "")
            disk_key = disk.get("disk_key", "")
            for partition in disk.get("partitions", []) or []:
                rows.append({
                    "VM Name": vm_name,
                    "Disk": disk_name,
                    "Disk Key": disk_key or partition.get("disk_key", ""),
                    "Matched": True,
                    "Partition": partition.get("disk", ""),
                    "Capacity MiB": partition.get("capacity_mib", 0),
                    "Consumed MiB": partition.get("consumed_mib", 0),
                    "Free MiB": partition.get("free_mib", 0),
                    "Free %": partition.get("free_pct", 0),
                })
        for partition in record.get("Partition Details", []) or []:
            rows.append({
                "VM Name": vm_name,
                "Disk": "",
                "Disk Key": partition.get("disk_key", ""),
                "Matched": False,
                "Partition": partition.get("disk", ""),
                "Capacity MiB": partition.get("capacity_mib", 0),
                "Consumed MiB": partition.get("consumed_mib", 0),
                "Free MiB": partition.get("free_mib", 0),
                "Free %": partition.get("free_pct", 0),
            })
    return rows


def render_storage_planning(df_f, source_vms=None):
    partition_rows = build_partition_planning_rows(source_vms)
    high_free = [
        row for row in partition_rows
        if float(row.get("Free %") or 0) >= 50
    ]
    unmatched = [
        row for row in partition_rows
        if not row.get("Matched")
    ]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Storage GB", f"{df_f['Total Storage GB'].sum():,.2f}")
    c2.metric("Data Disks", int(df_f["Data Disk Count"].sum()))
    c3.metric("Partitions", len(partition_rows))
    c4.metric("Unmatched Partitions", len(unmatched))
    c5.metric("High Free Partitions", len(high_free))
    st.dataframe(
        df_f[[col for col in STORAGE_COLUMNS if col in df_f.columns]],
        hide_index=True,
        use_container_width=True,
    )
    if partition_rows:
        st.subheader("Partition Details")
        st.dataframe(
            pd.DataFrame(partition_rows),
            hide_index=True,
            use_container_width=True,
        )


def merge_decision_edits(df_table, edited_decisions):
    merged = df_table.copy()
    if "VM Key" in df_table.columns and "VM Key" in edited_decisions.columns:
        merged = merged.set_index("VM Key")
        edits = edited_decisions.set_index("VM Key")
        for column in edits.columns:
            if column in merged.columns:
                merged.loc[edits.index, column] = edits[column]
        return merged.reset_index()

    for column in edited_decisions.columns:
        if column in merged.columns:
            merged[column] = edited_decisions[column]
    return merged


def render_readiness_legend():
    st.caption("Ready means no detected issue in available data. Review means owner validation is needed. Blocked means remediation should happen before migration execution.")
