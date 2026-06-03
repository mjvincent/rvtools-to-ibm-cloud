from dataclasses import dataclass

from .base import as_float, clean_cell, clean_disk_key, get_row_identity


@dataclass
class StorageInventory:
    disk_sum: dict
    disk_count: dict
    boot_disk_gb: dict
    disk_details: dict
    unmatched_partition_details: dict
    partitions_by_vm: dict


def build_storage_inventory(df_vdisk, df_vpartition):
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

    cap_c = next((c for c in df_vdisk.columns if "Capacity" in c), None)
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

    return StorageInventory(
        disk_sum=disk_sum,
        disk_count=disk_count,
        boot_disk_gb=boot_disk_gb,
        disk_details=disk_details,
        unmatched_partition_details=unmatched_partition_details,
        partitions_by_vm=partitions_by_vm,
    )
