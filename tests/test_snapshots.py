import json

from handoff import (
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_migration_manifest,
)
from terraform_renderer import render_terraform_templates


def test_image_import_tfvars_snapshot(disk_vm_record, assert_matches_snapshot):
    actual = generate_image_import_tfvars([disk_vm_record])

    assert_matches_snapshot("image_import_tfvars.txt", actual)


def test_vsi_module_snapshot(disk_vm_record, assert_matches_snapshot):
    files = render_terraform_templates(
        [disk_vm_record],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
    )

    assert_matches_snapshot("vsi_module.tf", files[0])


def test_disk_mapping_csv_snapshot(disk_vm_record, assert_matches_snapshot):
    actual = generate_disk_mapping_csv([disk_vm_record])

    assert_matches_snapshot("disk_mapping.csv", actual)


def test_migration_manifest_snapshot(sample_vm_model, assert_matches_snapshot):
    manifest = generate_migration_manifest(
        [sample_vm_model],
        {
            "project_name": "demo",
            "target_region": "us-south",
            "target_zone": "us-south-1",
            "vpc_name": "demo-vpc",
            "pricing_mode": "static",
            "pricing_source": "static",
            "pricing_confidence": "fallback-static",
        },
    )
    actual = json.dumps(json.loads(manifest), indent=2, sort_keys=True) + "\n"

    assert_matches_snapshot("migration_manifest.json", actual)
