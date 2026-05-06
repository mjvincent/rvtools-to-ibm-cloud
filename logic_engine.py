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


def get_catalog_profiles():
    """Returns the list of supported IBM VPC profile names."""
    return [profile['name'] for profile in IBM_VPC_CATALOG]


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


def render_networking_templates(networks_data, vpc_name="migration-vpc", enable_security_groups=True, custom_cidrs=None, address_prefix_strategy="manual", project_name="my-ibm-migration"):
    """
    Renders the networking module main.tf content.
    """
    vpc_safe = vpc_name.replace("-", "_")
    address_preference = (
        "manual" if address_prefix_strategy == "manual"
        else "automatic"
    )

    hcl = f"""
resource "ibm_is_vpc" "{vpc_safe}" {{
  name = "{vpc_name}"
  address_preference = "{address_preference}"
  tags = ["project:{project_name}", "managed-by:rvtools-converter"]
}}
"""

    for i, net in enumerate(networks_data):
        raw_name = net.get('name', 'unknown-net')
        vlan_id = net.get('vlan')
        cidr = custom_cidrs.get(net.get('name'), net.get('cidr', f"10.0.{i+1}.0/24")) if custom_cidrs else net.get('cidr', f"10.0.{i+1}.0/24")

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
  tags            = ["project:{project_name}", "network:{safe_res}", "managed-by:rvtools-converter"]
}}
"""

        if enable_security_groups:
            hcl += f"""
resource "ibm_is_security_group" "sg_{safe_res}" {{
  name = "sg-{safe_res.replace('_', '-') }"
  vpc  = ibm_is_vpc.{vpc_safe}.id
  tags = ["project:{project_name}", "network:{safe_res}", "managed-by:rvtools-converter"]
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
"""

        hcl += f"""
output "{safe_res}_id" {{
  value = ibm_is_subnet.{safe_res}.id
}}
"""

        if enable_security_groups:
            hcl += f"""
output "{safe_res}_sg_id" {{
  value = ibm_is_security_group.sg_{safe_res}.id
}}
"""
    return hcl


def render_networking_variables():
    return """variable \"zone\" { type = string }
variable \"project\" { type = string }
"""


def render_networking_outputs(networks_data, enable_security_groups=True):
    outputs = ""
    for i, net in enumerate(networks_data):
        raw_name = net.get('name', 'unknown-net')
        vlan_id = net.get('vlan')
        safe_res = raw_name.lower().replace(" ", "_").replace("-", "_")
        if vlan_id and str(vlan_id).strip():
            safe_res += f"_vlan_{vlan_id}"

        outputs += f"""
output \"{safe_res}_id\" {{
  value = ibm_is_subnet.{safe_res}.id
}}
"""
        if enable_security_groups:
            outputs += f"""
output \"{safe_res}_sg_id\" {{
  value = ibm_is_security_group.sg_{safe_res}.id
}}
"""
    return outputs


def render_storage_variables():
    return """variable \"zone\" { type = string }
variable \"project\" { type = string }
"""


def render_storage_outputs():
    return """output \"volume_ids\" {
  value = [for v in ibm_is_volume : v.id]
}
"""


def render_storage_templates(final_vms, project_name="my-ibm-migration"):
    content = """# Storage module for VSI volumes\n"""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = vm_n_raw.replace(" ", "_").replace("-", "_")
        tier = vm.get('Override Storage Tier') or vm.get('Storage Tier', '3iops-tier')
        sz = vm.get('Total Storage GB', 10)

        content += f"""
resource "ibm_is_volume" "{safe_n}_vol" {{
  name     = "{safe_n}-vol"
  profile  = "{tier}"
  zone     = var.zone
  capacity = {sz}
  tags     = ["project:{project_name}", "vm:{safe_n}", "managed-by:rvtools-converter"]
}}
"""
    return content


def render_vsi_variables():
    return """variable "zone" { type = string }
variable "project" { type = string }
"""


def render_vsi_templates(final_vms, enable_security_groups=True, project_name="my-ibm-migration"):
    content = """# VSI module for instance definitions\n"""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = vm_n_raw.replace(" ", "_").replace("-", "_")
        prof = vm.get('Override Profile') or vm.get('IBM Profile', 'bx2-2x8')
        r_net = vm.get('Network', 'unknown-net')
        t_sub_res = r_net.lower().replace(" ", "_").replace("-", "_")

        content += f"""
resource "ibm_is_instance" "{safe_n}" {{
  name    = "{safe_n}-vsi"
  profile = "{prof}"
  zone    = var.zone
  primary_network_interface {{
    name   = "eth0"
    subnet = module.networking.{t_sub_res}_id
"""
        if enable_security_groups:
            content += f"""
    security_groups = [module.networking.{t_sub_res}_sg_id]
"""
        content += f"""
  }}
  tags = ["project:{project_name}", "vm:{safe_n}", "managed-by:rvtools-converter"]
}}
"""
    return content


def render_vsi_outputs(final_vms):
    outputs = ""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = vm_n_raw.replace(" ", "_").replace("-", "_")
        outputs += f"""
output "{safe_n}_id" {{
  value = ibm_is_instance.{safe_n}.id
}}
"""
    return outputs


def render_root_main(deployment_target="Plain CLI"):
    hcl = """terraform {
  required_providers {
    ibm = {
      source  = "IBM-Cloud/ibm"
      version = ">= 1.70.0"
    }
  }
"""
    if deployment_target == "Plain CLI":
        hcl += """
  backend "local" {
    path = "terraform.tfstate"
  }
"""
    else:
        hcl += """
  # IBM Schematics manages state for this deployment target.
"""
    hcl += """
}

provider "ibm" {
  region = var.region
}
"""
    hcl += """
module "networking" {
  source  = "./modules/networking"
  zone    = var.zone
  project = var.project
}

module "storage" {
  source  = "./modules/storage"
  zone    = var.zone
  project = var.project
}

module "vsi" {
  source     = "./modules/vsi"
  zone       = var.zone
  project    = var.project
  depends_on = [module.storage, module.networking]
}
"""
    return hcl


def render_root_variables():
    return """variable "ibmcloud_api_key" { sensitive = true }
variable "region" { type = string }
variable "zone" { type = string }
variable "project" { type = string }
"""


def render_root_outputs():
    return """output "project" {
  value = var.project
}
output "region" {
  value = var.region
}
output "zone" {
  value = var.zone
}
"""


def render_terraform_templates(final_vms, unique_nets, region, zone, enable_security_groups=True, vpc_name="migration-vpc", custom_cidrs=None, address_prefix_strategy="manual", deployment_target="Plain CLI", project_name="my-ibm-migration"):
    """Renders the Root main.tf and module contents."""

    root_main = render_root_main(deployment_target)
    root_vars = render_root_variables()
    root_out = render_root_outputs()
    net_hcl = render_networking_templates(unique_nets, vpc_name=vpc_name, enable_security_groups=enable_security_groups, custom_cidrs=custom_cidrs, address_prefix_strategy=address_prefix_strategy, project_name=project_name)
    net_vars = render_networking_variables()
    net_out = render_networking_outputs(unique_nets, enable_security_groups=enable_security_groups)
    storage_main = render_storage_templates(final_vms, project_name=project_name)
    storage_vars = render_storage_variables()
    storage_out = render_storage_outputs()
    vsi_main = render_vsi_templates(final_vms, enable_security_groups=enable_security_groups, project_name=project_name)
    vsi_vars = render_vsi_variables()
    vsi_out = render_vsi_outputs(final_vms)

    return (
        vsi_main,
        root_main,
        storage_main,
        net_hcl,
        root_vars,
        root_out,
        net_vars,
        net_out,
        vsi_vars,
        vsi_out,
        storage_vars,
        storage_out
    )


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
