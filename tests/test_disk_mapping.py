import json

from logic_engine import (
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_migration_manifest,
    render_terraform_templates,
)


def test_data_disk_volume_and_attachment_generation(disk_vm_record):
    files = render_terraform_templates(
        [disk_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
    )
    vsi_main, root_main, storage_main = files[0], files[1], files[2]

    assert "app_01_hard_disk_1_vol" not in storage_main
    assert "app_01_hard_disk_2_vol" in storage_main
    assert "app_01_hard_disk_2_attach" in vsi_main
    assert "data_volume_ids = module.storage.data_volume_ids" in root_main


def test_custom_image_ids_are_wired_into_vsi_generation(disk_vm_record):
    files = render_terraform_templates(
        [disk_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
    )
    vsi_main, root_main, root_vars, vsi_vars = (
        files[0], files[1], files[4], files[8]
    )

    assert 'variable "custom_image_ids"' in root_vars
    assert "custom_image_ids = var.custom_image_ids" in root_main
    assert 'variable "custom_image_ids"' in vsi_vars
    assert 'image   = var.custom_image_ids["app-01"]' in vsi_main


def test_image_import_tfvars_matches_vsi_image_key(disk_vm_record):
    tfvars = generate_image_import_tfvars([disk_vm_record])

    assert '"app-01" = "replace-with-imported-image-id"' in tfvars
    assert "pass it to Terraform" in tfvars
    assert "wire the map into Terraform" not in tfvars


def test_disk_mapping_exports_boot_and_data_roles(disk_vm_record):
    csv_text = generate_disk_mapping_csv([disk_vm_record])

    assert "covered-by-custom-image" in csv_text
    assert "create-and-attach-volume" in csv_text
    assert "app_01_hard_disk_2_vol" in csv_text


def test_manifest_includes_source_disks_and_target_data_volumes(disk_vm_record):
    manifest = json.loads(
        generate_migration_manifest([disk_vm_record], {"project_name": "demo"})
    )
    vm_record = manifest["virtual_machines"][0]

    assert len(vm_record["source"]["disks"]) == 2
    assert vm_record["target"]["data_volumes"][0]["source_disk"] == "Hard disk 2"
