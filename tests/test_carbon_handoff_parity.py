from prototype.api.handoff_parity import (
    CARBON_CURRENT_EXTRA_FILES,
    CARBON_PARITY_BLOCKERS,
    STREAMLIT_HANDOFF_FILES,
    STREAMLIT_PACKAGE_FILES,
    STREAMLIT_TERRAFORM_FILES,
)


def test_streamlit_package_parity_inventory_covers_expected_handoff_files():
    assert STREAMLIT_HANDOFF_FILES == {
        "migration-manifest.json",
        "assessment-quality.json",
        "assessment-quality.csv",
        "preflight-report.json",
        "preflight-report.csv",
        "pricing-diagnostics.json",
        "pricing-diagnostics.csv",
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
        "planning-state.json",
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
        "image-import-variables.tfvars.example",
        "migration-runbook.md",
    }


def test_streamlit_package_parity_inventory_covers_terraform_files():
    assert {
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "modules/networking/main.tf",
        "modules/vsi/main.tf",
        "modules/storage/main.tf",
    }.issubset(STREAMLIT_TERRAFORM_FILES)


def test_carbon_parity_blockers_are_subset_of_streamlit_package():
    assert CARBON_PARITY_BLOCKERS.issubset(STREAMLIT_PACKAGE_FILES)


def test_carbon_current_extra_files_are_documented():
    assert CARBON_CURRENT_EXTRA_FILES == {"network-plan.json"}

