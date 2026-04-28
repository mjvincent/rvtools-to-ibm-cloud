import os
import jinja2


def map_vmware_to_ibm_vpc(vcpus, ram_mb, cpu_usage, region, threshold):
    """
    Maps VMware specs to IBM Cloud VPC profiles with right-sizing logic.
    """
    # Simple right-sizing logic: adjust vCPUs based on usage vs threshold
    # If usage is 20% and threshold is 40%, we only need half the vCPUs
    adjusted_vcpus = max(1, int(vcpus * (cpu_usage / threshold)))

    # Logic to select a profile (Simplified for this example)
    # IBM Profiles usually follow: cx2-(vCPU)x(RAM)
    # We'll default to the 'cx2' (Compute Optimized) family
    profile = f"cx2-{adjusted_vcpus}x{int(adjusted_vcpus * 2)}"

    is_rightsized = cpu_usage < threshold

    return {
        "profile": profile,
        "is_rightsized": is_rightsized
    }


def render_terraform_templates(vms, region, zone):
    # Defining the template
    vsi_template_str = """
{% for vm in vms %}
# Compute Resource for {{ vm['VM Name'] }}
resource "ibm_is_instance" "{{ vm['VM Name']|replace(' ', '_') }}_vsi" {
  name    = "{{ vm['VM Name']|replace(' ', '_') }}-vsi"
  profile = "{{ vm['IBM Profile'] }}"
  image   = var.image_id
  zone    = var.zone

  primary_network_interface {
    subnet = var.subnet_id
  }
}

# Storage Resource (Aggregated from vDisk)
resource "ibm_is_volume" "{{ vm['VM Name']|replace(' ', '_') }}_volume" {
  name     = "{{ vm['VM Name']|replace(' ', '_') }}-data-vol"
  profile  = "{{ vm['Storage Tier'] }}"
  zone     = var.zone
  capacity = {{ vm['Total Storage GB']|int }}
}

# Attachment Resource
resource "ibm_is_instance_volume_attachment"
"{{ vm['VM Name']|replace(' ', '_') }}_attach" {
  instance = ibm_is_instance.{{ vm['VM Name']|replace(' ', '_') }}_vsi.id
  volume   = ibm_is_volume.{{ vm['VM Name']|replace(' ', '_') }}_volume.id
  name     = "{{ vm['VM Name']|replace(' ', '_') }}-attachment"
}

{% endfor %}
"""
    # Initialize Jinja environment
    env = jinja2.Environment(loader=jinja2.BaseLoader())

    # FIX F841: Actually use the template string to render
    template = env.from_string(vsi_template_str)
    vsi_h = template.render(vms=vms)

    # Placeholder logic for VPC and Storage (can be expanded later)
    vpc_h = "# VPC resources would be defined here"
    stor_h = "# Additional storage logic if needed"

    return vsi_h, vpc_h, stor_h


def create_terraform_structure(project_name, vsi, vpc, stor, var, tfvars):
    """Creates the directory structure and writes the .tf files."""
    os.makedirs(project_name, exist_ok=True)

    files = {
        "main.tf": f"{vsi}\n{vpc}\n{stor}",
        "variables.tf": var,
        "terraform.tfvars": tfvars
    }

    for filename, content in files.items():
        with open(os.path.join(project_name, filename), "w") as f:
            f.write(content)


def generate_variables_hcl():
    """Returns the HCL string for variables.tf."""
    return """
variable "zone" { type = string }
variable "image_id" { type = string }
variable "subnet_id" { type = string }
"""


def generate_tfvars(region, zone, project_name):
    """Returns the HCL string for terraform.tfvars."""
    return f"""
zone      = "{zone}"
image_id  = "r006-74937749-9831-482d-8f96-3c66f9166989"
subnet_id = "default-subnet-id"
"""
