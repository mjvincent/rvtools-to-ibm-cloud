"""
Terraform renderer for Carbon UI network planning state.

This module generates Terraform HCL from Carbon UI's NetworkPlanningState,
bridging the gap between visual network planning and infrastructure as code.
"""

import json
import math
from typing import Dict, List, Optional
from models.network_planning import (
    NetworkPlanningState,
    VpcPlan,
    SubnetPlan,
    SecurityGroupPlan,
    SecurityRule,
    NetworkComponentPlan,
    VmNetworkAssignment,
)
from models import MigrationVm


def _hcl_string(value, default=""):
    """Render a value as a quoted HCL string literal."""
    return json.dumps(str(value if value is not None else default))


def _safe_resource_name(value):
    """Convert a name to a safe Terraform resource name."""
    import re
    cleaned = str(value).lower()
    cleaned = re.sub(r"[^0-9a-zA-Z_]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    if not cleaned:
        cleaned = "unknown"
    if cleaned[0].isdigit():
        cleaned = f"r_{cleaned}"
    return cleaned


def _ibm_name(value):
    """Convert a name to IBM Cloud naming convention (lowercase with hyphens)."""
    import re
    cleaned = _safe_resource_name(value).replace("_", "-")
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "unknown"


# =============================================================================
# VPC Generation
# =============================================================================

def render_vpc_from_carbon(vpc: VpcPlan, project_name: str = "carbon-migration") -> str:
    """
    Generate Terraform HCL for a VPC from Carbon planning state.

    Args:
        vpc: VpcPlan from Carbon UI
        project_name: Project name for tagging

    Returns:
        Terraform HCL string for ibm_is_vpc resource
    """
    vpc_resource_name = _safe_resource_name(vpc.name)
    address_prefix_mode = "manual" if vpc.address_prefix_mode == "manual" else "auto"

    hcl = f"""
resource "ibm_is_vpc" "{vpc_resource_name}" {{
  name                      = {_hcl_string(vpc.name)}
  address_prefix_management = {_hcl_string(address_prefix_mode)}
  resource_group            = {_hcl_string(vpc.resource_group_id) if vpc.resource_group_id else "null"}
  tags                      = [{_hcl_string(f"project:{project_name}")}, {_hcl_string(f"vpc:{vpc.name}")}, "managed-by:carbon-ui"]
}}
"""

    # Generate address prefixes if manual mode
    if vpc.address_prefix_mode == "manual" and vpc.address_prefixes:
        for prefix in vpc.address_prefixes:
            prefix_resource_name = _safe_resource_name(prefix.name)
            hcl += f"""
resource "ibm_is_vpc_address_prefix" "{vpc_resource_name}_{prefix_resource_name}" {{
  name = {_hcl_string(prefix.name)}
  zone = {_hcl_string(prefix.zone)}
  vpc  = ibm_is_vpc.{vpc_resource_name}.id
  cidr = {_hcl_string(prefix.cidr)}
}}
"""

    return hcl


# =============================================================================
# Subnet Generation
# =============================================================================

def render_subnet_from_carbon(
    subnet: SubnetPlan,
    vpc_resource_name: str,
    project_name: str = "carbon-migration"
) -> str:
    """
    Generate Terraform HCL for a subnet from Carbon planning state.

    Args:
        subnet: SubnetPlan from Carbon UI
        vpc_resource_name: Terraform resource name of the parent VPC
        project_name: Project name for tagging

    Returns:
        Terraform HCL string for ibm_is_subnet resource
    """
    subnet_resource_name = _safe_resource_name(subnet.name)

    hcl = f"""
resource "ibm_is_subnet" "{subnet_resource_name}" {{
  name            = {_hcl_string(subnet.name)}
  vpc             = ibm_is_vpc.{vpc_resource_name}.id
  zone            = {_hcl_string(subnet.zone)}
  ipv4_cidr_block = {_hcl_string(subnet.cidr)}
"""

    # Add public gateway if specified
    if subnet.public_gateway and subnet.public_gateway_id:
        pgw_resource_name = _safe_resource_name(subnet.public_gateway_id)
        hcl += f"  public_gateway = ibm_is_public_gateway.{pgw_resource_name}.id\n"

    # Add ACL if specified
    if subnet.acl_id:
        acl_resource_name = _safe_resource_name(subnet.acl_id)
        hcl += f"  network_acl     = ibm_is_network_acl.{acl_resource_name}.id\n"

    # Add route table if specified
    if subnet.route_table_id:
        rt_resource_name = _safe_resource_name(subnet.route_table_id)
        hcl += f"  routing_table   = ibm_is_vpc_routing_table.{rt_resource_name}.id\n"

    # Add tags
    tags = [
        _hcl_string(f"project:{project_name}"),
        _hcl_string(f"subnet:{subnet.name}"),
        _hcl_string(f"purpose:{subnet.purpose}"),
        '"managed-by:carbon-ui"'
    ]
    hcl += f"  tags            = [{', '.join(tags)}]\n"
    hcl += "}\n"

    return hcl


# =============================================================================
# Security Group Generation
# =============================================================================

def render_security_rule_from_carbon(
    rule: SecurityRule,
    sg_resource_name: str,
    rule_index: int
) -> str:
    """
    Generate Terraform HCL for a security group rule.

    Args:
        rule: SecurityRule from Carbon UI
        sg_resource_name: Terraform resource name of the parent security group
        rule_index: Index of the rule for unique naming

    Returns:
        Terraform HCL string for ibm_is_security_group_rule resource
    """
    rule_resource_name = f"{sg_resource_name}_rule_{rule_index}"

    hcl = f"""
resource "ibm_is_security_group_rule" "{rule_resource_name}" {{
  group     = ibm_is_security_group.{sg_resource_name}.id
  direction = {_hcl_string(rule.direction)}
  remote    = {_hcl_string(rule.source if rule.direction == "inbound" else rule.destination)}
"""

    # Add protocol-specific configuration
    if rule.protocol == "tcp":
        hcl += f"""
  tcp {{
    port_min = {rule.port_min}
    port_max = {rule.port_max}
  }}
"""
    elif rule.protocol == "udp":
        hcl += f"""
  udp {{
    port_min = {rule.port_min}
    port_max = {rule.port_max}
  }}
"""
    elif rule.protocol == "icmp":
        hcl += """
  icmp {
    type = 8
  }
"""
    # For "all" protocol, no additional block needed

    hcl += "}\n"
    return hcl


def render_security_group_from_carbon(
    sg: SecurityGroupPlan,
    vpc_resource_name: str,
    project_name: str = "carbon-migration"
) -> str:
    """
    Generate Terraform HCL for a security group from Carbon planning state.

    Args:
        sg: SecurityGroupPlan from Carbon UI
        vpc_resource_name: Terraform resource name of the parent VPC
        project_name: Project name for tagging

    Returns:
        Terraform HCL string for ibm_is_security_group and rules
    """
    sg_resource_name = _safe_resource_name(sg.name)

    # Generate security group resource
    hcl = f"""
resource "ibm_is_security_group" "{sg_resource_name}" {{
  name = {_hcl_string(sg.name)}
  vpc  = ibm_is_vpc.{vpc_resource_name}.id
  tags = [{_hcl_string(f"project:{project_name}")}, {_hcl_string(f"sg:{sg.name}")}, {_hcl_string(f"purpose:{sg.purpose}")}, "managed-by:carbon-ui"]
}}
"""

    # Generate rules
    for idx, rule in enumerate(sg.rules):
        hcl += render_security_rule_from_carbon(rule, sg_resource_name, idx)

    return hcl


# =============================================================================
# Network Component Generation (Placeholders)
# =============================================================================

def render_public_gateway_from_carbon(
    component: NetworkComponentPlan,
    vpc_resource_name: str,
    project_name: str = "carbon-migration"
) -> str:
    """Generate Terraform HCL for a public gateway."""
    pgw_resource_name = _safe_resource_name(component.name)

    return f"""
resource "ibm_is_public_gateway" "{pgw_resource_name}" {{
  name = {_hcl_string(component.name)}
  vpc  = ibm_is_vpc.{vpc_resource_name}.id
  zone = {_hcl_string(component.config.get('zone', 'us-south-1'))}
  tags = [{_hcl_string(f"project:{project_name}")}, {_hcl_string(f"pgw:{component.name}")}, "managed-by:carbon-ui"]
}}
"""


def render_load_balancer_from_carbon(
    component: NetworkComponentPlan,
    project_name: str = "carbon-migration"
) -> str:
    """Generate Terraform HCL placeholder for a load balancer."""
    lb_resource_name = _safe_resource_name(component.name)

    return f"""
# Load Balancer: {component.name}
# TODO: Implement full load balancer configuration
# Configuration: {json.dumps(component.config, indent=2)}
resource "ibm_is_lb" "{lb_resource_name}" {{
  name    = {_hcl_string(component.name)}
  subnets = [] # TODO: Add subnet IDs from config
  type    = {_hcl_string(component.config.get('type', 'public'))}
  tags    = [{_hcl_string(f"project:{project_name}")}, {_hcl_string(f"lb:{component.name}")}, "managed-by:carbon-ui"]
}}
"""


def render_vpe_gateway_from_carbon(
    component: NetworkComponentPlan,
    vpc_resource_name: str,
    project_name: str = "carbon-migration"
) -> str:
    """Generate Terraform HCL placeholder for a VPE gateway."""
    vpe_resource_name = _safe_resource_name(component.name)

    return f"""
# VPE Gateway: {component.name}
# Service: {component.config.get('serviceName', 'unknown')}
# TODO: Implement full VPE gateway configuration
resource "ibm_is_virtual_endpoint_gateway" "{vpe_resource_name}" {{
  name = {_hcl_string(component.name)}
  vpc  = ibm_is_vpc.{vpc_resource_name}.id
  # target = [] # TODO: Add service target
  tags = [{_hcl_string(f"project:{project_name}")}, {_hcl_string(f"vpe:{component.name}")}, "managed-by:carbon-ui"]
}}
"""


def render_network_component_from_carbon(
    component: NetworkComponentPlan,
    vpc_resource_name: str,
    project_name: str = "carbon-migration"
) -> str:
    """
    Route network component to appropriate renderer based on type.

    Args:
        component: NetworkComponentPlan from Carbon UI
        vpc_resource_name: Terraform resource name of the parent VPC
        project_name: Project name for tagging

    Returns:
        Terraform HCL string for the network component
    """
    if component.type == "public_gateway":
        return render_public_gateway_from_carbon(component, vpc_resource_name, project_name)
    elif component.type == "load_balancer":
        return render_load_balancer_from_carbon(component, project_name)
    elif component.type == "vpe_gateway":
        return render_vpe_gateway_from_carbon(component, vpc_resource_name, project_name)
    else:
        # Placeholder for other component types
        return f"""
# Network Component: {component.name} (Type: {component.type})
# TODO: Implement {component.type} generation
# Configuration: {json.dumps(component.config, indent=2)}
"""


# =============================================================================
# VSI Generation from VM Assignments
# =============================================================================

def render_vsi_from_carbon_assignment(
    vm: MigrationVm,
    assignment: VmNetworkAssignment,
    vpc_resource_name: str,
    project_name: str = "carbon-migration"
) -> str:
    """
    Generate Terraform HCL for a VSI from Carbon VM assignment.

    Args:
        vm: MigrationVm with VM details
        assignment: VmNetworkAssignment from Carbon UI
        vpc_resource_name: Terraform resource name of the VPC
        project_name: Project name for tagging

    Returns:
        Terraform HCL string for ibm_is_instance resource
    """
    vm_resource_name = _safe_resource_name(assignment.vm_name)
    profile = vm.get('Override Profile') or vm.get('IBM Profile', 'bx2-2x8')

    # Get subnet and security group resource names
    primary_subnet_res = _safe_resource_name(assignment.primary_subnet_id)
    primary_sg_res = _safe_resource_name(assignment.primary_security_group_id)

    hcl = f"""
resource "ibm_is_instance" "{vm_resource_name}" {{
  name    = {_hcl_string(_ibm_name(assignment.vm_name))}
  image   = var.custom_image_ids[{_hcl_string(assignment.vm_key)}]
  profile = {_hcl_string(profile)}
  vpc     = ibm_is_vpc.{vpc_resource_name}.id
  zone    = var.zone

  primary_network_interface {{
    name            = "eth0"
    subnet          = ibm_is_subnet.{primary_subnet_res}.id
    security_groups = [ibm_is_security_group.{primary_sg_res}.id]
  }}
"""

    # Add secondary NICs if present
    for idx, sec_nic in enumerate(assignment.secondary_nics, start=1):
        sec_subnet_res = _safe_resource_name(sec_nic.subnet_id)
        sec_sg_res = _safe_resource_name(sec_nic.security_group_id)
        hcl += f"""
  network_interfaces {{
    name            = "eth{idx}"
    subnet          = ibm_is_subnet.{sec_subnet_res}.id
    security_groups = [ibm_is_security_group.{sec_sg_res}.id]
  }}
"""

    # Add tags
    tags = [
        _hcl_string(f"project:{project_name}"),
        _hcl_string(f"vm:{vm_resource_name}"),
        '"managed-by:carbon-ui"'
    ]
    if assignment.wave_id:
        tags.append(_hcl_string(f"wave:{assignment.wave_id}"))

    hcl += f"  tags = [{', '.join(tags)}]\n"
    hcl += "}\n"

    return hcl


# =============================================================================
# Complete Network Plan Rendering
# =============================================================================

def render_networking_from_carbon_plan(
    network_plan: NetworkPlanningState,
    project_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate complete Terraform configuration from Carbon network planning state.

    This is the main entry point for converting Carbon UI planning into Terraform HCL.

    Args:
        network_plan: NetworkPlanningState from Carbon UI
        project_name: Optional project name override

    Returns:
        Dictionary mapping filename to HCL content:
        {
            "vpc.tf": "...",
            "subnets.tf": "...",
            "security_groups.tf": "...",
            "network_components.tf": "...",
            "variables.tf": "...",
            "outputs.tf": "..."
        }
    """
    if project_name is None:
        project_name = network_plan.metadata.get('project_name', 'carbon-migration')

    terraform_files = {}

    # Generate provider configuration
    terraform_files["providers.tf"] = """terraform {
  required_version = ">= 1.0"
  required_providers {
    ibm = {
      source  = "IBM-Cloud/ibm"
      version = ">= 1.70.0"
    }
  }
}

provider "ibm" {
  region = var.region
}
"""

    # Generate VPCs
    vpc_hcl = "# VPC Resources\n"
    vpc_resource_names = {}
    for vpc in network_plan.vpcs:
        vpc_hcl += render_vpc_from_carbon(vpc, project_name)
        vpc_resource_names[vpc.id] = _safe_resource_name(vpc.name)
    terraform_files["vpc.tf"] = vpc_hcl

    # Generate Subnets
    subnet_hcl = "# Subnet Resources\n"
    for subnet in network_plan.subnets:
        vpc_res_name = vpc_resource_names.get(subnet.vpc_id, "unknown_vpc")
        subnet_hcl += render_subnet_from_carbon(subnet, vpc_res_name, project_name)
    terraform_files["subnets.tf"] = subnet_hcl

    # Generate Security Groups
    sg_hcl = "# Security Group Resources\n"
    for sg in network_plan.security_groups:
        vpc_res_name = vpc_resource_names.get(sg.vpc_id, "unknown_vpc")
        sg_hcl += render_security_group_from_carbon(sg, vpc_res_name, project_name)
    terraform_files["security_groups.tf"] = sg_hcl

    # Generate Network Components
    if network_plan.network_components:
        nc_hcl = "# Network Components\n"
        for component in network_plan.network_components:
            vpc_res_name = vpc_resource_names.get(component.vpc_id, "unknown_vpc")
            nc_hcl += render_network_component_from_carbon(component, vpc_res_name, project_name)
        terraform_files["network_components.tf"] = nc_hcl

    # Generate Variables
    terraform_files["variables.tf"] = """variable "region" {
  description = "IBM Cloud region"
  type        = string
  default     = "us-south"
}

variable "zone" {
  description = "IBM Cloud availability zone"
  type        = string
  default     = "us-south-1"
}

variable "custom_image_ids" {
  description = "Map of VM names to custom image IDs"
  type        = map(string)
  default     = {}
}
"""

    # Generate Outputs
    outputs_hcl = "# Outputs\n"
    for vpc in network_plan.vpcs:
        vpc_res_name = _safe_resource_name(vpc.name)
        outputs_hcl += f"""
output "{vpc_res_name}_id" {{
  description = "ID of VPC {vpc.name}"
  value       = ibm_is_vpc.{vpc_res_name}.id
}}
"""
    terraform_files["outputs.tf"] = outputs_hcl

    return terraform_files


# Made with Bob
