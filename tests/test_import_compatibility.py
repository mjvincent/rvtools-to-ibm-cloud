def test_handoff_root_imports_still_work():
    from handoff import (
        generate_cutover_readiness_csv,
        generate_migration_manifest,
        generate_planning_state_json,
        generate_vm_mapping_csv,
        image_import_export,
    )
    from handoff.manifest import generate_migration_manifest as package_manifest

    assert generate_migration_manifest is package_manifest
    assert callable(generate_cutover_readiness_csv)
    assert callable(generate_planning_state_json)
    assert callable(generate_vm_mapping_csv)
    assert callable(image_import_export)


def test_models_root_imports_still_work():
    from models import DiskMapping, MigrationVm, NicMapping, clean_value
    from models.migration_vm import MigrationVm as PackageMigrationVm

    assert MigrationVm is PackageMigrationVm
    assert clean_value(" app-01 ") == "app-01"
    assert DiskMapping(disk="Hard disk 1").disk == "Hard disk 1"
    assert NicMapping(network="app-net").network == "app-net"


def test_rvtools_parser_root_imports_still_work():
    from rvtools import build_storage_inventory
    from rvtools.parser import parse_rvtools_workbook as package_parse
    from rvtools.storage import build_storage_inventory as package_storage
    from rvtools.workbook import load_rvtools_sheets as package_load
    from rvtools import load_rvtools_sheets
    from rvtools_parser import normalize_network_name, parse_rvtools_workbook

    assert parse_rvtools_workbook is package_parse
    assert load_rvtools_sheets is package_load
    assert build_storage_inventory is package_storage
    assert normalize_network_name("App Net") == "app_net"


def test_logic_engine_facade_still_exports_public_functions():
    from logic_engine import (
        generate_cutover_readiness_csv,
        generate_migration_manifest,
        generate_planning_state_json,
        render_terraform_templates,
    )

    assert callable(generate_cutover_readiness_csv)
    assert callable(generate_migration_manifest)
    assert callable(generate_planning_state_json)
    assert callable(render_terraform_templates)
