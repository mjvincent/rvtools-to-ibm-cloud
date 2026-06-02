import streamlit as st
import pandas as pd

from sizing import get_catalog_profiles
from streamlit_app.network_storage import (
    NETWORK_COLUMNS,
    STORAGE_COLUMNS,
    build_network_planning_rows,
    build_partition_planning_rows,
    render_network_planning,
    render_storage_planning,
)
from streamlit_app.overview_readiness import (
    READINESS_COLUMNS,
    active_df as _active_df,
    calculate_estate_summary,
    count_status as _count_status,
    render_assessment_quality,
    render_estate_summary,
    render_readiness_legend,
    render_readiness_triage,
)

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
    "Pricing Source", "Pricing Confidence", "Pricing Last Updated", "Pricing Status",
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
        "Pricing Status": st.column_config.TextColumn("Pricing Status"),
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

def merge_decision_edits(df_table, edited_decisions):
    merged = df_table.copy()
    if "VM Key" in df_table.columns and "VM Key" in edited_decisions.columns:
        if df_table["VM Key"].is_unique and edited_decisions["VM Key"].is_unique:
            edits = edited_decisions.set_index("VM Key")
            for column in edits.columns:
                if column in merged.columns:
                    values = merged["VM Key"].map(edits[column])
                    merged[column] = values.where(values.notna(), merged[column])
            return merged

        if len(merged) == len(edited_decisions):
            for column in edited_decisions.columns:
                if column in merged.columns:
                    merged[column] = edited_decisions[column].to_numpy()
            return merged

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


def apply_preflight_quick_fixes(df_table, quick_fixes):
    """Apply session-backed preflight quick fixes to the editable decision table."""
    if not quick_fixes:
        return df_table
    merged = df_table.copy()
    if "VM Name" not in merged.columns:
        return merged

    for vm_name, fixes in quick_fixes.items():
        mask = merged["VM Name"] == vm_name
        if not mask.any():
            continue
        for column, value in fixes.items():
            if column in merged.columns:
                merged.loc[mask, column] = value
    return merged


def _finding_record(finding):
    return finding.to_record() if hasattr(finding, "to_record") else finding


def _finding_attr(finding, key, default=""):
    if hasattr(finding, key):
        return getattr(finding, key) or default
    return finding.get(key, default) if isinstance(finding, dict) else default


def _finding_options(finding):
    options = _finding_attr(finding, "valid_options", ())
    if isinstance(options, str):
        return [value.strip() for value in options.split(",") if value.strip()]
    return list(options or [])


def _queue_quick_fix(vm_name, column, value):
    fixes = st.session_state.setdefault("preflight_quick_fixes", {})
    vm_fixes = fixes.setdefault(vm_name, {})
    vm_fixes[column] = value
    st.session_state["preflight_needs_rerun"] = True


def _render_labeled_detail(label, value):
    if not value:
        return
    value = str(value)
    if "\n" in value:
        st.markdown(f"**{label}:**\n{value}")
    else:
        st.write(f"**{label}:** {value}")


def _render_quick_fix(finding, df_table, key_prefix):
    quick_fix_type = _finding_attr(finding, "quick_fix_type")
    subject = _finding_attr(finding, "subject")
    field = _finding_attr(finding, "field")
    options = _finding_options(finding)
    recommended = _finding_attr(finding, "recommended_option")

    if quick_fix_type in {"storage_tier", "profile"} and options:
        default = recommended if recommended in options else options[0]
        selected = st.selectbox(
            "Quick fix value",
            options,
            index=options.index(default),
            key=f"{key_prefix}_value",
        )
        if st.button("Apply quick fix", key=f"{key_prefix}_apply"):
            _queue_quick_fix(subject, field, selected)
            st.success("Quick fix queued. Re-run preflight to confirm the blocker is cleared.")
        return

    if quick_fix_type == "exclude_vm" and subject:
        if st.button("Exclude VM from this package", key=f"{key_prefix}_exclude"):
            _queue_quick_fix(subject, "Exclude?", True)
            st.success("VM exclusion queued. Re-run preflight to confirm the blocker is cleared.")
        return

    if quick_fix_type == "include_vm":
        excluded = []
        if "Exclude?" in df_table.columns and "VM Name" in df_table.columns:
            excluded = sorted(
                df_table.loc[df_table["Exclude?"] == True, "VM Name"].dropna().astype(str)
            )
        if excluded:
            selected = st.selectbox(
                "VM to include",
                excluded,
                key=f"{key_prefix}_include_value",
            )
            if st.button("Include selected VM", key=f"{key_prefix}_include"):
                _queue_quick_fix(selected, "Exclude?", False)
                st.success("VM inclusion queued. Re-run preflight to confirm the blocker is cleared.")


def render_preflight_guidance(findings, df_table=None):
    summary = {
        "blocker": 0,
        "warning": 0,
        "info": 0,
    }
    for finding in findings or []:
        summary[_finding_attr(finding, "severity", "info")] = (
            summary.get(_finding_attr(finding, "severity", "info"), 0) + 1
        )

    st.write("### Package Preflight")
    c1, c2, c3 = st.columns(3)
    c1.metric("Blockers", summary.get("blocker", 0))
    c2.metric("Warnings", summary.get("warning", 0))
    c3.metric("Info", summary.get("info", 0))

    if not findings:
        st.success("No preflight blockers or warnings were detected.")
        return

    if summary.get("blocker", 0):
        st.error(
            "Terraform ZIP not generated. Fix the blockers below, then "
            "re-run preflight before building the package."
        )
    else:
        st.info(
            "Warnings are exported for review, but they do not stop Terraform "
            "package generation."
        )

    if st.session_state.get("preflight_needs_rerun"):
        st.warning("Quick fixes have been queued. Re-run preflight to refresh the blocker list.")

    blocker_findings = [
        finding for finding in findings
        if _finding_attr(finding, "severity") == "blocker"
    ]
    warning_findings = [
        finding for finding in findings
        if _finding_attr(finding, "severity") == "warning"
    ]

    for index, finding in enumerate(blocker_findings):
        category = _finding_attr(finding, "category", "preflight")
        subject = _finding_attr(finding, "subject", "package")
        title = f"{category.replace('_', ' ').title()}: {subject}"
        with st.expander(title, expanded=True):
            _render_labeled_detail(
                "What is wrong",
                _finding_attr(finding, "message"),
            )
            _render_labeled_detail(
                "Current evidence",
                _finding_attr(finding, "current_value"),
            )
            _render_labeled_detail(
                "Allowed values / constraint",
                _finding_attr(finding, "constraint"),
            )
            options = _finding_options(finding)
            if options:
                st.write(f"**Valid choices:** {', '.join(options)}")
            _render_labeled_detail(
                "Recommended",
                _finding_attr(finding, "recommended_option"),
            )
            _render_labeled_detail(
                "Where to fix",
                _finding_attr(
                    finding,
                    "fix_location",
                    "Review the relevant workbench tab",
                ),
            )
            action = _finding_attr(finding, "suggested_action") or _finding_attr(finding, "remediation")
            _render_labeled_detail("Suggested action", action)
            _render_quick_fix(finding, df_table if df_table is not None else pd.DataFrame(), f"preflight_{index}")

    if warning_findings:
        with st.expander("Warnings that will be included in the package report"):
            st.dataframe(
                pd.DataFrame([_finding_record(finding) for finding in warning_findings]),
                hide_index=True,
                use_container_width=True,
            )

    with st.expander("Full preflight report"):
        st.dataframe(
            pd.DataFrame([_finding_record(finding) for finding in findings]),
            hide_index=True,
            use_container_width=True,
        )
