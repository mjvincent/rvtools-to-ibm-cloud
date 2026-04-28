import os


def map_vmware_to_ibm_vpc(
    cpus, memory, usage, region, threshold
):
    """Maps VMware specs to IBM VPC profiles with right-sizing."""
    # Placeholder for your existing mapping logic
    return {"profile": "bx2-2x8", "is_rightsized": True}


def render_terraform_templates(final_vms, region, zone):
    """
    Renders strings for VSI, VPC, and Storage based on selected VMs.
    This replaces the 'missing' function causing the ImportError.
    """
    vsi_content = f"# VSI Configuration for {region}\n"
    vpc_content = f"# VPC Network Configuration for {zone}\n"
    storage_content = "# Block Storage Volume Configurations\n"

    for vm in final_vms:
        name = vm.get('VM Name', 'unknown')
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

    # Create the folder tree
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
