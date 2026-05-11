import io
import zipfile
import streamlit as st
import pandas as pd
from logic_engine import (
    IBM_VPC_CATALOG,
    SNAPSHOT_BLOCK_SIZE_MIB,
    assess_image_readiness,
    make_readiness_finding,
    get_catalog_profiles,
    map_vmware_to_ibm_vpc,
    render_terraform_templates,
    generate_tfvars,
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_migration_manifest,
    generate_nic_mapping_csv,
    generate_readiness_findings_csv,
    generate_migration_runbook,
    summarize_migration_readiness,
    generate_vm_mapping_csv
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
    "Security Group": st.column_config.TextColumn("Security Group"),
    "Image Readiness": st.column_config.TextColumn("Image Readiness"),
    "Readiness Reasons": st.column_config.TextColumn("Readiness Reasons"),
    "Firmware": st.column_config.TextColumn("Firmware"),
    "Boot Disk GB": st.column_config.NumberColumn(
        "Boot Disk GB", format="%.2f"
    ),
    "Data Disk Count": st.column_config.NumberColumn("Data Disk Count"),
    "Guest Customization": st.column_config.TextColumn("Guest Customization"),
    "Migration Readiness": st.column_config.TextColumn(
        "Migration Readiness"
    ),
    "Migration Readiness Reasons": st.column_config.TextColumn(
        "Migration Readiness Reasons"
    ),
    "Snapshot Count": st.column_config.NumberColumn("Snapshot Count"),
    "Snapshot Size MiB": st.column_config.NumberColumn(
        "Snapshot Size MiB", format="%.2f"
    ),
    "VMware Tools Status": st.column_config.TextColumn(
        "VMware Tools Status"
    ),
    "Mounted Media": st.column_config.TextColumn("Mounted Media"),
    "USB Devices": st.column_config.NumberColumn("USB Devices"),
    "Health Warnings": st.column_config.NumberColumn("Health Warnings")
}

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


def get_row_identity(row, fallback):
    for col in ["VM", "VM UUID", "VM ID"]:
        value = row.get(col)
        if value is not None and not pd.isna(value):
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
    return fallback


def get_vm_display_name(row, fallback):
    for col in ["VM", "DNS Name", "VM UUID", "VM ID"]:
        value = row.get(col)
        if value is not None and not pd.isna(value):
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
    return fallback


def as_bool(value):
    if value is None or pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ["true", "yes", "1", "connected"]


def as_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_cell(value, default=""):
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return default if text.lower() == "nan" else text


def is_unhealthy_status(value):
    text = clean_cell(value).lower()
    if not text:
        return False
    healthy_tokens = ["green", "ok", "toolsok", "running", "ready"]
    if any(token in text for token in healthy_tokens):
        return False
    unhealthy_tokens = [
        "gray", "red", "yellow", "not", "old", "upgrade", "error",
        "fail", "false", "none", "unknown"
    ]
    return any(token in text for token in unhealthy_tokens)


uploaded_file = st.sidebar.file_uploader("Upload RVTools", type=["xlsx"])

if uploaded_file is not None:
    # 1. LOAD TABS
    xls = pd.ExcelFile(uploaded_file)

    def read_sheet(sheet_name):
        if sheet_name in xls.sheet_names:
            return pd.read_excel(xls, sheet_name=sheet_name)
        return pd.DataFrame()

    df_vinfo = read_sheet('vInfo')
    df_vdisk = read_sheet('vDisk')
    df_vcpu = read_sheet('vCPU')
    df_vhost = read_sheet('vHost')
    df_vcluster = read_sheet('vCluster')
    df_vnetwork = read_sheet('vNetwork')
    df_vsnapshot = read_sheet('vSnapshot')
    df_vtools = read_sheet('vTools')
    df_vcd = read_sheet('vCD')
    df_vusb = read_sheet('vUSB')
    df_vhealth = read_sheet('vHealth')

    # 2. CLEAN COLUMN NAMES
    for df in [df_vinfo, df_vdisk, df_vcpu, df_vhost,
               df_vcluster, df_vnetwork, df_vsnapshot, df_vtools,
               df_vcd, df_vusb, df_vhealth]:
        if not df.empty:
            df.columns = df.columns.str.strip()

    # 3. NETWORKING EXTRACTION
    df_vnetwork["_rvtools_vm_key"] = df_vnetwork.apply(
        lambda row: get_row_identity(row, ""),
        axis=1
    )
    nic_rows = df_vnetwork[df_vnetwork["_rvtools_vm_key"] != ""].copy()
    nic_details = {}

    sort_cols = []
    for c_name in ["Internal Sort Column", "NIC label", "Mac Address"]:
        if c_name in nic_rows.columns:
            sort_cols.append(c_name)
    nic_sort = nic_rows.sort_values(sort_cols) if sort_cols else nic_rows

    for name, rows in nic_sort.groupby("_rvtools_vm_key"):
        details = []
        for idx, nic_row in enumerate(rows.to_dict("records")):
            network = nic_row.get("Network", "")
            if pd.isna(network) or not str(network).strip():
                network = "unknown-net"
            details.append({
                "label": str(nic_row.get("NIC label", f"nic-{idx + 1}")),
                "adapter": nic_row.get("Adapter", ""),
                "network": str(network).strip(),
                "switch": nic_row.get("Switch", ""),
                "connected": nic_row.get("Connected", True),
                "starts_connected": nic_row.get("Starts Connected", ""),
                "mac_address": nic_row.get("Mac Address", ""),
                "type": nic_row.get("Type", ""),
                "ipv4": nic_row.get("IPv4 Address", ""),
                "ipv6": nic_row.get("IPv6 Address", ""),
                "planned": bool(nic_row.get("Connected", True))
            })
        nic_details[str(name)] = details

    network_sources = {}
    for details in nic_details.values():
        for nic in details:
            network_sources.setdefault(nic["network"], nic.get("ipv4", ""))

    if not network_sources:
        net_cols = [c for c in df_vinfo.columns if c.startswith("Network #")]
        for _, row in df_vinfo.iterrows():
            for col in net_cols:
                value = row.get(col)
                if value is not None and not pd.isna(value):
                    network_sources.setdefault(str(value).strip(), "")

    unique_nets = []
    for n_name, raw_ip in network_sources.items():
        raw_ip = str(raw_ip) if raw_ip is not None and not pd.isna(raw_ip) else ''

        try:
            p = raw_ip.split('.')
            if len(p) == 4:
                d_cidr = f"{p[0]}.{p[1]}.{p[2]}.0/24"
            else:
                d_cidr = f"10.0.{len(unique_nets) + 1}.0/24"
        except Exception:
            d_cidr = f"10.0.{len(unique_nets) + 1}.0/24"

        unique_nets.append({'name': n_name, 'vlan': '', 'cidr': d_cidr})

    # Update TABLE_CONFIG with dynamic Network options
    TABLE_CONFIG["Network"] = st.column_config.SelectboxColumn(
        "Network", options=[""] + [net.get('name', 'unknown-net') for net in unique_nets]
    )
    TABLE_CONFIG["Subnet"] = st.column_config.TextColumn("Subnet")
    TABLE_CONFIG["Security Group"] = st.column_config.TextColumn("Security Group")

    # 4. STORAGE SUMMARY
    cap_c = next((c for c in df_vdisk.columns if 'Capacity' in c), None)
    df_vdisk["_rvtools_vm_key"] = df_vdisk.apply(
        lambda row: get_row_identity(row, ""),
        axis=1
    )
    disk_rows = df_vdisk[df_vdisk["_rvtools_vm_key"] != ""].copy()
    disk_sum = {}
    disk_count = {}
    boot_disk_gb = {}
    disk_details = {}
    if cap_c:
        disk_sum = disk_rows.groupby("_rvtools_vm_key")[cap_c].sum().to_dict()
        disk_count = (
            disk_rows.groupby("_rvtools_vm_key")[cap_c].count().to_dict()
        )
        sort_cols = []
        for c_name in ["Unit #", "Disk Key", "Disk"]:
            if c_name in df_vdisk.columns:
                sort_cols.append(c_name)
        disk_sort = (
            disk_rows.sort_values(sort_cols) if sort_cols else disk_rows
        )
        for name, rows in disk_sort.groupby("_rvtools_vm_key"):
            details = []
            for idx, disk_row in enumerate(rows.to_dict("records")):
                capacity_gb = round(disk_row.get(cap_c, 0) / 1024, 2)
                details.append({
                    "disk": str(disk_row.get("Disk", f"disk-{idx + 1}")),
                    "disk_key": disk_row.get("Disk Key", ""),
                    "disk_path": disk_row.get("Disk Path", ""),
                    "capacity_gb": capacity_gb,
                    "capacity_mib": disk_row.get(cap_c, 0),
                    "is_boot": idx == 0,
                    "controller": disk_row.get("Controller", ""),
                    "label": disk_row.get("Label", ""),
                    "unit_number": disk_row.get("Unit #", ""),
                    "scsi_unit": disk_row.get("SCSI Unit #", ""),
                    "disk_mode": disk_row.get("Disk Mode", ""),
                    "thin": disk_row.get("Thin", ""),
                    "raw": disk_row.get("Raw", ""),
                    "shared_bus": disk_row.get("Shared Bus", "")
                })
            disk_details[str(name)] = details
            if details:
                boot_disk_gb[str(name)] = details[0]["capacity_gb"]

    # 5. VCPU PERFORMANCE
    vcpu_m = {}
    for _, v_r in df_vcpu.iterrows():
        name = get_row_identity(v_r, "")
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

    # 7. MIGRATION READINESS INPUTS
    snapshot_summary = {}
    if not df_vsnapshot.empty:
        df_vsnapshot["_rvtools_vm_key"] = df_vsnapshot.apply(
            lambda row: get_row_identity(row, ""),
            axis=1
        )
        snap_size_col = next(
            (c for c in df_vsnapshot.columns if "Size MiB (total)" in c),
            None
        )
        snap_rows = df_vsnapshot[df_vsnapshot["_rvtools_vm_key"] != ""].copy()
        for name, rows in snap_rows.groupby("_rvtools_vm_key"):
            total_size = 0.0
            if snap_size_col:
                total_size = sum(
                    as_float(v) for v in rows[snap_size_col].tolist()
                )
            snapshot_summary[str(name)] = {
                "count": len(rows),
                "size_mib": round(total_size, 2),
            }

    tools_summary = {}
    if not df_vtools.empty:
        df_vtools["_rvtools_vm_key"] = df_vtools.apply(
            lambda row: get_row_identity(row, ""),
            axis=1
        )
        for _, tool_row in df_vtools.iterrows():
            name = tool_row.get("_rvtools_vm_key", "")
            if not name:
                continue
            tools_summary[str(name)] = {
                "tools": clean_cell(tool_row.get("Tools")),
                "version": clean_cell(tool_row.get("Tools Version")),
                "upgradeable": clean_cell(tool_row.get("Upgradeable")),
                "app_status": clean_cell(tool_row.get("App status")),
                "heartbeat": clean_cell(tool_row.get("Heartbeat status")),
                "operation_ready": clean_cell(tool_row.get("Operation Ready")),
            }

    mounted_media = {}
    if not df_vcd.empty:
        df_vcd["_rvtools_vm_key"] = df_vcd.apply(
            lambda row: get_row_identity(row, ""),
            axis=1
        )
        cd_rows = df_vcd[df_vcd["_rvtools_vm_key"] != ""].copy()
        for name, rows in cd_rows.groupby("_rvtools_vm_key"):
            media = []
            for media_row in rows.to_dict("records"):
                if (
                    as_bool(media_row.get("Connected")) or
                    as_bool(media_row.get("Starts Connected"))
                ):
                    device = clean_cell(media_row.get("Device Node"), "CD/DVD")
                    media_type = clean_cell(
                        media_row.get("Device Type"), "connected media"
                    )
                    media.append(f"{device}: {media_type}")
            mounted_media[str(name)] = media

    usb_summary = {}
    if not df_vusb.empty:
        df_vusb["_rvtools_vm_key"] = df_vusb.apply(
            lambda row: get_row_identity(row, ""),
            axis=1
        )
        usb_rows = df_vusb[df_vusb["_rvtools_vm_key"] != ""].copy()
        for name, rows in usb_rows.groupby("_rvtools_vm_key"):
            devices = []
            for usb_row in rows.to_dict("records"):
                if as_bool(usb_row.get("Connected")):
                    device = clean_cell(usb_row.get("Device Node"), "USB")
                    device_type = clean_cell(
                        usb_row.get("Device Type"), "connected USB device"
                    )
                    devices.append(f"{device}: {device_type}")
            usb_summary[str(name)] = devices

    health_summary = {}
    if not df_vhealth.empty:
        for health_row in df_vhealth.to_dict("records"):
            raw_name = clean_cell(health_row.get("Name"))
            if not raw_name:
                continue
            health_summary.setdefault(raw_name, []).append({
                "message": clean_cell(health_row.get("Message")),
                "type": clean_cell(health_row.get("Message type")),
            })

    def build_migration_findings(vm_key, vm_name, power_state):
        findings = []
        snapshots = snapshot_summary.get(vm_key, {"count": 0, "size_mib": 0})
        if snapshots["count"] > 0:
            severity = (
                "Blocked"
                if snapshots["size_mib"] >= SNAPSHOT_BLOCK_SIZE_MIB
                else "Review"
            )
            findings.append(make_readiness_finding(
                "Active snapshots",
                severity,
                "vSnapshot",
                (
                    f"{snapshots['count']} snapshot(s), "
                    f"{snapshots['size_mib']} MiB total"
                ),
                "Remove or consolidate snapshots before export/replication"
            ))

        media = mounted_media.get(vm_key, [])
        if media:
            findings.append(make_readiness_finding(
                "Mounted CD/DVD media",
                "Blocked",
                "vCD",
                "; ".join(media),
                "Disconnect ISO or physical media before migration"
            ))

        usb_devices = usb_summary.get(vm_key, [])
        if usb_devices:
            findings.append(make_readiness_finding(
                "Attached USB devices",
                "Blocked",
                "vUSB",
                "; ".join(usb_devices),
                "Remove USB dependencies or replace them with cloud-native access"
            ))

        tools = tools_summary.get(vm_key, {})
        tools_parts = [
            tools.get("tools"),
            f"upgradeable={tools.get('upgradeable')}" if tools.get("upgradeable") else "",
            f"heartbeat={tools.get('heartbeat')}" if tools.get("heartbeat") else "",
            f"app={tools.get('app_status')}" if tools.get("app_status") else "",
            f"operation_ready={tools.get('operation_ready')}" if tools.get("operation_ready") else "",
        ]
        tools_status = ", ".join([part for part in tools_parts if part])
        if tools and (
            is_unhealthy_status(tools.get("tools")) or
            is_unhealthy_status(tools.get("heartbeat")) or
            is_unhealthy_status(tools.get("app_status")) or
            clean_cell(tools.get("upgradeable")).lower() == "yes" or
            clean_cell(tools.get("operation_ready")).lower() == "false"
        ):
            findings.append(make_readiness_finding(
                "VMware Tools status",
                "Review",
                "vTools",
                tools_status,
                "Update VMware Tools and verify guest heartbeat/application status"
            ))

        if clean_cell(power_state).lower() == "poweredoff":
            findings.append(make_readiness_finding(
                "Powered-off VM",
                "Review",
                "vInfo",
                "VM is powered off in the source inventory",
                "Confirm whether the VM should be migrated or excluded"
            ))

        for lookup_name in [vm_key, vm_name]:
            for health in health_summary.get(lookup_name, []):
                h_type = clean_cell(health.get("type"))
                severity = (
                    "Blocked"
                    if h_type.lower() in ["error", "critical", "red"]
                    else "Review"
                )
                findings.append(make_readiness_finding(
                    "RVTools health warning",
                    severity,
                    "vHealth",
                    f"{h_type}: {clean_cell(health.get('message'))}",
                    "Review RVTools health finding and remediate before cutover"
                ))

        return findings

    # 8. PROCESS VMS
    processed_vms = []
    vinfo_cols = df_vinfo.columns.tolist()
    vi_net_c = next(
        (c for c in vinfo_cols if "Network" in c or "Port" in c),
        None
    )

    for idx, row in df_vinfo.iterrows():
        vm_key = get_row_identity(row, f"row-{idx + 1}")
        vm_n = get_vm_display_name(row, f"Unknown-{idx + 1}")
        usage = row.get('CPU Usage %')
        p_st = row.get('Powerstate', 'poweredOn')
        o_cpu, o_ram = row.get('CPUs', 1), row.get('Memory', 1024)
        h_n = row.get('Host', 'Unknown')
        raw_vm_net = row.get(vi_net_c, None) if vi_net_c else None
        vm_net = str(raw_vm_net).strip() if raw_vm_net is not None and not pd.isna(raw_vm_net) else 'unknown'
        vm_nics = nic_details.get(vm_key, [])
        if not vm_nics:
            vm_nics = [{
                "label": "Network adapter 1",
                "adapter": "",
                "network": vm_net,
                "switch": "",
                "connected": True,
                "starts_connected": True,
                "mac_address": "",
                "type": "",
                "ipv4": row.get('Primary IP Address', ''),
                "ipv6": "",
                "planned": True
            }]
        connected_nics = [
            nic for nic in vm_nics
            if str(nic.get("connected", True)).lower() == "true"
        ]
        primary_nic = connected_nics[0] if connected_nics else vm_nics[0]
        vm_net = primary_nic.get("network", vm_net)
        primary_ip = primary_nic.get("ipv4") or row.get('Primary IP Address', '')

        perf = vcpu_m.get(vm_key, {'ready': 0, 'stop': 0, 'mhz': 0, 'limit': 0})
        host = h_cap.get(h_n, {'cores': 1, 'speed': 0})

        starve = perf['ready'] > 5.0 or perf['stop'] > 3.0
        throt = perf['limit'] > 0 and perf['mhz'] >= (perf['limit'] * 0.95)

        h_matches = df_vinfo['Host'] == h_n
        t_vcpus = df_vinfo[h_matches]['CPUs'].sum()
        vp_ratio = round(t_vcpus / host['cores'], 1)

        t_gb = round(disk_sum.get(vm_key, 0) / 1024, 2)
        b_gb = boot_disk_gb.get(vm_key)
        if b_gb is None:
            if row.get('Disks', 0) == 1 and t_gb > 0:
                b_gb = t_gb
            else:
                provisioned_mib = row.get('Provisioned MiB', 0)
                b_gb = (
                    round(provisioned_mib / 1024, 2)
                    if not pd.isna(provisioned_mib) and provisioned_mib
                    else 0
                )
        guest_os = row.get(
            'OS according to the VMware Tools',
            row.get('OS according to the configuration file', '')
        )
        firmware = row.get('Firmware', '')
        vm_disk_details = disk_details.get(vm_key, [])
        vm_disk_count = disk_count.get(vm_key, row.get('Disks', 0))
        readiness = assess_image_readiness(
            guest_os,
            firmware,
            b_gb,
            vm_disk_count,
            p_st
        )
        vm_findings = build_migration_findings(vm_key, vm_n, p_st)
        migration_readiness = summarize_migration_readiness(vm_findings)
        vm_snapshots = snapshot_summary.get(
            vm_key, {"count": 0, "size_mib": 0}
        )
        vm_tools = tools_summary.get(vm_key, {})
        vm_tools_status = ", ".join([
            part for part in [
                vm_tools.get("tools"),
                f"upgradeable={vm_tools.get('upgradeable')}"
                if vm_tools.get("upgradeable") else "",
                f"heartbeat={vm_tools.get('heartbeat')}"
                if vm_tools.get("heartbeat") else "",
                f"app={vm_tools.get('app_status')}"
                if vm_tools.get("app_status") else "",
            ]
            if part
        ])
        vm_media = mounted_media.get(vm_key, [])
        vm_usb = usb_summary.get(vm_key, [])
        vm_health_count = len(health_summary.get(vm_key, [])) + len(
            health_summary.get(vm_n, [])
        )
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
            'VM Key': vm_key,
            'VM Name': vm_n,
            'Power State': p_st,
            'Source IP': primary_ip,
            'NIC Count': len(vm_nics),
            'Primary Network': vm_net,
            'Primary IP': primary_ip,
            'Network Details': vm_nics,
            'Guest OS': guest_os,
            'Disk Count': vm_disk_count,
            'Data Disk Count': max(0, len(vm_disk_details) - 1),
            'Disk Details': vm_disk_details,
            'Firmware': readiness['firmware'],
            'Boot Disk GB': readiness['boot_disk_gb'],
            'Guest Customization': readiness['guest_customization'],
            'Image Readiness': readiness['status'],
            'Readiness Reasons': readiness['reasons'],
            'Migration Readiness': migration_readiness['status'],
            'Migration Readiness Reasons': migration_readiness['reasons'],
            'Readiness Findings': vm_findings,
            'Snapshot Count': vm_snapshots['count'],
            'Snapshot Size MiB': vm_snapshots['size_mib'],
            'VMware Tools Status': vm_tools_status,
            'Mounted Media': "; ".join(vm_media),
            'USB Devices': len(vm_usb),
            'Health Warnings': vm_health_count,
            'Host': h_n,
            'Cluster': row.get('Cluster', ''),
            'Datacenter': row.get('Datacenter', ''),
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
    df_table = df_f.drop(
        columns=["Disk Details", "Network Details", "Readiness Findings"],
        errors="ignore"
    )
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

    r1, r2, r3 = st.columns(3)
    active_df = df_f[~df_f['Exclude?']]
    r1.metric(
        "Image Ready",
        len(active_df[active_df['Image Readiness'] == "Ready"])
    )
    r2.metric(
        "Image Review",
        len(active_df[active_df['Image Readiness'] == "Review"])
    )
    r3.metric(
        "Image Blocked",
        len(active_df[active_df['Image Readiness'] == "Blocked"])
    )

    mr1, mr2, mr3 = st.columns(3)
    mr1.metric(
        "Migration Ready",
        len(active_df[active_df['Migration Readiness'] == "Ready"])
    )
    mr2.metric(
        "Migration Review",
        len(active_df[active_df['Migration Readiness'] == "Review"])
    )
    mr3.metric(
        "Migration Blocked",
        len(active_df[active_df['Migration Readiness'] == "Blocked"])
    )

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
            for idx, net in enumerate(unique_nets):
                net_name = net.get('name', 'unknown-net')
                default_cidr = net.get('cidr', '10.0.0.0/24')
                sanitized_name = normalize_network_name(net_name)
                net_key = f"{sanitized_name}_{idx}"
                net['cidr_key'] = net_key
                custom_cidrs[net_key] = st.text_input(
                    f"{net_name} CIDR",
                    default_cidr,
                    key=f"cidr_{net_key}"
                )

    # --- 9. DATA TABLE ---
    edited_df = st.data_editor(
        df_table,
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
                for vm in final_vms:
                    vm["Disk Details"] = disk_details.get(vm.get("VM Key"), [])
                    vm["Network Details"] = nic_details.get(
                        vm.get("VM Key"), []
                    )
                    vm["Readiness Findings"] = next(
                        (
                            source.get("Readiness Findings", [])
                            for source in processed_vms
                            if source.get("VM Key") == vm.get("VM Key")
                        ),
                        []
                    )

                terraform_files = render_terraform_templates(
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
                (
                    vsi, root_main, stor, net, root_vars, root_out,
                    net_vars, net_out, vsi_vars, vsi_out, stor_vars,
                    stor_out
                ) = terraform_files

                migration_context = {
                    'project_name': project_name,
                    'target_region': target_region,
                    'target_zone': target_zone,
                    'vpc_name': vpc_name,
                    'address_prefix_strategy': address_prefix_strategy,
                    'deployment_target': deployment_target,
                    'generate_security_groups': generate_security_groups
                }

                zip_b = io.BytesIO()
                with zipfile.ZipFile(zip_b, "a") as zf:
                    zf.writestr("main.tf", root_main)
                    zf.writestr("variables.tf", root_vars)
                    zf.writestr("outputs.tf", root_out)
                    zf.writestr(
                        "terraform.tfvars",
                        generate_tfvars(
                            target_region, target_zone, project_name
                        )
                    )
                    zf.writestr("modules/networking/main.tf", net)
                    zf.writestr("modules/networking/variables.tf", net_vars)
                    zf.writestr("modules/networking/outputs.tf", net_out)
                    zf.writestr("modules/vsi/main.tf", vsi)
                    zf.writestr("modules/vsi/variables.tf", vsi_vars)
                    zf.writestr("modules/vsi/outputs.tf", vsi_out)
                    zf.writestr("modules/storage/main.tf", stor)
                    zf.writestr("modules/storage/variables.tf", stor_vars)
                    zf.writestr("modules/storage/outputs.tf", stor_out)
                    zf.writestr(
                        "migration-manifest.json",
                        generate_migration_manifest(final_vms, migration_context)
                    )
                    zf.writestr(
                        "vm-mapping.csv",
                        generate_vm_mapping_csv(final_vms)
                    )
                    zf.writestr(
                        "disk-mapping.csv",
                        generate_disk_mapping_csv(final_vms)
                    )
                    zf.writestr(
                        "nic-mapping.csv",
                        generate_nic_mapping_csv(
                            final_vms, generate_security_groups
                        )
                    )
                    zf.writestr(
                        "readiness-findings.csv",
                        generate_readiness_findings_csv(final_vms)
                    )
                    zf.writestr(
                        "image-import-variables.tfvars.example",
                        generate_image_import_tfvars(final_vms)
                    )
                    zf.writestr(
                        "migration-runbook.md",
                        generate_migration_runbook(migration_context)
                    )

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
    st.markdown("**Image Readiness**")
    st.write("- **Ready:** No metadata blockers found for image planning.")
    st.write("- **Review:** Metadata or multi-disk items need validation.")
    st.write("- **Blocked:** Boot image exceeds IBM Cloud custom image limits.")
    st.markdown("**Migration Readiness**")
    st.write("- **Ready:** No migration blockers found in optional RVTools tabs.")
    st.write("- **Review:** Snapshots, tools, power state, or health items need owner validation.")
    st.write("- **Blocked:** Large snapshots, mounted media, USB devices, or severe health items should be remediated before migration.")
