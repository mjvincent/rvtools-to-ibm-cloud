"""Expected handoff artifacts for Carbon-to-Streamlit export parity."""

STREAMLIT_TERRAFORM_FILES = {
    "README.md",
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "terraform.tfvars",
    "modules/networking/main.tf",
    "modules/networking/variables.tf",
    "modules/networking/outputs.tf",
    "modules/vsi/main.tf",
    "modules/vsi/variables.tf",
    "modules/vsi/outputs.tf",
    "modules/storage/main.tf",
    "modules/storage/variables.tf",
    "modules/storage/outputs.tf",
}

STREAMLIT_HANDOFF_FILES = {
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

STREAMLIT_PACKAGE_FILES = STREAMLIT_TERRAFORM_FILES | STREAMLIT_HANDOFF_FILES

CARBON_MODULAR_TERRAFORM_FILES = {
    "README.md",
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "provider.tf",
    "versions.tf",
    "terraform.tfvars.example",
    "modules/networking/main.tf",
    "modules/networking/variables.tf",
    "modules/networking/outputs.tf",
    "modules/vsi/main.tf",
    "modules/vsi/variables.tf",
    "modules/vsi/outputs.tf",
    "modules/storage/main.tf",
    "modules/storage/variables.tf",
    "modules/storage/outputs.tf",
}

CARBON_CURRENT_EXTRA_FILES = {
    "network-plan.json",
}

CARBON_PARITY_BLOCKERS = {
    "migration-manifest.json",
    "decision-audit.csv",
    "remediation-backlog.csv",
    "image-import-plan.csv",
    "cutover-readiness.csv",
    "planning-state.json",
    "preflight-report.json",
    "preflight-report.csv",
    "pricing-diagnostics.json",
    "pricing-diagnostics.csv",
    "migration-runbook.md",
    "image-import-variables.tfvars.example",
}
