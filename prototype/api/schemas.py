"""
Pydantic validation schemas for FastAPI endpoints.
These schemas validate incoming requests and outgoing responses.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import re


class AddressPrefixSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    cidr: str = Field(..., regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
    zone: str
    is_default: bool = False


class VpcPlanSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    region: str
    address_prefix_mode: str = Field(default="manual", regex="^(manual|auto)$")
    address_prefixes: List[AddressPrefixSchema] = []
    resource_group_id: Optional[str] = None
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str
    updated_at: str

    @validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Name must contain only lowercase letters, numbers, and hyphens"
            )
        return v


class SubnetPlanSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    vpc_id: str
    zone: str
    cidr: str = Field(..., regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
    purpose: str = ""
    source_network: Optional[str] = None
    public_gateway: bool = False
    public_gateway_id: Optional[str] = None
    acl_id: Optional[str] = None
    route_table_id: Optional[str] = None
    ipv4_cidr_count: Optional[int] = None
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str
    updated_at: str


class SecurityRuleSchema(BaseModel):
    id: str
    direction: str = Field(..., regex="^(inbound|outbound)$")
    protocol: str = Field(..., regex="^(tcp|udp|icmp|all)$")
    port_min: Optional[int] = Field(None, ge=1, le=65535)
    port_max: Optional[int] = Field(None, ge=1, le=65535)
    source: Optional[str] = None
    destination: Optional[str] = None
    description: str = ""

    @validator("port_max")
    def validate_port_range(cls, v, values):
        if "port_min" in values and values["port_min"] and v:
            if v < values["port_min"]:
                raise ValueError("port_max must be >= port_min")
        return v


class SecurityGroupPlanSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    vpc_id: str
    purpose: str = ""
    rules: List[SecurityRuleSchema] = []
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str
    updated_at: str


class StorageProfilePlanSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    tier: str
    iops_intent: str = ""
    notes: str = ""
    created_at: str
    updated_at: str


class WavePlanSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    owner: str = ""
    target_window: str = ""
    priority: str = Field(default="medium", regex="^(high|medium|low)$")
    notes: str = ""
    created_at: str
    updated_at: str


class NetworkComponentPlanSchema(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=63)
    type: str = Field(
        ...,
        regex="^(public_gateway|vpn_gateway|load_balancer|vpe_gateway|floating_ip|route_table|acl)$"
    )
    vpc_id: str
    subnet_id: Optional[str] = None
    attachment: str = ""
    config: Dict[str, Any] = {}
    tags: Dict[str, str] = {}
    notes: str = ""
    created_at: str
    updated_at: str


class SecondaryNicAssignmentSchema(BaseModel):
    id: str
    subnet_id: str
    security_group_id: str
    order: int = Field(..., ge=1)
    source_network: Optional[str] = None


class VmNetworkAssignmentSchema(BaseModel):
    vm_key: str
    vm_name: str
    primary_subnet_id: str
    primary_security_group_id: str
    secondary_nics: List[SecondaryNicAssignmentSchema] = []
    storage_profile_id: Optional[str] = None
    wave_id: Optional[str] = None
    excluded: bool = False
    exclusion_reason: Optional[str] = None


class PlanningMetadataSchema(BaseModel):
    project_name: str = ""
    target_region: str = "us-south"
    target_zone: str = "us-south-1"
    deployment_target: str = Field(
        default="plain_cli",
        regex="^(plain_cli|schematics)$"
    )
    created_by: Optional[str] = None
    created_at: str
    updated_at: str
    rvtools_filename: Optional[str] = None
    rvtools_uploaded_at: Optional[str] = None


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
