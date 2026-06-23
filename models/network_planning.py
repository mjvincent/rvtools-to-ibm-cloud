"""
Network Planning Schema v1.0

Python dataclass models for network planning state.
These models mirror the TypeScript schema and provide
conversion to/from dict for JSON serialization.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

SCHEMA_VERSION = "1.0"


@dataclass
class AddressPrefix:
    """VPC address prefix."""
    id: str
    name: str
    cidr: str
    zone: str
    is_default: bool = False


@dataclass
class VpcPlan:
    """VPC planning configuration."""
    id: str
    name: str
    region: str
    address_prefix_mode: str = "manual"
    address_prefixes: List[AddressPrefix] = field(default_factory=list)
    resource_group_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        if self.address_prefix_mode not in ("manual", "auto"):
            raise ValueError("address_prefix_mode must be 'manual' or 'auto'")
        # Convert dict address_prefixes to AddressPrefix objects
        if self.address_prefixes and isinstance(self.address_prefixes[0], dict):
            self.address_prefixes = [
                AddressPrefix(**ap) for ap in self.address_prefixes
            ]


@dataclass
class SubnetPlan:
    """Subnet planning configuration."""
    id: str
    name: str
    vpc_id: str
    zone: str
    cidr: str
    purpose: str = ""
    source_network: Optional[str] = None
    public_gateway: bool = False
    public_gateway_id: Optional[str] = None
    acl_id: Optional[str] = None
    route_table_id: Optional[str] = None
    ipv4_cidr_count: Optional[int] = None
    tags: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SecurityRule:
    """Security group rule."""
    id: str
    direction: str
    protocol: str
    port_min: Optional[int] = None
    port_max: Optional[int] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    description: str = ""

    def __post_init__(self):
        if self.direction not in ("inbound", "outbound"):
            raise ValueError("direction must be 'inbound' or 'outbound'")
        if self.protocol not in ("tcp", "udp", "icmp", "all"):
            raise ValueError("protocol must be 'tcp', 'udp', 'icmp', or 'all'")


@dataclass
class SecurityGroupPlan:
    """Security group planning configuration."""
    id: str
    name: str
    vpc_id: str
    purpose: str = ""
    rules: List[SecurityRule] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        # Convert dict rules to SecurityRule objects
        if self.rules and isinstance(self.rules[0], dict):
            self.rules = [SecurityRule(**rule) for rule in self.rules]


@dataclass
class StorageProfilePlan:
    """Storage profile planning configuration."""
    id: str
    name: str
    tier: str
    iops_intent: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class WavePlan:
    """Migration wave planning configuration."""
    id: str
    name: str
    owner: str = ""
    target_window: str = ""
    priority: str = "medium"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class NetworkComponentPlan:
    """Network component planning configuration."""
    id: str
    name: str
    type: str
    vpc_id: str
    subnet_id: Optional[str] = None
    attachment: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SecondaryNicAssignment:
    """Secondary NIC assignment."""
    id: str
    subnet_id: str
    security_group_id: str
    order: int
    source_network: Optional[str] = None


@dataclass
class VmNetworkAssignment:
    """VM network assignment."""
    vm_key: str
    vm_name: str
    primary_subnet_id: str
    primary_security_group_id: str
    secondary_nics: List[SecondaryNicAssignment] = field(default_factory=list)
    storage_profile_id: Optional[str] = None
    wave_id: Optional[str] = None
    excluded: bool = False
    exclusion_reason: Optional[str] = None

    def __post_init__(self):
        # Convert dict secondary_nics to SecondaryNicAssignment objects
        if self.secondary_nics and isinstance(self.secondary_nics[0], dict):
            self.secondary_nics = [
                SecondaryNicAssignment(**nic) for nic in self.secondary_nics
            ]


@dataclass
class PlanningMetadata:
    """Planning metadata."""
    project_name: str = ""
    target_region: str = "us-south"
    target_zone: str = "us-south-1"
    deployment_target: str = "plain_cli"
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    rvtools_filename: Optional[str] = None
    rvtools_uploaded_at: Optional[str] = None


@dataclass
class NetworkPlanningState:
    """Root network planning state object."""
    version: str = SCHEMA_VERSION
    vpcs: List[VpcPlan] = field(default_factory=list)
    subnets: List[SubnetPlan] = field(default_factory=list)
    security_groups: List[SecurityGroupPlan] = field(default_factory=list)
    storage_profiles: List[StorageProfilePlan] = field(default_factory=list)
    waves: List[WavePlan] = field(default_factory=list)
    network_components: List[NetworkComponentPlan] = field(default_factory=list)
    vm_assignments: List[VmNetworkAssignment] = field(default_factory=list)
    metadata: PlanningMetadata = field(default_factory=PlanningMetadata)

    def __post_init__(self):
        # Convert dict objects to dataclass instances
        if self.vpcs and isinstance(self.vpcs[0], dict):
            self.vpcs = [VpcPlan(**vpc) for vpc in self.vpcs]
        if self.subnets and isinstance(self.subnets[0], dict):
            self.subnets = [SubnetPlan(**subnet) for subnet in self.subnets]
        if self.security_groups and isinstance(self.security_groups[0], dict):
            self.security_groups = [
                SecurityGroupPlan(**sg) for sg in self.security_groups
            ]
        if self.storage_profiles and isinstance(self.storage_profiles[0], dict):
            self.storage_profiles = [
                StorageProfilePlan(**sp) for sp in self.storage_profiles
            ]
        if self.waves and isinstance(self.waves[0], dict):
            self.waves = [WavePlan(**wave) for wave in self.waves]
        if self.network_components and isinstance(self.network_components[0], dict):
            self.network_components = [
                NetworkComponentPlan(**nc) for nc in self.network_components
            ]
        if self.vm_assignments and isinstance(self.vm_assignments[0], dict):
            self.vm_assignments = [
                VmNetworkAssignment(**va) for va in self.vm_assignments
            ]
        if isinstance(self.metadata, dict):
            self.metadata = PlanningMetadata(**self.metadata)


# Conversion helpers
def to_dict(obj: Any) -> Dict[str, Any]:
    """Convert dataclass to dict recursively."""
    if hasattr(obj, '__dataclass_fields__'):
        return asdict(obj)
    return obj


def from_dict(data: Dict[str, Any]) -> NetworkPlanningState:
    """Convert dict to NetworkPlanningState."""
    return NetworkPlanningState(**data)

# Made with Bob
