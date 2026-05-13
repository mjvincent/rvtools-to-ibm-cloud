"""Compatibility facade for the refactored migration engine modules.

Existing tests and callers import from logic_engine.py. The implementation now
lives in focused modules for assessments, sizing, Terraform rendering, and
migration handoff generation.
"""

from assessments import (
    IMAGE_MAX_GB,
    IMAGE_MIN_GB,
    MEMORY_PRESSURE_MIB,
    SNAPSHOT_BLOCK_SIZE_MIB,
    assess_image_readiness,
    assess_memory_readiness,
    make_readiness_finding,
    summarize_migration_readiness,
)
from assessment_quality import (
    build_assessment_quality_report,
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
)
from handoff import (
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    generate_memory_readiness_csv,
    generate_migration_manifest,
    generate_migration_runbook,
    generate_nic_mapping_csv,
    generate_partition_mapping_csv,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
)
from sizing import (
    IBM_VPC_CATALOG,
    find_cheapest_fit,
    get_catalog_profiles,
    map_vmware_to_ibm_vpc,
    recommend_storage_tier,
)
from terraform_renderer import (
    generate_tfvars,
    generate_variables_hcl,
    render_networking_outputs,
    render_networking_templates,
    render_networking_variables,
    render_root_main,
    render_root_outputs,
    render_root_variables,
    render_storage_outputs,
    render_storage_templates,
    render_storage_variables,
    render_terraform_templates,
    render_vsi_outputs,
    render_vsi_templates,
    render_vsi_variables,
)

__all__ = [
    "IMAGE_MAX_GB",
    "IMAGE_MIN_GB",
    "MEMORY_PRESSURE_MIB",
    "SNAPSHOT_BLOCK_SIZE_MIB",
    "IBM_VPC_CATALOG",
    "assess_image_readiness",
    "assess_memory_readiness",
    "build_assessment_quality_report",
    "generate_assessment_quality_csv",
    "generate_assessment_quality_json",
    "make_readiness_finding",
    "summarize_migration_readiness",
    "find_cheapest_fit",
    "get_catalog_profiles",
    "map_vmware_to_ibm_vpc",
    "recommend_storage_tier",
    "generate_disk_mapping_csv",
    "generate_image_import_tfvars",
    "generate_memory_readiness_csv",
    "generate_migration_manifest",
    "generate_migration_runbook",
    "generate_nic_mapping_csv",
    "generate_partition_mapping_csv",
    "generate_readiness_findings_csv",
    "generate_vm_mapping_csv",
    "generate_tfvars",
    "generate_variables_hcl",
    "render_networking_outputs",
    "render_networking_templates",
    "render_networking_variables",
    "render_root_main",
    "render_root_outputs",
    "render_root_variables",
    "render_storage_outputs",
    "render_storage_templates",
    "render_storage_variables",
    "render_terraform_templates",
    "render_vsi_outputs",
    "render_vsi_templates",
    "render_vsi_variables",
]
