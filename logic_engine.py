import os
from jinja2 import Template


def map_vmware_to_ibm_vpc(
    vcpus, ram_mb, cpu_usage=100, region="us-south", threshold=40
):
    """
    Upgraded Logic Engine: Now supports dynamic utilization thresholds.
    """
    target_vcpus = vcpus
    # Use the dynamic threshold instead of hardcoded 40
    if cpu_usage < threshold:
        target_vcpus = max(1, int(vcpus / 2))

    ram_gb = ram_mb / 1024
    ratio = ram_gb / target_vcpus

    # Maintain your family logic (cx2, mx2, bx2)
    if ratio <= 2:
        family = "cx2"
    elif ratio >= 8:
        family = "mx2"
    else:
        family = "bx2"

    ibm_profile = f"{family}-{int(target_vcpus)}x{int(ram_gb)}"

    # ... rest of your zone logic stays the same ...
    return {
        "profile": ibm_profile,
        "is_rightsized": target_vcpus < vcpus,
        "family": family
    }


def generate_variables_hcl():
    """
    Generates the variable definitions file.
    """
    return """
variable "ibm_region" {
  description = "The IBM Cloud region"
  type        = string
}

variable "ibm_zone" {
  description = "The specific zone within the region"
  type        = string
}

variable "prefix" {
  description = "A prefix for resource naming"
  type        = string
}

variable "image_id" {
  description = "The ID of the image to use for VSIs"
  type        = string
  default     = "r006-00000000-0000-0000-0000-000000000000"
}
"""


def generate_tfvars(region, zone, project):
    """
    Generates the actual values for the variables.
    """
    # Line split to avoid E501 length error
    output = f'ibm_region = "{region}"\n'
    output += f'ibm_zone   = "{zone}"\n'
    output += f'prefix     = "{project}"\n'
    return output


def create_terraform_structure(project, vsi_h, vpc_h, stor_h, var_h, tfvars_h):
    """
    Creates a best-practice directory structure including variables.
    """
    base_path = f"./{project}"
    module_path = f"{base_path}/modules"

    os.makedirs(f"{module_path}/vsi", exist_ok=True)
    os.makedirs(f"{module_path}/vpc", exist_ok=True)
    os.makedirs(f"{module_path}/storage", exist_ok=True)

    # 1. Write Root Files
    with open(f"{base_path}/variables.tf", "w") as f:
        f.write(var_h)
    with open(f"{base_path}/terraform.tfvars", "w") as f:
        f.write(tfvars_h)

    # The 'Glue' file for modules
    root_main = """
module "vpc" {
  source = "./modules/vpc"
}

module "storage" {
  source = "./modules/storage"
}

module "vsi" {
  source = "./modules/vsi"
  vpc_id = module.vpc.vpc_id
}
"""
    with open(f"{base_path}/main.tf", "w") as f:
        f.write(root_main)

    # 2. Write Module Files
    with open(f"{module_path}/vpc/main.tf", "w") as f:
        f.write(vpc_h)
    with open(f"{module_path}/vsi/main.tf", "w") as f:
        f.write(vsi_h)
    with open(f"{module_path}/storage/main.tf", "w") as f:
        f.write(stor_h)

    return f"Success! Project created at {base_path}"


def render_terraform_templates(vm_list, region, zone):
    """
    Populates templates with VM and Storage data.
    """
    with open("templates/vsi.j2", "r") as f:
        vsi_template = Template(f.read())

    all_vsi_hcl = ""
    all_storage_hcl = ""

    for vm in vm_list:
        name = vm['VM Name'].lower().replace(" ", "-").replace(".", "-")

        all_vsi_hcl += vsi_template.render(
            vm_name_sanitized=name,
            ibm_profile=vm['IBM Profile'],
            zone=zone
        )

        for i, disk in enumerate(vm.get('Disks', [])):
            if i == 0:
                continue

            all_storage_hcl += f"""
resource "ibm_is_volume" "{name}-disk-{i}" {{
  name     = "{name}-disk-{i}"
  profile  = "10iops-tier"
  zone     = "{zone}"
  capacity = {disk['capacity_gb']}
}}
"""

    vpc_hcl = f"""
resource "ibm_is_vpc" "vpc" {{
  name = "migration-vpc"
}}

resource "ibm_is_subnet" "subnet" {{
  name            = "migration-subnet"
  vpc             = ibm_is_vpc.vpc.id
  zone            = "{zone}"
  ipv4_cidr_block = "10.240.0.0/24"
}}
"""
    return all_vsi_hcl, vpc_hcl, all_storage_hcl
