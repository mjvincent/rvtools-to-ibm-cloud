from dataclasses import dataclass

import pandas as pd

from assessment_quality import build_assessment_quality_report
from assessments import (
    SNAPSHOT_BLOCK_SIZE_MIB,
    assess_image_readiness,
    assess_memory_readiness,
    assess_network_readiness,
    make_readiness_finding,
    summarize_migration_readiness,
)
from models import MigrationVm
from sizing import map_vmware_to_ibm_vpc, recommend_storage_tier

from .base import (
    as_bool,
    as_float,
    clean_cell,
    clean_disk_key,
    first_present,
    get_row_identity,
    get_vm_display_name,
    is_unhealthy_status,
    normalize_match_key,
    normalize_network_name,
    row_matches_any,
)
from .network_context import (
    build_port_contexts,
    build_switch_contexts,
    enrich_nic_with_network_context,
)


@dataclass
class ParsedRvtoolsWorkbook:
    processed_vms: list
    unique_nets: list
    disk_details: dict
    nic_details: dict
    assessment_quality: dict
    df_vcluster: object
    df_vhost: object
    df_vcpu: object


def parse_rvtools_workbook(
    uploaded_file,
    target_region,
    utilization_threshold,
    generate_security_groups,
    catalog_profiles=None,
    storage_tier_rates=None,
    pricing_metadata=None,
):
    """Parse RVTools workbook sheets into normalized migration VM records."""
    catalog_profiles = catalog_profiles or []
    pricing_metadata = pricing_metadata or {}

    # 1. LOAD TABS
    xls = pd.ExcelFile(uploaded_file)

    def read_sheet(sheet_name):
        if sheet_name in xls.sheet_names:
            return pd.read_excel(xls, sheet_name=sheet_name)
        return pd.DataFrame()

    df_vinfo = read_sheet('vInfo')
    df_vdisk = read_sheet('vDisk')
    df_vcpu = read_sheet('vCPU')
    df_vmemory = read_sheet('vMemory')
    df_vhost = read_sheet('vHost')
    df_vcluster = read_sheet('vCluster')
    df_vnetwork = read_sheet('vNetwork')
    df_vsnapshot = read_sheet('vSnapshot')
    df_vtools = read_sheet('vTools')
    df_vcd = read_sheet('vCD')
    df_vusb = read_sheet('vUSB')
    df_vhealth = read_sheet('vHealth')
    df_vpartition = read_sheet('vPartition')
    df_vport = read_sheet('vPort')
    df_dvport = read_sheet('dvPort')
    df_vswitch = read_sheet('vSwitch')
    df_dvswitch = read_sheet('dvSwitch')

    # 2. CLEAN COLUMN NAMES
    for df in [df_vinfo, df_vdisk, df_vcpu, df_vhost,
               df_vmemory, df_vcluster, df_vnetwork, df_vsnapshot, df_vtools,
               df_vcd, df_vusb, df_vhealth, df_vpartition, df_vport,
               df_dvport, df_vswitch, df_dvswitch]:
        if not df.empty:
            df.columns = df.columns.str.strip()

    workbook_sheets = {
        "vInfo": df_vinfo,
        "vDisk": df_vdisk,
        "vCPU": df_vcpu,
        "vMemory": df_vmemory,
        "vHost": df_vhost,
        "vCluster": df_vcluster,
        "vNetwork": df_vnetwork,
        "vSnapshot": df_vsnapshot,
        "vTools": df_vtools,
        "vCD": df_vcd,
        "vUSB": df_vusb,
        "vHealth": df_vhealth,
        "vPartition": df_vpartition,
        "vPort": df_vport,
        "dvPort": df_dvport,
        "vSwitch": df_vswitch,
        "dvSwitch": df_dvswitch,
    }
    assessment_quality = build_assessment_quality_report(
        workbook_sheets,
        xls.sheet_names
    )

    # 3. NETWORKING EXTRACTION
    switch_contexts = {}
    switch_contexts.update(
        build_switch_contexts(df_vswitch, "standard", "vSwitch")
    )
    switch_contexts.update(
        build_switch_contexts(df_dvswitch, "distributed", "dvSwitch")
    )
    port_contexts = (
        build_port_contexts(df_vport, "vPort", switch_contexts) +
        build_port_contexts(df_dvport, "dvPort", switch_contexts)
    )
    network_detail_available = bool(port_contexts or switch_contexts)

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
            nic_detail = {
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
                "planned": as_bool(nic_row.get("Connected", True))
            }
            details.append(enrich_nic_with_network_context(
                nic_detail, str(name), "", port_contexts
            ))
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

    # 4. STORAGE SUMMARY
    partitions_by_vm = {}
    if not df_vpartition.empty:
        df_vpartition["_rvtools_vm_key"] = df_vpartition.apply(
            lambda row: get_row_identity(row, ""),
            axis=1
        )
        partition_rows = df_vpartition[
            df_vpartition["_rvtools_vm_key"] != ""
        ].copy()
        for name, rows in partition_rows.groupby("_rvtools_vm_key"):
            partitions = []
            for partition_row in rows.to_dict("records"):
                partitions.append({
                    "disk": clean_cell(partition_row.get("Disk")),
                    "disk_key": clean_disk_key(partition_row.get("Disk Key")),
                    "capacity_mib": as_float(
                        partition_row.get("Capacity MiB")
                    ),
                    "consumed_mib": as_float(
                        partition_row.get("Consumed MiB")
                    ),
                    "free_mib": as_float(partition_row.get("Free MiB")),
                    "free_pct": as_float(partition_row.get("Free % ")),
                    "matched": False,
                })
            partitions_by_vm[str(name)] = partitions

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
    unmatched_partition_details = {}
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
            vm_partitions = partitions_by_vm.get(str(name), [])
            matched_partition_indexes = set()
            for idx, disk_row in enumerate(rows.to_dict("records")):
                capacity_gb = round(disk_row.get(cap_c, 0) / 1024, 2)
                disk_key = clean_disk_key(disk_row.get("Disk Key", ""))
                disk_partitions = []
                if disk_key:
                    for p_idx, partition in enumerate(vm_partitions):
                        if clean_cell(partition.get("disk_key")) == disk_key:
                            matched = partition.copy()
                            matched["matched"] = True
                            disk_partitions.append(matched)
                            matched_partition_indexes.add(p_idx)
                details.append({
                    "disk": str(disk_row.get("Disk", f"disk-{idx + 1}")),
                    "disk_key": disk_key,
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
                    "shared_bus": disk_row.get("Shared Bus", ""),
                    "partitions": disk_partitions,
                })
            unmatched = [
                partition
                for p_idx, partition in enumerate(vm_partitions)
                if p_idx not in matched_partition_indexes
            ]
            if len(details) == 1 and unmatched:
                details[0]["partitions"].extend([
                    {**partition, "matched": True}
                    for partition in unmatched
                ])
                unmatched = []
            disk_details[str(name)] = details
            unmatched_partition_details[str(name)] = unmatched
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

    # 6. VMEMORY PERFORMANCE
    memory_summary = {}
    if not df_vmemory.empty:
        df_vmemory["_rvtools_vm_key"] = df_vmemory.apply(
            lambda row: get_row_identity(row, ""),
            axis=1
        )
        for _, mem_row in df_vmemory.iterrows():
            name = mem_row.get("_rvtools_vm_key", "")
            if not name:
                continue
            memory_summary[str(name)] = {
                "configured_mib": as_float(mem_row.get("Size MiB")),
                "active_mib": as_float(mem_row.get("Active")),
                "consumed_mib": as_float(mem_row.get("Consumed")),
                "ballooned_mib": as_float(mem_row.get("Ballooned")),
                "swapped_mib": as_float(mem_row.get("Swapped")),
                "reservation_mib": as_float(mem_row.get("Reservation")),
                "limit_mib": as_float(mem_row.get("Limit"), -1),
                "hot_add": clean_cell(mem_row.get("Hot Add")),
            }

    # 7. HOST CAPACITY
    h_cap = {}
    for _, h_r in df_vhost.iterrows():
        h_n = h_r.get('Host')
        h_cap[h_n] = {
            'speed': h_r.get('Speed', 0),
            'cores': h_r.get('# Cores', 1)
        }

    # 8. MIGRATION READINESS INPUTS
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

    # 9. PROCESS VMS
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
                "planned": True,
            }]
            vm_nics = [
                enrich_nic_with_network_context(
                    nic, vm_key, vm_n, port_contexts
                )
                for nic in vm_nics
            ]
        connected_nics = [
            nic for nic in vm_nics
            if as_bool(nic.get("connected", True))
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
        vm_unmatched_partitions = unmatched_partition_details.get(vm_key, [])
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
        network_readiness = assess_network_readiness(
            vm_nics,
            network_detail_available=network_detail_available
        )
        vm_memory = memory_summary.get(vm_key, {})
        memory_readiness = assess_memory_readiness(
            vm_memory.get("configured_mib", o_ram),
            vm_memory.get("active_mib", 0),
            vm_memory.get("consumed_mib", 0),
            vm_memory.get("ballooned_mib", 0),
            vm_memory.get("swapped_mib", 0),
            vm_memory.get("reservation_mib", 0),
            vm_memory.get("limit_mib", -1),
            vm_memory.get("hot_add", ""),
            source_available=vm_key in memory_summary
        )
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
        s_tier = recommend_storage_tier(vm_n, usage)

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
            o_cpu, memory_readiness['sizing_memory_mib'], c_use, target_region,
            utilization_threshold, t_gb, s_tier, memory_is_sizing=True,
            catalog=catalog_profiles,
            storage_tier_rates=storage_tier_rates,
            pricing_metadata=pricing_metadata
        )

        baseline = map_vmware_to_ibm_vpc(
            o_cpu, o_ram, 100, target_region,
            100, t_gb, s_tier,
            catalog=catalog_profiles,
            storage_tier_rates=storage_tier_rates,
            pricing_metadata=pricing_metadata
        )
        savings = round(max(0.0, baseline['monthly'] - mapping['monthly']), 2)
        normalized_net = normalize_network_name(vm_net or 'unknown-net')
        default_subnet = f"module.networking.{normalized_net}_id"
        default_sg = (
            f"module.networking.{normalized_net}_sg_id"
            if generate_security_groups else "N/A"
        )

        processed_vms.append(MigrationVm.from_record({
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
            'Partition Details': vm_unmatched_partitions,
            'Partition Count': (
                sum(len(disk.get("partitions", [])) for disk in vm_disk_details)
                + len(vm_unmatched_partitions)
            ),
            'Unmatched Partition Count': len(vm_unmatched_partitions),
            'Firmware': readiness['firmware'],
            'Boot Disk GB': readiness['boot_disk_gb'],
            'Guest Customization': readiness['guest_customization'],
            'Image Readiness': readiness['status'],
            'Readiness Reasons': readiness['reasons'],
            'Migration Readiness': migration_readiness['status'],
            'Migration Readiness Reasons': migration_readiness['reasons'],
            'Readiness Findings': vm_findings,
            'Network Readiness': network_readiness['status'],
            'Network Readiness Reasons': network_readiness['reasons'],
            'Network Readiness Findings': network_readiness['findings'],
            'Memory Readiness': memory_readiness['status'],
            'Memory Readiness Reasons': memory_readiness['reasons'],
            'Configured Memory MiB': memory_readiness['configured_mib'],
            'Active Memory MiB': memory_readiness['active_mib'],
            'Consumed Memory MiB': memory_readiness['consumed_mib'],
            'Ballooned Memory MiB': memory_readiness['ballooned_mib'],
            'Swapped Memory MiB': memory_readiness['swapped_mib'],
            'Memory Reservation MiB': memory_readiness['reservation_mib'],
            'Memory Limit MiB': memory_readiness['limit_mib'],
            'Memory Hot Add': memory_readiness['hot_add'],
            'Sizing Memory MiB': memory_readiness['sizing_memory_mib'],
            'Memory Sizing Basis': memory_readiness['sizing_basis'],
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
            'Pricing Source': mapping['pricing_source'],
            'Pricing Confidence': mapping['pricing_confidence'],
            'Pricing Last Updated': mapping['pricing_last_updated'],
            'Pricing Status': mapping.get('pricing_status', ''),
            'Profile Hourly': mapping['profile_hourly'],
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
        }))


    return ParsedRvtoolsWorkbook(
        processed_vms=processed_vms,
        unique_nets=unique_nets,
        disk_details=disk_details,
        nic_details=nic_details,
        assessment_quality=assessment_quality,
        df_vcluster=df_vcluster,
        df_vhost=df_vhost,
        df_vcpu=df_vcpu,
    )

