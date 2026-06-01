from dataclasses import dataclass, field

from .base import clean_value, get_record_value


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
class SourceMetadata:
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
    total_storage_gb: float = 0
    disk_count: int = 0
    nic_count: int = 0
    primary_network: str = ""
    primary_ip: str = ""
    disks: list = field(default_factory=list)
    partitions: list = field(default_factory=list)
    nics: list = field(default_factory=list)


@dataclass
class TargetRecommendation:
    ibm_profile: str = ""
    override_profile: str = ""
    storage_tier: str = "3iops-tier"
    override_storage_tier: str = ""
    subnet: str = ""
    security_group: str = ""
    compute_cost_monthly: float = 0
    storage_cost_monthly: float = 0
    monthly_cost: float = 0
    baseline_cost_monthly: float = 0
    savings_monthly: float = 0
    right_sized: str = ""

    @property
    def effective_profile(self):
        return clean_value(self.override_profile) or clean_value(
            self.ibm_profile, "bx2-2x8"
        )

    @property
    def effective_storage_tier(self):
        return clean_value(self.override_storage_tier) or clean_value(
            self.storage_tier, "3iops-tier"
        )


@dataclass
class PricingMetadata:
    source: str = ""
    confidence: str = ""
    last_updated: str = ""
    status: str = ""
    profile_hourly: float = 0


@dataclass
class ImageReadiness:
    status: str = "Review"
    reasons: str = ""
    firmware: str = ""
    boot_disk_gb: float = 0
    guest_customization: str = ""


@dataclass
class MemoryReadiness:
    status: str = "Review"
    reasons: str = ""
    configured_mib: float = 0
    active_mib: float = 0
    consumed_mib: float = 0
    ballooned_mib: float = 0
    swapped_mib: float = 0
    reservation_mib: float = 0
    limit_mib: float = 0
    hot_add: str = ""
    sizing_memory_mib: float = 0
    sizing_basis: str = ""


@dataclass
class NetworkReadiness:
    status: str = "Review"
    reasons: str = ""
    findings: list = field(default_factory=list)


@dataclass
class MigrationReadiness:
    status: str = "Review"
    reasons: str = ""
    snapshot_count: int = 0
    snapshot_size_mib: float = 0
    vmware_tools_status: str = ""
    mounted_media: str = ""
    usb_devices: int = 0
    health_warnings: int = 0
    findings: list = field(default_factory=list)
