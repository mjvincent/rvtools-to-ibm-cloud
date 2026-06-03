from dataclasses import dataclass, field

from .base import as_bool, clean_number, clean_value, get_record_value, _prefer
from .network import NicMapping
from .readiness import (
    ImageReadiness,
    MemoryReadiness,
    MigrationReadiness,
    NetworkReadiness,
    PricingMetadata,
    ReadinessFinding,
    SourceMetadata,
    TargetRecommendation,
)
from .storage import DiskMapping, PartitionMapping


@dataclass
class MigrationVm:
    exclude: bool = False
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
    # Optional human-friendly reasons for decisions
    override_profile_reason: str = ""
    storage_tier: str = "3iops-tier"
    override_storage_tier: str = ""
    override_storage_tier_reason: str = ""
    exclusion_reason: str = ""
    subnet: str = ""
    security_group: str = ""
    compute_cost_monthly: float = 0
    storage_cost_monthly: float = 0
    total_storage_gb: float = 0
    monthly_cost: float = 0
    baseline_cost_monthly: float = 0
    savings_monthly: float = 0
    data_status: str = ""
    right_sized: str = ""
    ready_pct: float = 0
    overall_mhz: float = 0
    vp_ratio: float = 0
    disk_count: int = 0
    data_disk_count: int = 0
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
    network_readiness: str = "Review"
    network_readiness_reasons: str = ""
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
    pricing_status: str = ""
    profile_hourly: float = 0
    wave: str = ""
    cutover_group: str = ""
    owner: str = ""
    application: str = ""
    priority: str = ""
    dependency_group: str = ""
    disks: list = field(default_factory=list)
    partitions: list = field(default_factory=list)
    nics: list = field(default_factory=list)
    readiness_findings: list = field(default_factory=list)
    network_readiness_findings: list = field(default_factory=list)
    source: SourceMetadata = field(default_factory=SourceMetadata)
    target: TargetRecommendation = field(default_factory=TargetRecommendation)
    pricing: PricingMetadata = field(default_factory=PricingMetadata)
    image: ImageReadiness = field(default_factory=ImageReadiness)
    memory: MemoryReadiness = field(default_factory=MemoryReadiness)
    network_status: NetworkReadiness = field(default_factory=NetworkReadiness)
    migration: MigrationReadiness = field(default_factory=MigrationReadiness)

    def __post_init__(self):
        self.disks = [self._disk(disk) for disk in self.disks]
        self.partitions = [
            self._partition(partition) for partition in self.partitions
        ]
        self.nics = [self._nic(nic) for nic in self.nics]
        self.readiness_findings = [
            self._finding(finding) for finding in self.readiness_findings
        ]
        self.network_readiness_findings = [
            self._finding(finding) for finding in self.network_readiness_findings
        ]
        self.network_status.findings = [
            self._finding(finding) for finding in self.network_status.findings
        ]
        self.migration.findings = [
            self._finding(finding) for finding in self.migration.findings
        ]
        self._pull_nested_defaults()
        self.disks = [self._disk(disk) for disk in self.disks]
        self.partitions = [
            self._partition(partition) for partition in self.partitions
        ]
        self.nics = [self._nic(nic) for nic in self.nics]
        self.readiness_findings = [
            self._finding(finding) for finding in self.readiness_findings
        ]
        self.network_readiness_findings = [
            self._finding(finding) for finding in self.network_readiness_findings
        ]
        self._refresh_nested_records()

    @staticmethod
    def _disk(record):
        return record if isinstance(record, DiskMapping) else DiskMapping.from_record(record)

    @staticmethod
    def _partition(record):
        if isinstance(record, PartitionMapping):
            return record
        return PartitionMapping.from_record(record)

    @staticmethod
    def _nic(record):
        return record if isinstance(record, NicMapping) else NicMapping.from_record(record)

    @staticmethod
    def _finding(record):
        if isinstance(record, ReadinessFinding):
            return record
        return ReadinessFinding.from_record(record)

    @classmethod
    def from_record(cls, record):
        return cls(
            exclude=as_bool(get_record_value(record, "Exclude?")),
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
            override_profile_reason=clean_value(get_record_value(record, "Override Profile Reason")),
            override_storage_tier_reason=clean_value(get_record_value(record, "Override Storage Tier Reason")),
            exclusion_reason=clean_value(get_record_value(record, "Exclusion Reason")),
            subnet=clean_value(get_record_value(record, "Subnet")),
            security_group=clean_value(get_record_value(record, "Security Group")),
            compute_cost_monthly=clean_value(
                get_record_value(record, "Compute (Mo)"), 0
            ),
            storage_cost_monthly=clean_value(
                get_record_value(record, "Storage (Mo)"), 0
            ),
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
            vp_ratio=clean_value(get_record_value(record, "v_p_Ratio"), 0),
            disk_count=clean_value(get_record_value(record, "Disk Count"), 0),
            data_disk_count=clean_value(
                get_record_value(record, "Data Disk Count"), 0
            ),
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
            network_readiness=clean_value(
                get_record_value(record, "Network Readiness"), "Review"
            ),
            network_readiness_reasons=clean_value(
                get_record_value(record, "Network Readiness Reasons")
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
            pricing_status=clean_value(get_record_value(record, "Pricing Status")),
            profile_hourly=clean_value(get_record_value(record, "Profile Hourly"), 0),
            wave=_prefer(
                get_record_value(record, "wave"),
                get_record_value(record, "Wave"),
            ),
            cutover_group=_prefer(
                get_record_value(record, "cutover_group"),
                get_record_value(record, "Cutover Group"),
            ),
            owner=_prefer(
                get_record_value(record, "owner"),
                get_record_value(record, "Owner"),
            ),
            application=_prefer(
                get_record_value(record, "application"),
                get_record_value(record, "Application"),
            ),
            priority=_prefer(
                get_record_value(record, "priority"),
                get_record_value(record, "Priority"),
            ),
            dependency_group=_prefer(
                get_record_value(record, "dependency_group"),
                get_record_value(record, "Dependency Group"),
            ),
            disks=[
                DiskMapping.from_record(d)
                for d in get_record_value(record, "Disk Details", []) or []
            ],
            partitions=[
                PartitionMapping.from_record(p)
                for p in get_record_value(record, "Partition Details", []) or []
            ],
            nics=[
                NicMapping.from_record(n)
                for n in get_record_value(record, "Network Details", []) or []
            ],
            readiness_findings=[
                ReadinessFinding.from_record(f)
                for f in get_record_value(record, "Readiness Findings", []) or []
            ],
            network_readiness_findings=[
                ReadinessFinding.from_record(f)
                for f in get_record_value(
                    record, "Network Readiness Findings", []
                ) or []
            ],
        )

    @property
    def effective_profile(self):
        return self.target.effective_profile

    @property
    def effective_storage_tier(self):
        return self.target.effective_storage_tier

    def _pull_nested_defaults(self):
        self.vm_key = _prefer(self.vm_key, self.source.vm_key)
        self.vm_name = _prefer(self.vm_name, self.source.vm_name)
        self.power_state = _prefer(self.power_state, self.source.power_state)
        self.source_ip = _prefer(self.source_ip, self.source.source_ip)
        self.network = _prefer(self.network, self.source.network, "unknown-net")
        self.guest_os = _prefer(self.guest_os, self.source.guest_os)
        self.host = _prefer(self.host, self.source.host)
        self.cluster = _prefer(self.cluster, self.source.cluster)
        self.datacenter = _prefer(self.datacenter, self.source.datacenter)
        self.original_specs = _prefer(self.original_specs, self.source.original_specs)
        self.total_storage_gb = _prefer(
            self.total_storage_gb, self.source.total_storage_gb, 0
        )
        self.disk_count = _prefer(self.disk_count, self.source.disk_count, 0)
        self.nic_count = _prefer(self.nic_count, self.source.nic_count, 0)
        self.primary_network = _prefer(
            self.primary_network, self.source.primary_network
        )
        self.primary_ip = _prefer(self.primary_ip, self.source.primary_ip)
        self.ibm_profile = _prefer(self.ibm_profile, self.target.ibm_profile)
        self.override_profile = _prefer(
            self.override_profile, self.target.override_profile
        )
        self.storage_tier = _prefer(
            self.storage_tier, self.target.storage_tier, "3iops-tier"
        )
        self.override_storage_tier = _prefer(
            self.override_storage_tier, self.target.override_storage_tier
        )
        self.subnet = _prefer(self.subnet, self.target.subnet)
        self.security_group = _prefer(self.security_group, self.target.security_group)
        self.compute_cost_monthly = _prefer(
            self.compute_cost_monthly, self.target.compute_cost_monthly, 0
        )
        self.storage_cost_monthly = _prefer(
            self.storage_cost_monthly, self.target.storage_cost_monthly, 0
        )
        self.monthly_cost = _prefer(self.monthly_cost, self.target.monthly_cost, 0)
        self.baseline_cost_monthly = _prefer(
            self.baseline_cost_monthly, self.target.baseline_cost_monthly, 0
        )
        self.savings_monthly = _prefer(
            self.savings_monthly, self.target.savings_monthly, 0
        )
        self.right_sized = _prefer(self.right_sized, self.target.right_sized)
        self.pricing_source = _prefer(self.pricing_source, self.pricing.source)
        self.pricing_confidence = _prefer(
            self.pricing_confidence, self.pricing.confidence
        )
        self.pricing_last_updated = _prefer(
            self.pricing_last_updated, self.pricing.last_updated
        )
        self.pricing_status = _prefer(self.pricing_status, self.pricing.status)
        self.profile_hourly = _prefer(
            self.profile_hourly, self.pricing.profile_hourly, 0
        )
        self.image_readiness = _prefer(
            self.image_readiness, self.image.status, "Review"
        )
        self.readiness_reasons = _prefer(
            self.readiness_reasons, self.image.reasons
        )
        self.firmware = _prefer(self.firmware, self.image.firmware)
        self.boot_disk_gb = _prefer(self.boot_disk_gb, self.image.boot_disk_gb, 0)
        self.guest_customization = _prefer(
            self.guest_customization, self.image.guest_customization
        )
        self.memory_readiness = _prefer(
            self.memory_readiness, self.memory.status, "Review"
        )
        self.memory_readiness_reasons = _prefer(
            self.memory_readiness_reasons, self.memory.reasons
        )
        self.configured_memory_mib = _prefer(
            self.configured_memory_mib, self.memory.configured_mib, 0
        )
        self.active_memory_mib = _prefer(
            self.active_memory_mib, self.memory.active_mib, 0
        )
        self.consumed_memory_mib = _prefer(
            self.consumed_memory_mib, self.memory.consumed_mib, 0
        )
        self.ballooned_memory_mib = _prefer(
            self.ballooned_memory_mib, self.memory.ballooned_mib, 0
        )
        self.swapped_memory_mib = _prefer(
            self.swapped_memory_mib, self.memory.swapped_mib, 0
        )
        self.memory_reservation_mib = _prefer(
            self.memory_reservation_mib, self.memory.reservation_mib, 0
        )
        self.memory_limit_mib = _prefer(
            self.memory_limit_mib, self.memory.limit_mib, 0
        )
        self.memory_hot_add = _prefer(self.memory_hot_add, self.memory.hot_add)
        self.sizing_memory_mib = _prefer(
            self.sizing_memory_mib, self.memory.sizing_memory_mib, 0
        )
        self.memory_sizing_basis = _prefer(
            self.memory_sizing_basis, self.memory.sizing_basis
        )
        self.network_readiness = _prefer(
            self.network_readiness, self.network_status.status, "Review"
        )
        self.network_readiness_reasons = _prefer(
            self.network_readiness_reasons, self.network_status.reasons
        )
        self.migration_readiness = _prefer(
            self.migration_readiness, self.migration.status, "Review"
        )
        self.migration_readiness_reasons = _prefer(
            self.migration_readiness_reasons, self.migration.reasons
        )
        self.snapshot_count = _prefer(
            self.snapshot_count, self.migration.snapshot_count, 0
        )
        self.snapshot_size_mib = _prefer(
            self.snapshot_size_mib, self.migration.snapshot_size_mib, 0
        )
        self.vmware_tools_status = _prefer(
            self.vmware_tools_status, self.migration.vmware_tools_status
        )
        self.mounted_media = _prefer(self.mounted_media, self.migration.mounted_media)
        self.usb_devices = _prefer(self.usb_devices, self.migration.usb_devices, 0)
        self.health_warnings = _prefer(
            self.health_warnings, self.migration.health_warnings, 0
        )
        if not self.disks:
            self.disks = list(self.source.disks)
        if not self.partitions:
            self.partitions = list(self.source.partitions)
        if not self.nics:
            self.nics = list(self.source.nics)
        if not self.readiness_findings:
            self.readiness_findings = list(self.migration.findings)
        if not self.network_readiness_findings:
            self.network_readiness_findings = list(self.network_status.findings)

    def _refresh_nested_records(self):
        self.source = SourceMetadata(
            vm_key=self.vm_key,
            vm_name=self.vm_name,
            power_state=self.power_state,
            source_ip=self.source_ip,
            network=self.network,
            guest_os=self.guest_os,
            host=self.host,
            cluster=self.cluster,
            datacenter=self.datacenter,
            original_specs=self.original_specs,
            total_storage_gb=self.total_storage_gb,
            disk_count=self.disk_count,
            nic_count=self.nic_count,
            primary_network=self.primary_network,
            primary_ip=self.primary_ip,
            disks=self.disks,
            partitions=self.partitions,
            nics=self.nics,
        )
        self.target = TargetRecommendation(
            ibm_profile=self.ibm_profile,
            override_profile=self.override_profile,
            storage_tier=self.storage_tier,
            override_storage_tier=self.override_storage_tier,
            subnet=self.subnet,
            security_group=self.security_group,
            compute_cost_monthly=self.compute_cost_monthly,
            storage_cost_monthly=self.storage_cost_monthly,
            monthly_cost=self.monthly_cost,
            baseline_cost_monthly=self.baseline_cost_monthly,
            savings_monthly=self.savings_monthly,
            right_sized=self.right_sized,
        )
        self.pricing = PricingMetadata(
            source=self.pricing_source,
            confidence=self.pricing_confidence,
            last_updated=self.pricing_last_updated,
            status=self.pricing_status,
            profile_hourly=self.profile_hourly,
        )
        self.image = ImageReadiness(
            status=self.image_readiness,
            reasons=self.readiness_reasons,
            firmware=self.firmware,
            boot_disk_gb=self.boot_disk_gb,
            guest_customization=self.guest_customization,
        )
        self.memory = MemoryReadiness(
            status=self.memory_readiness,
            reasons=self.memory_readiness_reasons,
            configured_mib=self.configured_memory_mib,
            active_mib=self.active_memory_mib,
            consumed_mib=self.consumed_memory_mib,
            ballooned_mib=self.ballooned_memory_mib,
            swapped_mib=self.swapped_memory_mib,
            reservation_mib=self.memory_reservation_mib,
            limit_mib=self.memory_limit_mib,
            hot_add=self.memory_hot_add,
            sizing_memory_mib=self.sizing_memory_mib,
            sizing_basis=self.memory_sizing_basis,
        )
        self.network_status = NetworkReadiness(
            status=self.network_readiness,
            reasons=self.network_readiness_reasons,
            findings=self.network_readiness_findings,
        )
        self.migration = MigrationReadiness(
            status=self.migration_readiness,
            reasons=self.migration_readiness_reasons,
            snapshot_count=self.snapshot_count,
            snapshot_size_mib=self.snapshot_size_mib,
            vmware_tools_status=self.vmware_tools_status,
            mounted_media=self.mounted_media,
            usb_devices=self.usb_devices,
            health_warnings=self.health_warnings,
            findings=self.readiness_findings,
        )

    def to_record(self):
        self._refresh_nested_records()
        partition_count = sum(
            clean_number(disk.partition_count, 0) for disk in self.disks
        ) + len(self.partitions)
        if float(partition_count).is_integer():
            partition_count = int(partition_count)
        return {
            "Exclude?": self.exclude,
            "VM Key": self.vm_key,
            "VM Name": self.vm_name,
            "Power State": self.power_state,
            "Source IP": self.source_ip,
            "NIC Count": self.nic_count,
            "Primary Network": self.primary_network,
            "Primary IP": self.primary_ip,
            "Network Details": [nic.to_record() for nic in self.nics],
            "Guest OS": self.guest_os,
            "Disk Count": self.disk_count,
            "Data Disk Count": self.data_disk_count,
            "Disk Details": [disk.to_record() for disk in self.disks],
            "Partition Details": [
                partition.to_record() for partition in self.partitions
            ],
            "Partition Count": partition_count,
            "Unmatched Partition Count": len(self.partitions),
            "Firmware": self.firmware,
            "Boot Disk GB": self.boot_disk_gb,
            "Guest Customization": self.guest_customization,
            "Image Readiness": self.image_readiness,
            "Readiness Reasons": self.readiness_reasons,
            "Migration Readiness": self.migration_readiness,
            "Migration Readiness Reasons": self.migration_readiness_reasons,
            "Readiness Findings": [
                finding.to_record() for finding in self.readiness_findings
            ],
            "Network Readiness": self.network_readiness,
            "Network Readiness Reasons": self.network_readiness_reasons,
            "Network Readiness Findings": [
                finding.to_record()
                for finding in self.network_readiness_findings
            ],
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
            "Host": self.host,
            "Cluster": self.cluster,
            "Datacenter": self.datacenter,
            "Original Specs": self.original_specs,
            "IBM Profile": self.ibm_profile,
            "Override Profile": self.override_profile,
            "Compute (Mo)": self.compute_cost_monthly,
            "Storage (Mo)": self.storage_cost_monthly,
            "Baseline Cost (Mo)": self.baseline_cost_monthly,
            "Savings (Mo)": self.savings_monthly,
            "Monthly Cost": self.monthly_cost,
            "Pricing Source": self.pricing_source,
            "Pricing Confidence": self.pricing_confidence,
            "Pricing Last Updated": self.pricing_last_updated,
            "Pricing Status": self.pricing_status,
            "Profile Hourly": self.profile_hourly,
            "Subnet": self.subnet,
            "Security Group": self.security_group,
            "Override Storage Tier": self.override_storage_tier,
            "Override Profile Reason": self.override_profile_reason,
            "Override Storage Tier Reason": self.override_storage_tier_reason,
            "Exclusion Reason": self.exclusion_reason,
            "Right-Sized": self.right_sized,
            "Storage Tier": self.storage_tier,
            "Total Storage GB": self.total_storage_gb,
            "Data Status": self.data_status,
            "v_p_Ratio": self.vp_ratio,
            "Ready_Pct": self.ready_pct,
            "Overall_MHz": self.overall_mhz,
            "Network": self.network,
            "wave": self.wave,
            "cutover_group": self.cutover_group,
            "owner": self.owner,
            "application": self.application,
            "priority": self.priority,
            "dependency_group": self.dependency_group,
        }

    def get(self, key, default=None):
        return self.to_record().get(key, default)
