import os

# --- STRATEGY B: ECONOMIC OPTIMIZER CATALOG ---
# Hourly prices based on IBM Cloud US-South (Dallas) standard rates.
# This serves as our "Price-to-Profile" map for right-sizing.
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
    """
    Strategy B: Finds the lowest-priced profile that satisfies
    the required CPU and RAM minimums.
    """
    # Filter for profiles that actually fit the requirements
    candidates = [
        p for p in IBM_VPC_CATALOG
        if p['cpu'] >= target_cpu and p['ram'] >= target_ram
    ]

    if not candidates:
        # Fallback to a high-spec profile if no small fit found
        return {"name": "bx2-16x64", "cpu": 16, "ram": 64, "hourly": 0.912}

    # Sort by price (Low to High)
    optimized = sorted(candidates, key=lambda x: x['hourly'])
    return optimized[0]


def map_vmware_to_ibm_vpc(cpus, memory, usage, region, threshold):
    """
    Maps VMware to IBM VPC with Strategy B: Economic Optimization.
    """
    # Calculate required specs based on actual usage + user threshold
    util_factor = threshold / 100
    needed_cpu = max(1, round(cpus * util_factor))

    # RAM is less flexible; keep 80% of original for safety buffer
    needed_ram = max(2, round((memory / 1024) * 0.8))

    # Get the cheapest fit for the ACTUAL calculated need
    optimized = find_cheapest_fit(needed_cpu, needed_ram)

    # Check if we successfully reduced the footprint
    is_rightsized = optimized['cpu'] < cpus

    return {
        "profile": optimized['name'],
        "hourly": optimized['hourly'],
        "monthly": round(optimized['hourly'] * 730, 2),
        "is_rightsized": is_rightsized
    }


def render_terraform_templates(final_vms, region, zone):
    """
    Renders strings for VSI, VPC, and Storage based on selected VMs.
    Ensures variables are mapped to the correct modular structure.
    """
    vsi_content = f"# VSI Configuration for {region}\n"
    vpc_content = f"# VPC Network Configuration for {zone}\n"
    storage_content = "# Block Storage Volume Configurations\n"

    for vm in final_vms:
        name = str(vm.get('VM Name', 'unknown')).replace(" ", "_")
        profile = vm.get('IBM Profile', 'bx2-2x8')
        tier = vm.get('Storage Tier', '3iops-tier')
        size = vm.get('Total Storage GB', 10)

        vsi_content += f"\n# VM: {name}\nmodule \"vsi_{name}\" {{\n"
        vsi_content += f"  profile = \"{profile}\"\n}}\n"

        storage_content += f"\n# Disk for {name}\nresource \"ibm_is_vol\" "
        storage_content += f"\"{name}_disk\" {{\n  profile = \"{tier}\"\n"
        storage_content += f"  capacity = {size}\n}}\n"

    return vsi_content, vpc_content, storage_content


def generate_variables_hcl():
    """Returns the content for variables.tf."""
    return "variable \"ibmcloud_api_key\" { sensitive = true }\n"


def generate_tfvars(region, zone, project):
    """Returns the content for terraform.tfvars."""
    return f"region = \"{region}\"\nzone = \"{zone}\"\nproject = \"{project}\""


def create_terraform_structure(
    project_name, vsi, vpc, stor, var, tfv
):
    """Creates directory structure with modules for VSI, VPC, and Storage."""
    base_path = project_name
    module_path = os.path.join(base_path, "modules")

    # Create the folder tree (Terraform Standard Module Structure)
    folders = [
        os.path.join(module_path, "vsi"),
        os.path.join(module_path, "vpc"),
        os.path.join(module_path, "storage")
    ]

    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    # 1. Write the Root Files
    with open(os.path.join(base_path, "variables.tf"), "w") as f:
        f.write(var)
    with open(os.path.join(base_path, "terraform.tfvars"), "w") as f:
        f.write(tfv)
    with open(os.path.join(base_path, "main.tf"), "w") as f:
        f.write("# Root Module calls modules/vpc\n" + vpc)

    # 2. Write the Module Files
    with open(os.path.join(module_path, "vsi", "main.tf"), "w") as f:
        f.write(vsi)
    with open(os.path.join(module_path, "storage", "main.tf"), "w") as f:
        f.write(stor)
