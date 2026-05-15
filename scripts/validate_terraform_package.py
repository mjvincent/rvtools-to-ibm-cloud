#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from assessment_quality import (
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
)
from handoff import (
    generate_image_import_tfvars,
    generate_migration_manifest,
    generate_migration_runbook,
)
from terraform_renderer import generate_tfvars, render_terraform_templates


SAMPLE_VM = {
    "VM Key": "vm-001",
    "VM Name": "app-01",
    "Network": "app-net",
    "IBM Profile": "bx2-2x8",
    "Storage Tier": "3iops-tier",
    "Image Readiness": "Review",
    "Migration Readiness": "Ready",
    "Memory Readiness": "Ready",
    "Disk Details": [
        {"disk": "Hard disk 1", "capacity_gb": 80, "is_boot": True},
        {"disk": "Hard disk 2", "capacity_gb": 120, "is_boot": False},
    ],
    "Network Details": [
        {"label": "Network adapter 1", "network": "app-net", "connected": True}
    ],
}

SAMPLE_NETWORKS = [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}]


def _write_sample_package(package_dir):
    files = render_terraform_templates(
        [SAMPLE_VM],
        SAMPLE_NETWORKS,
        "us-south",
        "us-south-1",
        True,
        "migration-vpc",
        None,
        "manual",
        "Plain CLI",
        "sample-migration",
    )
    (
        vsi, root_main, stor, net, root_vars, root_out, net_vars, net_out,
        vsi_vars, vsi_out, stor_vars, stor_out,
    ) = files
    contents = {
        "main.tf": root_main,
        "variables.tf": root_vars,
        "outputs.tf": root_out,
        "terraform.tfvars": generate_tfvars(
            "us-south", "us-south-1", "sample-migration"
        ),
        "modules/networking/main.tf": net,
        "modules/networking/variables.tf": net_vars,
        "modules/networking/outputs.tf": net_out,
        "modules/vsi/main.tf": vsi,
        "modules/vsi/variables.tf": vsi_vars,
        "modules/vsi/outputs.tf": vsi_out,
        "modules/storage/main.tf": stor,
        "modules/storage/variables.tf": stor_vars,
        "modules/storage/outputs.tf": stor_out,
        "migration-manifest.json": generate_migration_manifest(
            [SAMPLE_VM],
            {
                "project_name": "sample-migration",
                "target_region": "us-south",
                "target_zone": "us-south-1",
                "vpc_name": "migration-vpc",
            },
        ),
        "assessment-quality.json": generate_assessment_quality_json({}),
        "assessment-quality.csv": generate_assessment_quality_csv({}),
        "image-import-variables.tfvars.example": generate_image_import_tfvars(
            [SAMPLE_VM]
        ),
        "migration-runbook.md": generate_migration_runbook({
            "project_name": "sample-migration",
            "target_region": "us-south",
            "target_zone": "us-south-1",
            "vpc_name": "migration-vpc",
        }),
    }
    for relative_path, content in contents.items():
        path = package_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _extract_zip(zip_path, package_dir):
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(package_dir)


def _run(command, cwd):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    return result.returncode


def validate_package(package_dir, run_init_validate=False):
    terraform = shutil.which("terraform")
    if not terraform:
        print("SKIP: terraform executable not found.")
        return 0

    fmt_code = _run([terraform, "fmt", "-check", "-recursive"], package_dir)
    if fmt_code:
        return fmt_code

    if not run_init_validate:
        print("SKIP: terraform init/validate not requested.")
        return 0

    init_code = _run([terraform, "init", "-backend=false"], package_dir)
    if init_code:
        return init_code
    return _run([terraform, "validate"], package_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Validate a generated Terraform package."
    )
    parser.add_argument("--zip", type=Path, help="Existing Terraform package ZIP.")
    parser.add_argument("--dir", type=Path, help="Existing extracted package.")
    parser.add_argument(
        "--init-validate",
        action="store_true",
        help="Run terraform init -backend=false and terraform validate.",
    )
    args = parser.parse_args()

    if args.zip and args.dir:
        parser.error("Use only one of --zip or --dir.")

    with tempfile.TemporaryDirectory(prefix="rvtools-tf-validate-") as tmp:
        package_dir = Path(tmp) / "package"
        package_dir.mkdir()
        if args.zip:
            _extract_zip(args.zip, package_dir)
        elif args.dir:
            package_dir = args.dir
        else:
            _write_sample_package(package_dir)
        return validate_package(package_dir, args.init_validate)


if __name__ == "__main__":
    sys.exit(main())
