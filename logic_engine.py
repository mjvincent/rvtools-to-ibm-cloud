import os
import pandas as pd
from jinja2 import Template

def generate_tfvars(project_name, region, zone):
    content = f"""
ibm_region = "{region}"
ibm_zone   = "{zone}"
project_prefix = "{project_name}"
"""
    return content

def map_vmware_to_ibm_vpc(vcpus, ram_mb, region="us-south"):
    """
    Core Logic Engine: Translates VMware specs to IBM VPC Profiles
    and assigns appropriate Data Centers (Zones).
    """
    # 1. Convert RAM to GB for IBM calculations
    ram_gb = ram_mb / 1024

    # 2. Assign the VSI Profile Family
    # Strategy: Use 'Balanced' (bx2) as default, 'Compute' (cx2) if low RAM ratio
    ratio = ram_gb / vcpus
    
    if ratio <= 2:
        family = "cx2"  # Compute Optimized
    elif ratio >= 8:
        family = "mx2"  # Memory Optimized
    else:
        family = "bx2"  # Balanced

    # 3. Match to nearest Official IBM Profile
    ibm_profile = f"{family}-{int(vcpus)}x{int(ram_gb)}"

    # 4. Data Center / Zone Logic
    zones = {
        "us-south": ["us-south-1", "us-south-2", "us-south-3"],
        "us-east": ["us-east-1", "us-east-2", "us-east-3"],
        "eu-gb": ["eu-gb-1", "eu-gb-2", "eu-gb-3"],
        "jp-tok": ["jp-tok-1", "jp-tok-2", "jp-tok-3"]
    }
    
    selected_zone = zones.get(region, [f"{region}-1"])[0]

    return {
        "profile": ibm_profile,
        "region": region,
        "zone": selected_zone,
        "family": family
    }

def create_terraform_structure(project_name, vsi_content, vpc_content, storage_content):
    base_path = f"./{project_name}"
    module_path = f"{base_path}/modules"
    
    # Add storage directory
    os.makedirs(f"{module_path}/vsi", exist_ok=True)
    os.makedirs(f"{module_path}/vpc", exist_ok=True)
    os.makedirs(f"{module_path}/storage", exist_ok=True) # New Folder!
    
    with open(f"{module_path}/vpc/main.tf", "w") as f:
        f.write(vpc_content)
    with open(f"{module_path}/vsi/main.tf", "w") as f:
        f.write(vsi_content)
    with open(f"{module_path}/storage/main.tf", "w") as f: # New File!
        f.write(storage_content)
        
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
def render_terraform_templates(vm_list, region, zone):
    with open("templates/vsi.j2", "r") as f:
        vsi_template = Template(f.read())
    
    all_vsi_hcl = ""
    all_storage_hcl = ""

    for vm in vm_list:
        sanitized_name = vm['VM Name'].lower().replace(" ", "-").replace(".", "-")
        
        # 1. Generate VSI HCL
        all_vsi_hcl += vsi_template.render(
            vm_name_sanitized = sanitized_name,
            ibm_profile = vm['IBM Profile'],
            zone = zone
        )

        # 2. Loop through the ACTUAL disks we found for this VM
        for i, disk in enumerate(vm.get('Disks', [])):
            # We skip the first disk if it's the boot drive (IBM handles boot disks in the VSI resource)
            if i == 0: continue 
            
            all_storage_hcl += f"""
resource "ibm_is_volume" "{sanitized_name}-disk-{i}" {{
  name     = "{sanitized_name}-disk-{i}"
  profile  = "10iops-tier" # Standard IBM storage tier
  zone     = "{zone}"
  capacity = {disk['capacity_gb']}
}}
"""
    # ... (rest of the VPC HCL code)

    # 3. Dynamic VPC HCL (No longer hardcoded!)
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