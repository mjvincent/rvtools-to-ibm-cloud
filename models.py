from dataclasses import dataclass, field


def clean_value(value, default=""):
    """Return JSON/CSV friendly scalar values from pandas/Streamlit records."""
    if value is None:
        return default
    try:
        if value != value:
            return default
    except TypeError:
        pass
    if isinstance(value, str):
        stripped = value.strip()
        return default if stripped.lower() == "nan" else stripped
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return default
    return value


def as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(clean_value(value)).strip().lower()
    if not text:
        return default
    return text in ["true", "yes", "1", "connected", "poweredon"]


def get_record_value(record, key, default=""):
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


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

    @classmethod
    def from_record(cls, record):
        return cls(
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
        )

    def to_record(self):
        return self.__dict__.copy()


@dataclass
class NicMapping:
    label: str = ""
    adapter: str = ""
    network: str = "unknown-net"
    switch: str = ""
    connected: bool = True
    starts_connected: str = ""
    mac_address: str = ""
    type: str = ""
    ipv4: str = ""
    ipv6: str = ""
    planned: bool = True

    @classmethod
    def from_record(cls, record):
        return cls(
            label=clean_value(get_record_value(record, "label")),
            adapter=clean_value(get_record_value(record, "adapter")),
            network=clean_value(get_record_value(record, "network"), "unknown-net"),
            switch=clean_value(get_record_value(record, "switch")),
            connected=as_bool(get_record_value(record, "connected", True), True),
            starts_connected=clean_value(
                get_record_value(record, "starts_connected")
            ),
            mac_address=clean_value(get_record_value(record, "mac_address")),
            type=clean_value(get_record_value(record, "type")),
            ipv4=clean_value(get_record_value(record, "ipv4")),
            ipv6=clean_value(get_record_value(record, "ipv6")),
            planned=as_bool(get_record_value(record, "planned", True), True),
        )

    def to_record(self):
        return self.__dict__.copy()


@dataclass
class ReadinessFinding:
    finding_type: str = ""
    severity: str = "Review"
    source_tab: str = ""
    evidence: str = ""
    recommended_action: str = ""

    @classmethod
    def from_record(cls, record):
        return cls(
            finding_type=clean_value(get_record_value(record, "finding_type")),
            severity=clean_value(get_record_value(record, "severity"), "Review"),
            source_tab=clean_value(get_record_value(record, "source_tab")),
            evidence=clean_value(get_record_value(record, "evidence")),
            recommended_action=clean_value(
                get_record_value(record, "recommended_action")
            ),
        )

    def to_record(self):
        return self.__dict__.copy()


@dataclass
class MigrationVm:
    vm_key: str = ""
    vm_name: str = ""
    power_state: str = ""
    source_ip: str = ""
    network: str = "unknown-net"
    guest_os: str = ""
    host: str = ""
    cluster: str = ""
    datacenter: str = ""
    original_specs: str = ""
    ibm_profile: str = ""
    override_profile: str = ""
    storage_tier: str = "3iops-tier"
    override_storage_tier: str = ""
    subnet: str = ""
    security_group: str = ""
    total_storage_gb: float = 0
    monthly_cost: float = 0
    baseline_cost_monthly: float = 0
    savings_monthly: float = 0
    data_status: str = ""
    right_sized: str = ""
    ready_pct: float = 0
    overall_mhz: float = 0
    disk_count: int = 0
    nic_count: int = 0
    primary_network: str = ""
    primary_ip: str = ""
    firmware: str = ""
    boot_disk_gb: float = 0
    guest_customization: str = ""
    image_readiness: str = "Review"
    readiness_reasons: str = ""
    migration_readiness: str = "Review"
    migration_readiness_reasons: str = ""
    memory_readiness: str = "Review"
    memory_readiness_reasons: str = ""
    configured_memory_mib: float = 0
    active_memory_mib: float = 0
    consumed_memory_mib: float = 0
    ballooned_memory_mib: float = 0
    swapped_memory_mib: float = 0
    memory_reservation_mib: float = 0
    memory_limit_mib: float = 0
    memory_hot_add: str = ""
    sizing_memory_mib: float = 0
    memory_sizing_basis: str = ""
    snapshot_count: int = 0
    snapshot_size_mib: float = 0
    vmware_tools_status: str = ""
    mounted_media: str = ""
    usb_devices: int = 0
    health_warnings: int = 0
    pricing_source: str = ""
    pricing_confidence: str = ""
    pricing_last_updated: str = ""
    profile_hourly: float = 0
    disks: list = field(default_factory=list)
    nics: list = field(default_factory=list)
    readiness_findings: list = field(default_factory=list)

    @classmethod
    def from_record(cls, record):
        return cls(
            vm_key=clean_value(get_record_value(record, "VM Key")),
            vm_name=clean_value(get_record_value(record, "VM Name")),
            power_state=clean_value(get_record_value(record, "Power State")),
            source_ip=clean_value(get_record_value(record, "Source IP")),
            network=clean_value(get_record_value(record, "Network"), "unknown-net"),
            guest_os=clean_value(get_record_value(record, "Guest OS")),
            host=clean_value(get_record_value(record, "Host")),
            cluster=clean_value(get_record_value(record, "Cluster")),
            datacenter=clean_value(get_record_value(record, "Datacenter")),
            original_specs=clean_value(get_record_value(record, "Original Specs")),
            ibm_profile=clean_value(get_record_value(record, "IBM Profile")),
            override_profile=clean_value(get_record_value(record, "Override Profile")),
            storage_tier=clean_value(
                get_record_value(record, "Storage Tier"), "3iops-tier"
            ),
            override_storage_tier=clean_value(
                get_record_value(record, "Override Storage Tier")
            ),
            subnet=clean_value(get_record_value(record, "Subnet")),
            security_group=clean_value(get_record_value(record, "Security Group")),
            total_storage_gb=clean_value(
                get_record_value(record, "Total Storage GB"), 0
            ),
            monthly_cost=clean_value(get_record_value(record, "Monthly Cost"), 0),
            baseline_cost_monthly=clean_value(
                get_record_value(record, "Baseline Cost (Mo)"), 0
            ),
            savings_monthly=clean_value(get_record_value(record, "Savings (Mo)"), 0),
            data_status=clean_value(get_record_value(record, "Data Status")),
            right_sized=clean_value(get_record_value(record, "Right-Sized")),
            ready_pct=clean_value(get_record_value(record, "Ready_Pct"), 0),
            overall_mhz=clean_value(get_record_value(record, "Overall_MHz"), 0),
            disk_count=clean_value(get_record_value(record, "Disk Count"), 0),
            nic_count=clean_value(get_record_value(record, "NIC Count"), 0),
            primary_network=clean_value(get_record_value(record, "Primary Network")),
            primary_ip=clean_value(get_record_value(record, "Primary IP")),
            firmware=clean_value(get_record_value(record, "Firmware")),
            boot_disk_gb=clean_value(get_record_value(record, "Boot Disk GB"), 0),
            guest_customization=clean_value(
                get_record_value(record, "Guest Customization")
            ),
            image_readiness=clean_value(
                get_record_value(record, "Image Readiness"), "Review"
            ),
            readiness_reasons=clean_value(
                get_record_value(record, "Readiness Reasons")
            ),
            migration_readiness=clean_value(
                get_record_value(record, "Migration Readiness"), "Review"
            ),
            migration_readiness_reasons=clean_value(
                get_record_value(record, "Migration Readiness Reasons")
            ),
            memory_readiness=clean_value(
                get_record_value(record, "Memory Readiness"), "Review"
            ),
            memory_readiness_reasons=clean_value(
                get_record_value(record, "Memory Readiness Reasons")
            ),
            configured_memory_mib=clean_value(
                get_record_value(record, "Configured Memory MiB"), 0
            ),
            active_memory_mib=clean_value(
                get_record_value(record, "Active Memory MiB"), 0
            ),
            consumed_memory_mib=clean_value(
                get_record_value(record, "Consumed Memory MiB"), 0
            ),
            ballooned_memory_mib=clean_value(
                get_record_value(record, "Ballooned Memory MiB"), 0
            ),
            swapped_memory_mib=clean_value(
                get_record_value(record, "Swapped Memory MiB"), 0
            ),
            memory_reservation_mib=clean_value(
                get_record_value(record, "Memory Reservation MiB"), 0
            ),
            memory_limit_mib=clean_value(
                get_record_value(record, "Memory Limit MiB"), 0
            ),
            memory_hot_add=clean_value(get_record_value(record, "Memory Hot Add")),
            sizing_memory_mib=clean_value(
                get_record_value(record, "Sizing Memory MiB"), 0
            ),
            memory_sizing_basis=clean_value(
                get_record_value(record, "Memory Sizing Basis")
            ),
            snapshot_count=clean_value(get_record_value(record, "Snapshot Count"), 0),
            snapshot_size_mib=clean_value(
                get_record_value(record, "Snapshot Size MiB"), 0
            ),
            vmware_tools_status=clean_value(
                get_record_value(record, "VMware Tools Status")
            ),
            mounted_media=clean_value(get_record_value(record, "Mounted Media")),
            usb_devices=clean_value(get_record_value(record, "USB Devices"), 0),
            health_warnings=clean_value(
                get_record_value(record, "Health Warnings"), 0
            ),
            pricing_source=clean_value(get_record_value(record, "Pricing Source")),
            pricing_confidence=clean_value(
                get_record_value(record, "Pricing Confidence")
            ),
            pricing_last_updated=clean_value(
                get_record_value(record, "Pricing Last Updated")
            ),
            profile_hourly=clean_value(get_record_value(record, "Profile Hourly"), 0),
            disks=[
                DiskMapping.from_record(d)
                for d in get_record_value(record, "Disk Details", []) or []
            ],
            nics=[
                NicMapping.from_record(n)
                for n in get_record_value(record, "Network Details", []) or []
            ],
            readiness_findings=[
                ReadinessFinding.from_record(f)
                for f in get_record_value(record, "Readiness Findings", []) or []
            ],
        )

    def to_record(self):
        return {
            "VM Key": self.vm_key,
            "VM Name": self.vm_name,
            "Power State": self.power_state,
            "Source IP": self.source_ip,
            "Network": self.network,
            "Guest OS": self.guest_os,
            "Host": self.host,
            "Cluster": self.cluster,
            "Datacenter": self.datacenter,
            "Original Specs": self.original_specs,
            "IBM Profile": self.ibm_profile,
            "Override Profile": self.override_profile,
            "Storage Tier": self.storage_tier,
            "Override Storage Tier": self.override_storage_tier,
            "Subnet": self.subnet,
            "Security Group": self.security_group,
            "Total Storage GB": self.total_storage_gb,
            "Monthly Cost": self.monthly_cost,
            "Baseline Cost (Mo)": self.baseline_cost_monthly,
            "Savings (Mo)": self.savings_monthly,
            "Data Status": self.data_status,
            "Right-Sized": self.right_sized,
            "Ready_Pct": self.ready_pct,
            "Overall_MHz": self.overall_mhz,
            "Disk Count": self.disk_count,
            "NIC Count": self.nic_count,
            "Primary Network": self.primary_network,
            "Primary IP": self.primary_ip,
            "Firmware": self.firmware,
            "Boot Disk GB": self.boot_disk_gb,
            "Guest Customization": self.guest_customization,
            "Image Readiness": self.image_readiness,
            "Readiness Reasons": self.readiness_reasons,
            "Migration Readiness": self.migration_readiness,
            "Migration Readiness Reasons": self.migration_readiness_reasons,
            "Memory Readiness": self.memory_readiness,
            "Memory Readiness Reasons": self.memory_readiness_reasons,
            "Configured Memory MiB": self.configured_memory_mib,
            "Active Memory MiB": self.active_memory_mib,
            "Consumed Memory MiB": self.consumed_memory_mib,
            "Ballooned Memory MiB": self.ballooned_memory_mib,
            "Swapped Memory MiB": self.swapped_memory_mib,
            "Memory Reservation MiB": self.memory_reservation_mib,
            "Memory Limit MiB": self.memory_limit_mib,
            "Memory Hot Add": self.memory_hot_add,
            "Sizing Memory MiB": self.sizing_memory_mib,
            "Memory Sizing Basis": self.memory_sizing_basis,
            "Snapshot Count": self.snapshot_count,
            "Snapshot Size MiB": self.snapshot_size_mib,
            "VMware Tools Status": self.vmware_tools_status,
            "Mounted Media": self.mounted_media,
            "USB Devices": self.usb_devices,
            "Health Warnings": self.health_warnings,
            "Pricing Source": self.pricing_source,
            "Pricing Confidence": self.pricing_confidence,
            "Pricing Last Updated": self.pricing_last_updated,
            "Profile Hourly": self.profile_hourly,
            "Disk Details": [disk.to_record() for disk in self.disks],
            "Network Details": [nic.to_record() for nic in self.nics],
            "Readiness Findings": [
                finding.to_record() for finding in self.readiness_findings
            ],
        }
