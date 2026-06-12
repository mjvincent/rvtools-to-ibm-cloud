import io
import zipfile

from streamlit_app.package_builder import (
    build_terraform_bundle,
    generate_terraform_operator_readme,
)


def _context(**overrides):
    context = {
        "project_name": "demo",
        "target_region": "us-south",
        "target_zone": "us-south-1",
        "vpc_name": "demo-vpc",
        "deployment_target": "Plain CLI",
    }
    context.update(overrides)
    return context


def _vm():
    return {
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Network": "app-net",
        "Guest OS": "Linux",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "5iops-tier",
        "Subnet": "module.networking.app_net_id",
        "Security Group": "module.networking.app_net_sg_id",
        "Disk Count": 1,
        "Total Storage GB": 100,
        "Original Specs": "rhel-8-template",
        "Image Readiness": "Ready",
        "Migration Readiness": "Ready",
        "Memory Readiness": "Ready",
        "Network Readiness": "Ready",
    }


def _bundle(deployment_target="Plain CLI"):
    return build_terraform_bundle(
        [_vm()],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
        True,
        "demo-vpc",
        {},
        "manual",
        deployment_target,
        "demo",
        "10.10.0.0/24",
        {
            "mode": "static",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
        },
        {},
        {},
        [],
        {},
        {"rhel-8-template": {"import_status": "Imported"}},
    )


def test_operator_readme_includes_local_cli_workflow():
    readme = generate_terraform_operator_readme(_context())

    assert "# Terraform Operator README" in readme
    assert "terraform fmt -check -recursive" in readme
    assert "terraform init" in readme
    assert "terraform validate" in readme
    assert "terraform plan -var-file=<populated-image-vars.tfvars>" in readme
    assert "Local CLI Notes" in readme
    assert "IBM Schematics Notes" not in readme
    assert "does not execute" in readme


def test_operator_readme_includes_schematics_notes():
    readme = generate_terraform_operator_readme(
        _context(deployment_target="IBM Schematics")
    )

    assert "IBM Schematics Notes" in readme
    assert "omits a\nlocal backend block" in readme
    assert "Local CLI Notes" not in readme


def test_terraform_bundle_includes_operator_readme():
    bundle = _bundle()

    with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
        names = set(zf.namelist())
        readme = zf.read("README.md").decode()

    assert "README.md" in names
    assert "main.tf" in names
    assert "preflight-report.csv" in names
    assert "image-import-variables.tfvars.example" in names
    assert "Required Reviews Before `terraform plan`" in readme
    assert "cutover-readiness.csv" in readme


def test_schematics_bundle_readme_differs_from_plain_cli():
    plain = _bundle("Plain CLI")
    schematics = _bundle("IBM Schematics")

    with zipfile.ZipFile(io.BytesIO(plain)) as zf:
        plain_readme = zf.read("README.md").decode()
    with zipfile.ZipFile(io.BytesIO(schematics)) as zf:
        schematics_readme = zf.read("README.md").decode()

    assert "Local CLI Notes" in plain_readme
    assert "IBM Schematics Notes" in schematics_readme
