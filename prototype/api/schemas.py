"""
Pydantic validation schemas for FastAPI endpoints.
These schemas validate incoming requests and outgoing responses.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class AddressPrefixSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    cidr: str = Field(..., pattern=r"^$|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
    zone: str
    is_default: bool = Field(default=False, alias="isDefault")


class VpcPlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    region: str
    address_prefix_mode: str = Field(default="manual", pattern="^(manual|auto)$", alias="addressPrefixMode")
    address_prefixes: List[AddressPrefixSchema] = Field(default=[], alias="addressPrefixes")
    resource_group_id: Optional[str] = Field(default=None, alias="resourceGroupId")
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")

class SubnetPlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    vpc_id: str = Field(..., alias="vpcId")
    zone: str
    # Carbon saves draft planning state before export; blank CIDRs are reported
    # by package preflight instead of blocking persistence.
    cidr: str = Field(..., pattern=r"^$|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
    purpose: str = ""
    source_network: Optional[str] = Field(default=None, alias="sourceNetwork")
    public_gateway: bool = Field(default=False, alias="publicGateway")
    public_gateway_id: Optional[str] = Field(default=None, alias="publicGatewayId")
    acl_id: Optional[str] = Field(default=None, alias="aclId")
    route_table_id: Optional[str] = Field(default=None, alias="routeTableId")
    ipv4_cidr_count: Optional[int] = Field(default=None, alias="ipv4CidrCount")
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")


class SecurityRuleSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    direction: str = Field(..., pattern="^(inbound|outbound)$")
    protocol: str = Field(..., pattern="^(tcp|udp|icmp|all)$")
    port_min: Optional[int] = Field(None, ge=1, le=65535, alias="portMin")
    port_max: Optional[int] = Field(None, ge=1, le=65535, alias="portMax")
    source: Optional[str] = None
    destination: Optional[str] = None
    description: str = ""

    @field_validator("port_max")
    @classmethod
    def validate_port_range(cls, v, info):
        if info.data.get("port_min") and v:
            if v < info.data["port_min"]:
                raise ValueError("port_max must be >= port_min")
        return v


class SecurityGroupPlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    vpc_id: str = Field(default="", alias="vpcId")  # Optional, can be inferred from first VPC
    purpose: str = ""
    rules: List[SecurityRuleSchema] = []
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")


class StorageProfilePlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    tier: str
    iops_intent: str = Field(default="", alias="iopsIntent")
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")


class WavePlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    owner: str = ""
    target_window: str = Field(default="", alias="targetWindow")
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")


class NetworkComponentPlanSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(..., min_length=1, max_length=63)
    type: str  # Accept any string, will normalize in validator
    vpc_id: str = Field(..., alias="vpcId")
    subnet_id: Optional[str] = Field(default=None, alias="subnetId")
    attachment: str = ""
    config: Dict[str, Any] = {}
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")

    @field_validator("type")
    @classmethod
    def normalize_type(cls, v):
        # Normalize display names to snake_case identifiers
        type_map = {
            "Public Gateway": "public_gateway",
            "VPN Gateway": "vpn_gateway",
            "Load Balancer": "load_balancer",
            "VPE Gateway": "vpe_gateway",
            "Floating IP": "floating_ip",
            "Route Table": "route_table",
            "ACL": "acl",
            "Transit Gateway": "transit_gateway",  # Not in original pattern but used
        }
        return type_map.get(v, v.lower().replace(" ", "_"))


class SecondaryNicAssignmentSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    subnet_id: str = Field(..., alias="subnetId")
    security_group_id: str = Field(..., alias="securityGroupId")
    order: int = Field(..., ge=1)
    source_network: Optional[str] = Field(default=None, alias="sourceNetwork")


class VmNetworkAssignmentSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vm_key: str = Field(..., alias="vmKey")
    vm_name: str = Field(..., alias="vmName")
    primary_subnet_id: str = Field(..., alias="primarySubnetId")
    primary_security_group_id: str = Field(..., alias="primarySecurityGroupId")
    secondary_nics: List[SecondaryNicAssignmentSchema] = Field(default=[], alias="secondaryNics")
    storage_profile_id: Optional[str] = Field(default=None, alias="storageProfileId")
    wave_id: Optional[str] = Field(default=None, alias="waveId")
    excluded: bool = False
    exclusion_reason: Optional[str] = Field(default=None, alias="exclusionReason")
    # Compute specifications for VSI generation
    cpu_count: Optional[int] = Field(default=None, alias="cpuCount", ge=1, le=128)
    memory_gb: Optional[float] = Field(default=None, alias="memoryGb", ge=1, le=1024)
    ibm_profile: Optional[str] = Field(default=None, alias="ibmProfile")
    override_profile: Optional[str] = Field(default=None, alias="overrideProfile")
    override_profile_reason: Optional[str] = Field(default=None, alias="overrideProfileReason")
    storage_tier: Optional[str] = Field(default=None, alias="storageTier")
    override_storage_tier: Optional[str] = Field(default=None, alias="overrideStorageTier")
    override_storage_tier_reason: Optional[str] = Field(default=None, alias="overrideStorageTierReason")
    network: Optional[str] = None
    owner: Optional[str] = None
    application: Optional[str] = None
    # Boot disk specifications
    boot_disk_gb: Optional[float] = Field(default=None, alias="bootDiskGb", ge=10, le=2000)
    # Custom image reference
    custom_image_id: Optional[str] = Field(default=None, alias="customImageId")
    guest_os: Optional[str] = Field(default=None, alias="guestOs")


class PlanningMetadataSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    project_name: str = Field(default="", alias="projectName")
    target_region: str = Field(default="us-south", alias="targetRegion")
    target_zone: str = Field(default="us-south-1", alias="targetZone")
    deployment_target: str = Field(
        default="plain_cli",
        pattern="^(plain_cli|schematics)$",
        alias="deploymentTarget"
    )
    ssh_public_key: Optional[str] = Field(default=None, alias="sshPublicKey")
    ssh_key_name: Optional[str] = Field(default=None, alias="sshKeyName")
    resource_group_id: Optional[str] = Field(default=None, alias="resourceGroupId")
    backend_type: str = Field(default="local", pattern="^(local|s3|cos)$", alias="backendType")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="createdAt")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="updatedAt")
    rvtools_filename: Optional[str] = Field(default=None, alias="rvtoolsFilename")
    rvtools_uploaded_at: Optional[str] = Field(default=None, alias="rvtoolsUploadedAt")


class NetworkPlanningStateSchema(BaseModel):
    version: str = "1.0"
    vpcs: List[VpcPlanSchema] = []
    subnets: List[SubnetPlanSchema] = []
    security_groups: List[SecurityGroupPlanSchema] = []
    storage_profiles: List[StorageProfilePlanSchema] = []
    waves: List[WavePlanSchema] = []
    network_components: List[NetworkComponentPlanSchema] = []
    vm_assignments: List[VmNetworkAssignmentSchema] = []
    metadata: PlanningMetadataSchema

# Made with Bob
