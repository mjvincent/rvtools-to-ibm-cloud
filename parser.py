import os
import pandas as pd
from jinja2 import Template
def get_ibm_profile(vcpus, ram_mb):
    """
    Translates VMware specs to IBM Cloud VPC Profiles.
    IBM Profiles follow a naming convention: 
    [Family][Generation]-[vCPU]x[RAM]
    Example: cx2-4x8 = Compute Family, Gen 2, 4 vCPU, 8GB RAM
    """
    
    # Convert RAM from MB to GB for IBM logic
    ram_gb = ram_mb / 1024

    # Logic: Find the best 'Compute' (cx2) or 'Balanced' (bx2) profile
    if vcpus <= 2 and ram_gb <= 4:
        return "cx2-2x4"
    elif vcpus <= 4 and ram_gb <= 8:
        return "cx2-4x8"
    elif vcpus <= 8 and ram_gb <= 16:
        return "cx2-8x16"
    else:
        # Fallback to a Balanced profile for larger workloads
        return f"bx2-{int(vcpus)}x{int(ram_gb)}"

# Test the logic
print(f"A 4 vCPU / 8GB VM becomes: {get_ibm_profile(4, 8192)}")
import os

def create_terraform_structure(project_name, vsi_content, vpc_content):
    """
    Creates a best-practice directory structure and writes the HCL files.
    """
    # 1. Define paths
    base_path = f"./{project_name}"
    module_path = f"{base_path}/modules"
    
    # 2. Create the directories
    os.makedirs(f"{module_path}/vsi", exist_ok=True)
    os.makedirs(f"{module_path}/vpc", exist_ok=True)
    
    # 3. Write the Networking piece (VPC)
    with open(f"{module_path}/vpc/main.tf", "w") as f:
        f.write(vpc_content)
        
    # 4. Write the Compute piece (VSI)
    with open(f"{module_path}/vsi/main.tf", "w") as f:
        f.write(vsi_content)
        
    # 5. Write the Root file (The 'Glue')
    root_main = """
module "vpc" {
  source = "./modules/vpc"
}

module "vsi" {
  source = "./modules/vsi"
  vpc_id = module.vpc.vpc_id
}
    """
    with open(f"{base_path}/main.tf", "w") as f:
        f.write(root_main)

    return f"Success! Project created at {base_path}"