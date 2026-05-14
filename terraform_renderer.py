import json
import math
import re

from models import MigrationVm, as_bool, clean_value


def _clean_value(value, default=""):
    """Return JSON/CSV friendly values from pandas and Streamlit records."""
    return clean_value(value, default)


def _clean_number(value, default=0):
    value = _clean_value(value, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_vm(value):
    if isinstance(value, MigrationVm):
        return value
    return MigrationVm.from_record(value)


def _as_record(value):
    if hasattr(value, "to_record"):
        return value.to_record()
    return value


def _normalize_vms(final_vms):
    return [_as_vm(vm) for vm in final_vms]


def _safe_resource_name(value):
    cleaned = str(_clean_value(value, "unknown")).lower()
    cleaned = re.sub(r"[^0-9a-zA-Z_]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    if not cleaned:
        cleaned = "unknown"
    if cleaned[0].isdigit():
        cleaned = f"r_{cleaned}"
    return cleaned


def _safe_vm_key(value):
    """Create a stable key shared with image import tfvars examples."""
    cleaned = str(_clean_value(value, "unknown-vm"))
    return cleaned.replace('"', '').replace("'", "")


def _vm_disks(vm):
    vm = _as_vm(vm)
    disks = vm.source.disks or vm.disks
    disks = [_as_record(disk) for disk in disks]
    return disks if isinstance(disks, list) else []


def _vm_data_disks(vm):
    return [disk for disk in _vm_disks(vm) if not disk.get('is_boot')]


def _vm_nics(vm):
    vm = _as_vm(vm)
    nics = vm.source.nics or vm.nics
    nics = [_as_record(nic) for nic in nics]
    return nics if isinstance(nics, list) else []


def _connected_nics(vm):
    return [
        nic for nic in _vm_nics(vm)
        if as_bool(nic.get('connected', True), True)
    ]


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
  name               = "{vpc_name}"
  address_preference = "{address_preference}"
  tags               = ["project:{project_name}", "managed-by:rvtools-converter"]
}}
"""

    for i, net in enumerate(networks_data):
        raw_name = net.get('name', 'unknown-net')
        vlan_id = net.get('vlan')
        cidr_key = net.get('cidr_key', net.get('name'))
        cidr = custom_cidrs.get(cidr_key, net.get('cidr', f"10.0.{i+1}.0/24")) if custom_cidrs else net.get('cidr', f"10.0.{i+1}.0/24")

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

output \"data_volume_ids\" {
  value = local.data_volume_ids
}
"""


def render_storage_templates(final_vms, project_name="my-ibm-migration"):
    final_vms = _normalize_vms(final_vms)
    content = """# Storage module for VSI volumes\n"""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        tier = vm.get('Override Storage Tier') or vm.get('Storage Tier', '3iops-tier')
        for idx, disk in enumerate(_vm_data_disks(vm)):
            disk_name = disk.get('disk') or f"disk_{idx + 1}"
            safe_disk = _safe_resource_name(disk_name)
            capacity = math.ceil(_clean_number(disk.get('capacity_gb'), 10))
            capacity = max(10, capacity)

            content += f"""
resource "ibm_is_volume" "{safe_n}_{safe_disk}_vol" {{
  name     = "{safe_n}-{safe_disk}-vol"
  profile  = "{tier}"
  zone     = var.zone
  capacity = {capacity}
  tags     = ["project:{project_name}", "vm:{safe_n}", "disk:{safe_disk}", "managed-by:rvtools-converter"]
}}
"""
    volume_map = []
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        ids = []
        for idx, disk in enumerate(_vm_data_disks(vm)):
            disk_name = disk.get('disk') or f"disk_{idx + 1}"
            safe_disk = _safe_resource_name(disk_name)
            ids.append(f"ibm_is_volume.{safe_n}_{safe_disk}_vol.id")
        values = ", ".join(ids)
        volume_map.append(f'    "{safe_n}" = [{values}]')

    content += "\nlocals {\n  data_volume_ids = {\n"
    content += "\n".join(volume_map)
    content += "\n  }\n}\n"
    return content


def render_vsi_variables():
    return """variable "zone" { type = string }
variable "project" { type = string }
variable "custom_image_ids" {
  type = map(string)

  validation {
    condition = alltrue([
      for image_id in values(var.custom_image_ids) :
      length(trimspace(image_id)) > 0 && trimspace(image_id) != "replace-with-imported-image-id"
    ])
    error_message = "custom_image_ids must contain real imported IBM Cloud VPC custom image IDs, not blank or placeholder values."
  }
}
variable "data_volume_ids" {
  type    = map(list(string))
  default = {}
}
"""


def render_vsi_templates(final_vms, enable_security_groups=True, project_name="my-ibm-migration"):
    final_vms = _normalize_vms(final_vms)
    content = """# VSI module for instance definitions\n"""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
        image_key = _safe_vm_key(vm.get('VM Name'))
        prof = vm.get('Override Profile') or vm.get('IBM Profile', 'bx2-2x8')
        r_net = vm.get('Network', 'unknown-net')
        connected_nics = _connected_nics(vm)
        if connected_nics:
            primary_nic = connected_nics[0]
            secondary_nics = connected_nics[1:]
            t_sub_res = _safe_resource_name(
                primary_nic.get('network') or r_net
            )
        else:
            primary_nic = {}
            secondary_nics = []
            t_sub_res = _safe_resource_name(r_net)

        content += f"""
resource "ibm_is_instance" "{safe_n}" {{
  name    = "{safe_n}-vsi"
  image   = var.custom_image_ids[{json.dumps(image_key)}]
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
"""
        for idx, nic in enumerate(secondary_nics, start=1):
            nic_net = _safe_resource_name(nic.get('network') or r_net)
            content += f"""
  network_interfaces {{
    name   = "eth{idx}"
    subnet = module.networking.{nic_net}_id
"""
            if enable_security_groups:
                content += f"""
    security_groups = [module.networking.{nic_net}_sg_id]
"""
            content += """
  }
"""
        content += f"""
  tags = ["project:{project_name}", "vm:{safe_n}", "managed-by:rvtools-converter"]
}}
"""
        for idx, disk in enumerate(_vm_data_disks(vm)):
            disk_name = disk.get('disk') or f"disk_{idx + 1}"
            safe_disk = _safe_resource_name(disk_name)
            content += f"""
resource "ibm_is_instance_volume_attachment" "{safe_n}_{safe_disk}_attach" {{
  instance = ibm_is_instance.{safe_n}.id
  volume   = var.data_volume_ids["{safe_n}"][{idx}]
  name     = "{safe_n}-{safe_disk}-attachment"
}}
"""
    return content


def render_vsi_outputs(final_vms):
    final_vms = _normalize_vms(final_vms)
    outputs = ""
    for vm in final_vms:
        vm_n_raw = str(vm.get('VM Name', 'unknown'))
        safe_n = _safe_resource_name(vm_n_raw)
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
  source           = "./modules/vsi"
  zone             = var.zone
  project          = var.project
  custom_image_ids = var.custom_image_ids
  data_volume_ids  = module.storage.data_volume_ids
  depends_on       = [module.storage, module.networking]
}
"""
    return hcl


def render_root_variables():
    return """variable "ibmcloud_api_key" { sensitive = true }
variable "region" { type = string }
variable "zone" { type = string }
variable "project" { type = string }
variable "custom_image_ids" {
  type = map(string)

  validation {
    condition = alltrue([
      for image_id in values(var.custom_image_ids) :
      length(trimspace(image_id)) > 0 && trimspace(image_id) != "replace-with-imported-image-id"
    ])
    error_message = "custom_image_ids must contain real imported IBM Cloud VPC custom image IDs, not blank or placeholder values."
  }
}
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
    final_vms = _normalize_vms(final_vms)

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
variable "custom_image_ids" {
  type = map(string)

  validation {
    condition = alltrue([
      for image_id in values(var.custom_image_ids) :
      length(trimspace(image_id)) > 0 && trimspace(image_id) != "replace-with-imported-image-id"
    ])
    error_message = "custom_image_ids must contain real imported IBM Cloud VPC custom image IDs, not blank or placeholder values."
  }
}
"""


def generate_tfvars(region, zone, project):
    """Outputs values chosen in Streamlit."""
    return f"""region  = "{region}"
zone    = "{zone}"
project = "{project}"
"""
