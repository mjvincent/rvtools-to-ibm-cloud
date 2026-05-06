# --- STRATEGY B: ECONOMIC OPTIMIZER CATALOG ---
IBM_VPC_CATALOG = [
    {"name": "cx2-2x4", "cpu": 2, "ram": 4, "hourly": 0.063},
    {"name": "bx2-2x8", "cpu": 2, "ram": 8, "hourly": 0.114},
    {"name": "mx2-2x16", "cpu": 2, "ram": 16, "hourly": 0.158},
    {"name": "cx2-4x8", "cpu": 4, "ram": 8, "hourly": 0.126},
    {"name": "bx2-4x16", "cpu": 4, "ram": 16, "hourly": 0.228},
    {"name": "mx2-4x32", "cpu": 4, "ram": 32, "hourly": 0.316},
    {"name": "cx2-8x16", "cpu": 8, "ram": 16, "hourly": 0.252},
    {"name": "bx2-8x32", "cpu": 8, "ram": 32, "hourly": 0.456},
]


def find_cheapest_fit(target_cpu, target_ram):
    """Finds the lowest-priced profile that fits requirements."""
    candidates = [
        p for p in IBM_VPC_CATALOG
        if p['cpu'] >= target_cpu and p['ram'] >= target_ram
    ]
    if not candidates:
        return {"name": "bx2-16x64", "cpu": 16, "ram": 64, "hourly": 0.912}
    optimized = sorted(candidates, key=lambda x: x['hourly'])
    return optimized[0]


def map_vmware_to_ibm_vpc(cpus, memory, usage, region,
                          threshold, storage_gb, tier):
    """Strategy B: Full Solution Cost (Compute + Storage)."""
    util_factor = threshold / 100
    needed_cpu = max(1, round(cpus * util_factor))
    needed_ram = max(2, round((memory / 1024) * 0.8))
    optimized = find_cheapest_fit(needed_cpu, needed_ram)

    tier_rates = {
        "3iops-tier": 0.10,
        "5iops-tier": 0.13,
        "10iops-tier": 0.17
    }

    compute_monthly = round(optimized['hourly'] * 730, 2)
    storage_monthly = round(storage_gb * tier_rates.get(tier, 0.10), 2)
    total_monthly = round(compute_monthly + storage_monthly, 2)

    return {
        "profile": optimized['name'],
        "compute_cost": compute_monthly,
        "storage_cost": storage_monthly,
        "monthly": total_monthly,
        "is_rightsized": optimized['cpu'] < cpus
    }


def render_networking_templates(networks_data, vpc_name="migration-vpc", enable_security_groups=True):
    """
    Renders VPC, Address Prefixes, Subnets, and optional security groups.
    address_preference = manual is required for custom customer CIDRs.
    """
    vpc_safe = vpc_name.replace("-", "_")

    hcl = f"""
resource "ibm_is_vpc" "{vpc_safe}" {{
  name = "{vpc_name}"
  address_preference = "manual"
}}
"""

    for i, net in enumerate(networks_data):
        raw_name = net.get('name', 'unknown-net')
        vlan_id = net.get('vlan')
        cidr = net.get('cidr', f"10.0.{i+1}.0/24")

        safe_res = raw_name.lower().replace(" ", "_").replace("-", "_")
        if vlan_id and str(vlan_id).strip():
            safe_res += f"_vlan_{vlan_id}"

        hcl += f"""
resource "ibm_is_vpc_address_prefix" "prefix_{safe_res}" {{
  name = "prefix-{safe_res.replace('_', '-') }"
  zone = var.zone
  vpc  = ibm_is_vpc.{vpc_safe}.id
  cidr = "{cidr}"
}}

resource "ibm_is_subnet" "{safe_res}" {{
  name            = "{safe_res.replace('_', '-')}-subnet"
  vpc             = ibm_is_vpc.{vpc_safe}.id
  zone            = var.zone
  ipv4_cidr_block = "{cidr}"
  depends_on      = [ibm_is_vpc_address_prefix.prefix_{safe_res}]
}}
"""

        if enable_security_groups:
            hcl += f"""
resource "ibm_is_security_group" "sg_{safe_res}" {{
  name = "sg-{safe_res.replace('_', '-') }"
  vpc  = ibm_is_vpc.{vpc_safe}.id
}}

resource "ibm_is_security_group_rule" "ssh_{safe_res}" {{
  security_group = ibm_is_security_group.sg_{safe_res}.id
  direction      = "inbound"
  ip_version     = "ipv4"
  protocol       = "tcp"
  port_min       = 22
  port_max       = 22
  remote         = "0.0.0.0/0"
}}

resource "ibm_is_security_group_rule" "internal_{safe_res}" {{
  security_group = ibm_is_security_group.sg_{safe_res}.id
  direction      = "inbound"
  ip_version     = "ipv4"
  protocol       = "all"
  remote         = "{cidr}"
}}

output "{safe_res}_sg_id" {{
  value = ibm_is_security_group.sg_{safe_res}.id
}}
"""

        hcl += f"""
output "{safe_res}_id" {{
  value = ibm_is_subnet.{safe_res}.id
}}
"""
    return hcl
# Removed unused import os

# ... (Catalog and find_cheapest_fit remain the same) ...

def render_terraform_templates(final_vms, unique_nets, region, zone, enable_security_groups=True):
    """Renders the Root main.tf and module contents."""

    # 1. Call networking logic
    net_hcl = render_networking_templates(
        unique_nets,
        enable_security_groups=enable_security_groups
    )

    # --- ROOT main.tf ---
    # FIXED: Removed 'f' from the string below to solve F541
    vpc_content = """# Root Module
terraform {
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

module "networking" {
  source = "./modules/networking"
  zone   = var.zone
}

module "storage" {
  source = "./modules/storage"
  zone   = var.zone
}

module "vsi" {
  source     = "./modules/vsi"
  zone       = var.zone
  depends_on = [module.storage, module.networking]
}
"""

    vsi_content = f"# VSI Module Configuration for {zone}\n"
    storage_content = f"# Block Storage Module for {zone}\n"

    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = vm_n_raw.replace(" ", "_").replace("-", "_")
        prof = vm.get('IBM Profile', 'bx2-2x8')
        tier = vm.get('Storage Tier', '3iops-tier')
        sz = vm.get('Total Storage GB', 10)

        # FIXED: Shortened variable names to keep line under 79 (E501)
        r_net = vm.get('Network', 'unknown-net')
        t_sub_res = r_net.lower().replace(" ", "_").replace("-", "_")

        vsi_content += f"""
resource "ibm_is_instance" "{safe_n}" {{
  name    = "{safe_n}-vsi"
  profile = "{prof}"
  zone    = var.zone
  primary_network_interface {{
    name   = "eth0"
    subnet = module.networking.{t_sub_res}_id
"""
        if enable_security_groups:
            vsi_content += f"""
    security_groups = [module.networking.{t_sub_res}_sg_id]
"""
        vsi_content += f"""
  }}
}}
"""
        storage_content += f"""
resource "ibm_is_volume" "{safe_n}_vol" {{
  name     = "{safe_n}-vol"
  profile  = "{tier}"
  zone     = var.zone
  capacity = {sz}
}}
"""

    return vsi_content, vpc_content, storage_content, net_hcl


def generate_variables_hcl():
    """Returns root variables definition."""
    return """variable "ibmcloud_api_key" { sensitive = true }
variable "region" { type = string }
variable "zone" { type = string }
variable "project" { type = string }
"""


def generate_tfvars(region, zone, project):
    """Outputs values chosen in Streamlit."""
    return f"""region  = "{region}"
zone    = "{zone}"
project = "{project}"
"""
