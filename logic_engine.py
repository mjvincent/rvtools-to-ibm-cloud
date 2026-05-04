import os

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


def render_terraform_templates(final_vms, region, zone):
    """Renders the Root main.tf and module contents."""

    # --- ROOT main.tf ---
    vpc_content = f"""# Root Module: IBM Cloud Infrastructure Deployment
# Region: {region}

terraform {{
  required_providers {{
    ibm = {{
      source  = "IBM-Cloud/ibm"
      version = ">= 1.70.0"
    }}
  }}
}}

provider "ibm" {{
  ibmcloud_api_key = var.ibmcloud_api_key
  region           = var.region
}}

module "storage" {{
  source = "./modules/storage"
  zone   = var.zone
}}

module "vsi" {{
  source     = "./modules/vsi"
  zone       = var.zone
  depends_on = [module.storage]
}}
"""

    vsi_content = f"# VSI Module Configuration for {zone}\n"
    storage_content = f"# Block Storage Module for {zone}\n"

    for vm in final_vms:
        # Fixed the line-break issue here
        vm_name_raw = str(vm.get('VM Name', 'unknown'))
        safe_name = vm_name_raw.replace(" ", "_").replace("-", "_")

        profile = vm.get('IBM Profile', 'bx2-2x8')
        tier = vm.get('Storage Tier', '3iops-tier')
        size = vm.get('Total Storage GB', 10)

        vsi_content += f"""
resource "ibm_is_instance" "{safe_name}" {{
  name    = "{safe_name}-vsi"
  profile = "{profile}"
  zone    = var.zone
  primary_network_interface {{
    name = "eth0"
  }}
}}
"""
        storage_content += f"""
resource "ibm_is_volume" "{safe_name}_vol" {{
  name     = "{safe_name}-vol"
  profile  = "{tier}"
  zone     = var.zone
  capacity = {size}
}}
"""

    return vsi_content, vpc_content, storage_content


def generate_variables_hcl():
    """Returns root variables definition."""
    return """variable "ibmcloud_api_key" { sensitive = true }
variable "region" { type = string }
variable "zone" { type = string }
variable "project" { type = string }
"""


def generate_tfvars(region, zone, project):
    """Outputs the specific values chosen in the Streamlit UI."""
    return f"""region  = "{region}"
zone    = "{zone}"
project = "{project}"
"""


def create_terraform_structure(project_name, vsi, vpc, stor, var, tfv):
    """Creates directory structure with modules."""
    base_path = project_name
    module_path = os.path.join(base_path, "modules")

    folders = [
        os.path.join(module_path, "vsi"),
        os.path.join(module_path, "vpc"),
        os.path.join(module_path, "storage")
    ]

    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    with open(os.path.join(base_path, "variables.tf"), "w") as f:
        f.write(var)
    with open(os.path.join(base_path, "terraform.tfvars"), "w") as f:
        f.write(tfv)
    with open(os.path.join(base_path, "main.tf"), "w") as f:
        f.write(vpc)

    with open(os.path.join(module_path, "vsi", "main.tf"), "w") as f:
        f.write(vsi)
    with open(os.path.join(module_path, "storage", "main.tf"), "w") as f:
        f.write(stor)
