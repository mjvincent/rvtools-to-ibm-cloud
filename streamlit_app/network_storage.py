import pandas as pd
import streamlit as st


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


def summarize_partition_planning(vms):
    partition_rows = build_partition_planning_rows(vms)
    high_free = [
        row for row in partition_rows
        if float(row.get("Free %") or 0) >= 50
    ]
    unmatched = [
        row for row in partition_rows
        if not row.get("Matched")
    ]
    return partition_rows, high_free, unmatched


def render_network_planning(df_f, unique_nets):
    c1, c2, c3 = st.columns(3)
    c1.metric("Discovered Networks", len(unique_nets))
    c2.metric("VMs With Multi-NIC", len(df_f[df_f["NIC Count"] > 1]))
    c3.metric(
        "Unknown Networks",
        len(
            df_f[
                df_f["Network"].astype(str).str.contains(
                    "unknown", case=False, na=False
                )
            ]
        ),
    )
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


def render_storage_planning(df_f, source_vms=None):
    partition_rows, high_free, unmatched = summarize_partition_planning(
        source_vms
    )

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
