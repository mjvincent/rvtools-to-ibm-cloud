from dataclasses import dataclass, field

from .base import as_bool, clean_number, clean_value, get_record_value


@dataclass
class PartitionMapping:
    disk: str = ""
    disk_key: str = ""
    capacity_mib: float = 0
    consumed_mib: float = 0
    free_mib: float = 0
    free_pct: float = 0
    matched: bool = False

    @classmethod
    def from_record(cls, record):
        return cls(
            disk=clean_value(get_record_value(record, "disk")),
            disk_key=clean_value(get_record_value(record, "disk_key")),
            capacity_mib=clean_value(get_record_value(record, "capacity_mib"), 0),
            consumed_mib=clean_value(
                get_record_value(record, "consumed_mib"), 0
            ),
            free_mib=clean_value(get_record_value(record, "free_mib"), 0),
            free_pct=clean_value(get_record_value(record, "free_pct"), 0),
            matched=as_bool(get_record_value(record, "matched")),
        )

    def to_record(self):
        return self.__dict__.copy()


@dataclass
class DiskMapping:
    disk: str = ""
    capacity_gb: float = 0
    capacity_mib: float = 0
    is_boot: bool = False
    disk_key: str = ""
    disk_path: str = ""
    controller: str = ""
    label: str = ""
    unit_number: str = ""
    scsi_unit: str = ""
    disk_mode: str = ""
    thin: str = ""
    raw: str = ""
    shared_bus: str = ""
    partitions: list = field(default_factory=list)
    partition_count: int = 0
    partition_labels: str = ""
    partition_capacity_mib: float = 0
    partition_consumed_mib: float = 0
    partition_free_mib: float = 0
    partition_free_pct: float = 0

    @classmethod
    def from_record(cls, record):
        partitions = [
            PartitionMapping.from_record(partition)
            for partition in get_record_value(record, "partitions", []) or []
        ]
        disk = cls(
            disk=clean_value(get_record_value(record, "disk")),
            capacity_gb=clean_value(get_record_value(record, "capacity_gb"), 0),
            capacity_mib=clean_value(get_record_value(record, "capacity_mib"), 0),
            is_boot=as_bool(get_record_value(record, "is_boot")),
            disk_key=clean_value(get_record_value(record, "disk_key")),
            disk_path=clean_value(get_record_value(record, "disk_path")),
            controller=clean_value(get_record_value(record, "controller")),
            label=clean_value(get_record_value(record, "label")),
            unit_number=clean_value(get_record_value(record, "unit_number")),
            scsi_unit=clean_value(get_record_value(record, "scsi_unit")),
            disk_mode=clean_value(get_record_value(record, "disk_mode")),
            thin=clean_value(get_record_value(record, "thin")),
            raw=clean_value(get_record_value(record, "raw")),
            shared_bus=clean_value(get_record_value(record, "shared_bus")),
            partitions=partitions,
            partition_count=clean_value(
                get_record_value(record, "partition_count"), 0
            ),
            partition_labels=clean_value(
                get_record_value(record, "partition_labels")
            ),
            partition_capacity_mib=clean_value(
                get_record_value(record, "partition_capacity_mib"), 0
            ),
            partition_consumed_mib=clean_value(
                get_record_value(record, "partition_consumed_mib"), 0
            ),
            partition_free_mib=clean_value(
                get_record_value(record, "partition_free_mib"), 0
            ),
            partition_free_pct=clean_value(
                get_record_value(record, "partition_free_pct"), 0
            ),
        )
        disk.refresh_partition_summary()
        return disk

    def refresh_partition_summary(self):
        self.partitions = [
            partition
            if isinstance(partition, PartitionMapping)
            else PartitionMapping.from_record(partition)
            for partition in self.partitions
        ]
        if not self.partitions:
            return
        self.partition_count = len(self.partitions)
        self.partition_labels = ", ".join([
            clean_value(partition.disk)
            for partition in self.partitions
            if clean_value(partition.disk)
        ])
        self.partition_capacity_mib = sum(
            clean_number(partition.capacity_mib, 0)
            for partition in self.partitions
        )
        self.partition_consumed_mib = sum(
            clean_number(partition.consumed_mib, 0)
            for partition in self.partitions
        )
        self.partition_free_mib = sum(
            clean_number(partition.free_mib, 0)
            for partition in self.partitions
        )
        if self.partition_capacity_mib:
            self.partition_free_pct = round(
                (self.partition_free_mib / self.partition_capacity_mib) * 100,
                2
            )

    def to_record(self):
        self.refresh_partition_summary()
        record = self.__dict__.copy()
        record["partitions"] = [
            partition.to_record() for partition in self.partitions
        ]
        return record
