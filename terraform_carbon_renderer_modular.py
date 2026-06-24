"""
Modular Terraform renderer for Carbon UI network planning state.

This module generates production-ready Terraform with IBM Cloud best practices:
- Module-based structure (networking, vsi, storage)
- Separate versions.tf, provider.tf, main.tf
- SSH key support
- Backend configuration
- Resource group management
"""

import json
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
# Root File Generation
# =============================================================================

def generate_versions_tf() -> str:
    """Generate versions.tf with Terraform and provider version constraints."""
    return """terraform {
  required_version = ">= 1.0"

  required_providers {
    ibm = {
      source  = "IBM-Cloud/ibm"
      version = ">= 1.70.0"
    }
  }
}
"""


def generate_provider_tf(backend_type: str = "local") -> str:
    """
    Generate provider.tf with IBM Cloud provider and backend configuration.

    Args:
        backend_type: Backend type (local, s3, cos)
    """
    backend_config = ""

    if backend_type == "local":
        backend_config = """
  backend "local" {
    path = "terraform.tfstate"
  }
"""
    elif backend_type == "s3":
        backend_config = """
  backend "s3" {
    # Configure S3 backend in terraform.tfvars or via CLI
    # bucket = "my-terraform-state"
    # key    = "carbon-migration/terraform.tfstate"
    # region = "us-east-1"
  }
"""
    elif backend_type == "cos":
        backend_config = """
  backend "cos" {
    # Configure IBM Cloud Object Storage backend
    # bucket = "my-terraform-state"
    # key    = "carbon-migration/terraform.tfstate"
    # region = "us-south"
  }
"""

    return f"""terraform {{{backend_config}}}

provider "ibm" {{
  region = var.region
}}
"""


def generate_main_tf(
    has_networking: bool = True,
    has_vsi: bool = False,
    has_storage: bool = False,
    resource_group_id: Optional[str] = None
) -> str:
    """
    Generate main.tf that orchestrates module calls.

    Args:
        has_networking: Whether to include networking module
        has_vsi: Whether to include VSI module
        has_storage: Whether to include storage module
        resource_group_id: Optional resource group ID
    """
    hcl = "# Main Terraform Configuration\n"
    hcl += "# This file orchestrates the module calls\n\n"

    # Add resource group data source if provided
    if resource_group_id:
        hcl += f"""data "ibm_resource_group" "group" {{
  name = var.resource_group_name
}}

"""

    # Networking module
    if has_networking:
        hcl += """module "networking" {
  source = "./modules/networking"

  region       = var.region
  zone         = var.zone
  project_name = var.project_name
"""
        if resource_group_id:
            hcl += "  resource_group_id = data.ibm_resource_group.group.id\n"
        hcl += "}\n\n"

    # VSI module
    if has_vsi:
        hcl += """module "vsi" {
  source = "./modules/vsi"

  region           = var.region
  zone             = var.zone
  project_name     = var.project_name
  ssh_public_key   = var.ssh_public_key
  custom_image_ids = var.custom_image_ids
"""
        if has_networking:
            hcl += """
  # Pass networking outputs
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.subnet_ids
  security_group_ids = module.networking.security_group_ids
"""
        if resource_group_id:
            hcl += "  resource_group_id = data.ibm_resource_group.group.id\n"
        hcl += "}\n\n"

    # Storage module
    if has_storage:
        hcl += """module "storage" {
  source = "./modules/storage"

  region       = var.region
  zone         = var.zone
  project_name = var.project_name
"""
        if resource_group_id:
            hcl += "  resource_group_id = data.ibm_resource_group.group.id\n"
        hcl += "}\n\n"

    return hcl


def generate_root_variables_tf(
    has_ssh_key: bool = True,
    has_resource_group: bool = False
) -> str:
    """Generate root variables.tf file."""
    hcl = """# Root Variables

variable "region" {
  description = "IBM Cloud region for deployment"
  type        = string
  default     = "us-south"
}

variable "zone" {
  description = "IBM Cloud availability zone"
  type        = string
  default     = "us-south-1"
}

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "carbon-migration"
}

"""

    if has_ssh_key:
        hcl += """variable "ssh_public_key" {
  description = "SSH public key for VSI access"
  type        = string
  sensitive   = true
}

"""

    if has_resource_group:
        hcl += """variable "resource_group_name" {
  description = "IBM Cloud resource group name"
  type        = string
  default     = "Default"
}

"""

    hcl += """variable "custom_image_ids" {
  description = "Map of VM names to custom image IDs"
  type        = map(string)
  default     = {}
}
"""

    return hcl


def generate_root_outputs_tf(vpc_names: List[str]) -> str:
    """Generate root outputs.tf file."""
    hcl = "# Root Outputs\n\n"

    if vpc_names:
        hcl += """output "vpc_id" {
  description = "VPC ID from networking module"
  value       = module.networking.vpc_id
}

output "subnet_ids" {
  description = "Subnet IDs from networking module"
  value       = module.networking.subnet_ids
}

output "security_group_ids" {
  description = "Security group IDs from networking module"
  value       = module.networking.security_group_ids
}
"""

    return hcl


def generate_terraform_tfvars_example(
    region: str = "us-south",
    zone: str = "us-south-1",
    project_name: str = "carbon-migration",
    resource_group_name: Optional[str] = None
) -> str:
    """Generate terraform.tfvars.example template."""
    hcl = f"""# Terraform Variables Example
# Copy this file to terraform.tfvars and fill in your values

region       = {_hcl_string(region)}
zone         = {_hcl_string(zone)}
project_name = {_hcl_string(project_name)}

# SSH public key for VSI access (REQUIRED)
# Generate with: ssh-keygen -t rsa -b 4096
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQD... your-email@example.com"

"""

    if resource_group_name:
        hcl += f"""# Resource group name
resource_group_name = {_hcl_string(resource_group_name)}

"""

    hcl += """# Custom image IDs (populate after image import)
custom_image_ids = {
  # "vm-name-1" = "r006-12345678-1234-1234-1234-123456789abc"
  # "vm-name-2" = "r006-87654321-4321-4321-4321-cba987654321"
}
"""

    return hcl


# =============================================================================
# Module File Generation
# =============================================================================

def generate_networking_module_main(
    vpcs: List[VpcPlan],
    subnets: List[SubnetPlan],
    security_groups: List[SecurityGroupPlan],
    network_components: List[NetworkComponentPlan],
    project_name: str = "carbon-migration"
) -> str:
    """Generate modules/networking/main.tf"""
    hcl = "# Networking Module - VPCs, Subnets, Security Groups\n\n"

    # Generate VPCs
    vpc_resource_names = {}
    for vpc in vpcs:
        vpc_resource_name = _safe_resource_name(vpc.name)
        vpc_resource_names[vpc.id] = vpc_resource_name
        address_prefix_mode = "manual" if vpc.address_prefix_mode == "manual" else "auto"

        hcl += f"""resource "ibm_is_vpc" "{vpc_resource_name}" {{
  name                      = {_hcl_string(vpc.name)}
  address_prefix_management = {_hcl_string(address_prefix_mode)}
  resource_group            = var.resource_group_id
  tags                      = [var.project_tag, {_hcl_string(f"vpc:{vpc.name}")}, "managed-by:carbon-ui"]
}}

"""

        # Generate address prefixes if manual mode
        if vpc.address_prefix_mode == "manual" and vpc.address_prefixes:
            for prefix in vpc.address_prefixes:
                prefix_resource_name = _safe_resource_name(prefix.name)
                hcl += f"""resource "ibm_is_vpc_address_prefix" "{vpc_resource_name}_{prefix_resource_name}" {{
  name = {_hcl_string(prefix.name)}
  zone = {_hcl_string(prefix.zone)}
  vpc  = ibm_is_vpc.{vpc_resource_name}.id
  cidr = {_hcl_string(prefix.cidr)}
}}

"""

    # Generate Subnets
    subnet_resource_names = {}
    for subnet in subnets:
        subnet_resource_name = _safe_resource_name(subnet.name)
        subnet_resource_names[subnet.id] = subnet_resource_name
        vpc_res_name = vpc_resource_names.get(subnet.vpc_id, "unknown_vpc")

        hcl += f"""resource "ibm_is_subnet" "{subnet_resource_name}" {{
  name            = {_hcl_string(subnet.name)}
  vpc             = ibm_is_vpc.{vpc_res_name}.id
  zone            = {_hcl_string(subnet.zone)}
  ipv4_cidr_block = {_hcl_string(subnet.cidr)}
  resource_group  = var.resource_group_id
  tags            = [var.project_tag, {_hcl_string(f"subnet:{subnet.name}")}, "managed-by:carbon-ui"]
}}

"""

    # Generate Security Groups
    for sg in security_groups:
        sg_resource_name = _safe_resource_name(sg.name)
        vpc_res_name = vpc_resource_names.get(sg.vpc_id, "unknown_vpc")

        hcl += f"""resource "ibm_is_security_group" "{sg_resource_name}" {{
  name           = {_hcl_string(sg.name)}
  vpc            = ibm_is_vpc.{vpc_res_name}.id
  resource_group = var.resource_group_id
  tags           = [var.project_tag, {_hcl_string(f"sg:{sg.name}")}, "managed-by:carbon-ui"]
}}

"""

        # Generate security group rules
        for idx, rule in enumerate(sg.rules):
            rule_resource_name = f"{sg_resource_name}_rule_{idx}"
            direction = rule.direction.lower()

            # Determine remote value based on direction
            if direction == "inbound":
                remote = rule.source or "0.0.0.0/0"
            else:
                remote = rule.destination or "0.0.0.0/0"

            hcl += f"""resource "ibm_is_security_group_rule" "{rule_resource_name}" {{
  group     = ibm_is_security_group.{sg_resource_name}.id
  direction = {_hcl_string(direction)}
  remote    = {_hcl_string(remote)}
"""

            if rule.protocol != "all":
                hcl += f"  {rule.protocol} {{\n"
                if rule.port_min is not None:
                    hcl += f"    port_min = {rule.port_min}\n"
                if rule.port_max is not None:
                    hcl += f"    port_max = {rule.port_max}\n"
                hcl += "  }\n"

            hcl += "}\n\n"

    # Generate Network Components (placeholders for now)
    if network_components:
        hcl += "# Network Components\n"
        hcl += "# TODO: Implement public gateways, load balancers, VPN gateways, etc.\n\n"

    return hcl


def generate_networking_module_variables() -> str:
    """Generate modules/networking/variables.tf"""
    return """# Networking Module Variables

variable "region" {
  description = "IBM Cloud region"
  type        = string
}

variable "zone" {
  description = "IBM Cloud availability zone"
  type        = string
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
}

variable "resource_group_id" {
  description = "Resource group ID"
  type        = string
  default     = null
}

variable "project_tag" {
  description = "Project tag for resources"
  type        = string
  default     = "project:carbon-migration"
}
"""


def generate_networking_module_outputs(
    vpcs: List[VpcPlan],
    subnets: List[SubnetPlan],
    security_groups: List[SecurityGroupPlan]
) -> str:
    """Generate modules/networking/outputs.tf"""
    hcl = "# Networking Module Outputs\n\n"

    if vpcs:
        vpc_resource_name = _safe_resource_name(vpcs[0].name)
        hcl += f"""output "vpc_id" {{
  description = "VPC ID"
  value       = ibm_is_vpc.{vpc_resource_name}.id
}}

"""

    if subnets:
        hcl += """output "subnet_ids" {
  description = "Map of subnet names to IDs"
  value = {
"""
        for subnet in subnets:
            subnet_resource_name = _safe_resource_name(subnet.name)
            hcl += f'    "{subnet.name}" = ibm_is_subnet.{subnet_resource_name}.id\n'
        hcl += "  }\n}\n\n"

    if security_groups:
        hcl += """output "security_group_ids" {
  description = "Map of security group names to IDs"
  value = {
"""
        for sg in security_groups:
            sg_resource_name = _safe_resource_name(sg.name)
            hcl += f'    "{sg.name}" = ibm_is_security_group.{sg_resource_name}.id\n'
        hcl += "  }\n}\n\n"

    return hcl


def _select_ibm_profile(vm: VmNetworkAssignment) -> str:
    """
    Select IBM Cloud profile for a VM based on CPU/RAM specs.

    Priority:
    1. override_profile (if set)
    2. ibm_profile (if set)
    3. Calculate from cpu_count/memory_gb using sizing logic
    4. Default to cx2-2x4
    """
    # Use override if specified
    if vm.override_profile:
        return vm.override_profile

    # Use pre-calculated profile if available
    if vm.ibm_profile:
        return vm.ibm_profile

    # Calculate from CPU/RAM if available
    if vm.cpu_count and vm.memory_gb:
        from sizing import find_cheapest_fit
        profile_data = find_cheapest_fit(vm.cpu_count, vm.memory_gb)
        return profile_data.get('name', 'cx2-2x4')

    # Default fallback
    return 'cx2-2x4'


def generate_vsi_module_main(
    vm_assignments: List[VmNetworkAssignment],
    subnets: List[SubnetPlan],
    security_groups: List[SecurityGroupPlan],
    ssh_key_name: Optional[str] = None
) -> str:
    """Generate modules/vsi/main.tf with SSH key and VSI resources"""
    hcl = "# VSI Module - SSH Keys and Virtual Server Instances\n\n"

    # Generate SSH key resource
    if ssh_key_name:
        key_resource_name = _safe_resource_name(ssh_key_name)
    else:
        key_resource_name = "migration_key"

    hcl += f"""resource "ibm_is_ssh_key" "{key_resource_name}" {{
  name           = var.ssh_key_name
  public_key     = var.ssh_public_key
  resource_group = var.resource_group_id
  tags           = [var.project_tag, "managed-by:carbon-ui"]
}}

"""

    # Generate VSI instances from VM assignments
    if not vm_assignments:
        hcl += "# No VM assignments defined\n\n"
        # Still include stock image data sources even if no VMs
        hcl += """# Stock IBM Cloud Images
data "ibm_is_image" "ubuntu_22_04" {
  name = "ibm-ubuntu-22-04-3-minimal-amd64-1"
}

data "ibm_is_image" "rhel_9" {
  name = "ibm-redhat-9-3-minimal-amd64-1"
}

data "ibm_is_image" "windows_2022" {
  name = "ibm-windows-server-2022-full-standard-amd64-10"
}

"""
        return hcl

    # Create subnet and security group lookup maps
    subnet_map = {s.id: s for s in subnets}
    sg_map = {sg.id: sg for sg in security_groups}

    hcl += "# Virtual Server Instances\n\n"

    for vm in vm_assignments:
        if vm.excluded:
            hcl += f"# VM {vm.vm_name} excluded: {vm.exclusion_reason or 'No reason provided'}\n\n"
            continue

        vm_resource_name = _safe_resource_name(vm.vm_name)
        vm_ibm_name = _ibm_name(vm.vm_name)

        # Select profile
        profile = _select_ibm_profile(vm)

        # Get subnet and security group names
        primary_subnet = subnet_map.get(vm.primary_subnet_id)
        primary_sg = sg_map.get(vm.primary_security_group_id)

        if not primary_subnet or not primary_sg:
            hcl += f"# VM {vm.vm_name} skipped: missing subnet or security group reference\n\n"
            continue

        subnet_name = primary_subnet.name
        sg_name = primary_sg.name

        # Determine image source
        if vm.custom_image_id:
            image_ref = f'var.custom_image_ids["{vm.vm_name}"]'
        else:
            # Use stock IBM image based on guest OS
            guest_os_lower = vm.guest_os.lower() if vm.guest_os else ''
            if 'windows' in guest_os_lower:
                image_ref = 'data.ibm_is_image.windows_2022.id'
            elif 'rhel' in guest_os_lower or 'red hat' in guest_os_lower:
                image_ref = 'data.ibm_is_image.rhel_9.id'
            elif 'ubuntu' in guest_os_lower:
                image_ref = 'data.ibm_is_image.ubuntu_22_04.id'
            else:
                image_ref = 'data.ibm_is_image.ubuntu_22_04.id'  # Default

        # Boot volume size
        boot_volume_capacity = int(vm.boot_disk_gb) if vm.boot_disk_gb else 100

        hcl += f"""resource "ibm_is_instance" "{vm_resource_name}" {{
  name           = "{vm_ibm_name}"
  profile        = "{profile}"
  vpc            = var.vpc_id
  zone           = var.zone
  keys           = [ibm_is_ssh_key.{key_resource_name}.id]
  resource_group = var.resource_group_id

  primary_network_interface {{
    subnet          = var.subnet_ids["{subnet_name}"]
    security_groups = [var.security_group_ids["{sg_name}"]]
  }}

  boot_volume {{
    name     = "{vm_ibm_name}-boot"
    size     = {boot_volume_capacity}
  }}

  image = {image_ref}

  tags = [
    var.project_tag,
    "managed-by:carbon-ui",
    "vm:{vm.vm_name}",
"""

        # Add wave tag if assigned
        if vm.wave_id:
            hcl += f'    "wave:{vm.wave_id}",\n'

        hcl += "  ]\n"

        # Add metadata for profile override reasoning
        if vm.override_profile and vm.override_profile_reason:
            hcl += f'\n  # Profile override: {vm.override_profile_reason}\n'

        hcl += "}\n\n"

        # Generate secondary NICs if present
        if vm.secondary_nics:
            for idx, nic in enumerate(vm.secondary_nics, start=1):
                nic_subnet = subnet_map.get(nic.subnet_id)
                nic_sg = sg_map.get(nic.security_group_id)

                if not nic_subnet or not nic_sg:
                    continue

                nic_resource_name = f"{vm_resource_name}_nic_{idx}"
                nic_ibm_name = f"{vm_ibm_name}-nic-{idx}"

                hcl += f"""resource "ibm_is_instance_network_interface" "{nic_resource_name}" {{
  instance        = ibm_is_instance.{vm_resource_name}.id
  name            = "{nic_ibm_name}"
  subnet          = var.subnet_ids["{nic_subnet.name}"]
  security_groups = [var.security_group_ids["{nic_sg.name}"]]
}}

"""

    # Add stock image data sources
    hcl += """# Stock IBM Cloud Images
data "ibm_is_image" "ubuntu_22_04" {
  name = "ibm-ubuntu-22-04-3-minimal-amd64-1"
}

data "ibm_is_image" "rhel_9" {
  name = "ibm-redhat-9-3-minimal-amd64-1"
}

data "ibm_is_image" "windows_2022" {
  name = "ibm-windows-server-2022-full-standard-amd64-10"
}

"""

    return hcl


def generate_vsi_module_variables() -> str:
    """Generate modules/vsi/variables.tf"""
    return """# VSI Module Variables

variable "region" {
  description = "IBM Cloud region"
  type        = string
}

variable "zone" {
  description = "IBM Cloud availability zone"
  type        = string
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for VSI access"
  type        = string
  sensitive   = true
}

variable "ssh_key_name" {
  description = "Name for the SSH key resource"
  type        = string
  default     = "migration-ssh-key"
}

variable "custom_image_ids" {
  description = "Map of VM names to custom image IDs"
  type        = map(string)
  default     = {}
}

variable "resource_group_id" {
  description = "Resource group ID"
  type        = string
  default     = null
}

variable "project_tag" {
  description = "Project tag for resources"
  type        = string
  default     = "project:carbon-migration"
}

# Networking inputs
variable "vpc_id" {
  description = "VPC ID from networking module"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Map of subnet names to IDs"
  type        = map(string)
  default     = {}
}

variable "security_group_ids" {
  description = "Map of security group names to IDs"
  type        = map(string)
  default     = {}
}
"""


def generate_vsi_module_outputs() -> str:
    """Generate modules/vsi/outputs.tf"""
    return """# VSI Module Outputs

output "ssh_key_id" {
  description = "SSH key ID"
  value       = ibm_is_ssh_key.migration_key.id
}

# VSI outputs will be added as instances are generated
"""


def generate_storage_module_main() -> str:
    """Generate modules/storage/main.tf"""
    return """# Storage Module - Block Storage Volumes

# Storage volumes will be generated here based on VM disk requirements
# TODO: Implement storage volume generation

"""


def generate_storage_module_variables() -> str:
    """Generate modules/storage/variables.tf"""
    return """# Storage Module Variables

variable "region" {
  description = "IBM Cloud region"
  type        = string
}

variable "zone" {
  description = "IBM Cloud availability zone"
  type        = string
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
}

variable "resource_group_id" {
  description = "Resource group ID"
  type        = string
  default     = null
}
"""


def generate_storage_module_outputs() -> str:
    """Generate modules/storage/outputs.tf"""
    return """# Storage Module Outputs

# Storage volume outputs will be added as volumes are generated
"""


# =============================================================================
# Main Modular Rendering Function
# =============================================================================

def render_modular_terraform_from_carbon_plan(
    network_plan: NetworkPlanningState,
    project_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate modular Terraform configuration from Carbon network planning state.

    This generates a production-ready module-based structure following IBM Cloud
    best practices.

    Args:
        network_plan: NetworkPlanningState from Carbon UI
        project_name: Optional project name override

    Returns:
        Dictionary mapping file paths to HCL content:
        {
            "versions.tf": "...",
            "provider.tf": "...",
            "main.tf": "...",
            "variables.tf": "...",
            "outputs.tf": "...",
            "terraform.tfvars.example": "...",
            "modules/networking/main.tf": "...",
            "modules/networking/variables.tf": "...",
            "modules/networking/outputs.tf": "...",
            "modules/vsi/main.tf": "...",
            "modules/vsi/variables.tf": "...",
            "modules/vsi/outputs.tf": "...",
            "modules/storage/main.tf": "...",
            "modules/storage/variables.tf": "...",
            "modules/storage/outputs.tf": "..."
        }
    """
    metadata = network_plan.metadata
    if project_name is None:
        project_name = metadata.project_name or 'carbon-migration'

    region = metadata.target_region or 'us-south'
    zone = metadata.target_zone or 'us-south-1'
    backend_type = metadata.backend_type or 'local'
    resource_group_id = metadata.resource_group_id
    ssh_key_name = metadata.ssh_key_name or 'migration-ssh-key'

    terraform_files = {}

    # Generate root files
    terraform_files["versions.tf"] = generate_versions_tf()
    terraform_files["provider.tf"] = generate_provider_tf(backend_type)

    has_networking = bool(network_plan.vpcs or network_plan.subnets or network_plan.security_groups)
    has_vsi = bool(network_plan.vm_assignments)
    has_storage = False  # TODO: Implement storage detection

    terraform_files["main.tf"] = generate_main_tf(
        has_networking=has_networking,
        has_vsi=has_vsi,
        has_storage=has_storage,
        resource_group_id=resource_group_id
    )

    terraform_files["variables.tf"] = generate_root_variables_tf(
        has_ssh_key=True,
        has_resource_group=bool(resource_group_id)
    )

    vpc_names = [vpc.name for vpc in network_plan.vpcs]
    terraform_files["outputs.tf"] = generate_root_outputs_tf(vpc_names)

    terraform_files["terraform.tfvars.example"] = generate_terraform_tfvars_example(
        region=region,
        zone=zone,
        project_name=project_name,
        resource_group_name="Default" if resource_group_id else None
    )

    # Generate networking module
    if has_networking:
        terraform_files["modules/networking/main.tf"] = generate_networking_module_main(
            network_plan.vpcs,
            network_plan.subnets,
            network_plan.security_groups,
            network_plan.network_components,
            project_name
        )
        terraform_files["modules/networking/variables.tf"] = generate_networking_module_variables()
        terraform_files["modules/networking/outputs.tf"] = generate_networking_module_outputs(
            network_plan.vpcs,
            network_plan.subnets,
            network_plan.security_groups
        )

    # Generate VSI module (always generate for SSH key support)
    terraform_files["modules/vsi/main.tf"] = generate_vsi_module_main(
        network_plan.vm_assignments,
        network_plan.subnets,
        network_plan.security_groups,
        ssh_key_name
    )
    terraform_files["modules/vsi/variables.tf"] = generate_vsi_module_variables()
    terraform_files["modules/vsi/outputs.tf"] = generate_vsi_module_outputs()

    # Generate storage module (always generate for future use)
    terraform_files["modules/storage/main.tf"] = generate_storage_module_main()
    terraform_files["modules/storage/variables.tf"] = generate_storage_module_variables()
    terraform_files["modules/storage/outputs.tf"] = generate_storage_module_outputs()

    return terraform_files


# Made with Bob
