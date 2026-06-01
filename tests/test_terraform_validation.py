from scripts.validate_terraform_package import (
    _write_sample_package,
    validate_package,
)


def test_terraform_validation_skips_when_binary_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: None)

    assert validate_package(tmp_path) == 0


def test_generated_sample_package_has_valid_module_boundaries(tmp_path):
    _write_sample_package(tmp_path)

    networking_main = (tmp_path / "modules/networking/main.tf").read_text(
        encoding="utf-8"
    )
    networking_outputs = (tmp_path / "modules/networking/outputs.tf").read_text(
        encoding="utf-8"
    )
    vsi_main = (tmp_path / "modules/vsi/main.tf").read_text(encoding="utf-8")
    storage_main = (tmp_path / "modules/storage/main.tf").read_text(
        encoding="utf-8"
    )
    root_main = (tmp_path / "main.tf").read_text(encoding="utf-8")

    assert networking_main.count('output "app_net_id"') == 0
    assert networking_outputs.count('output "app_net_id"') == 1
    assert 'output "subnet_ids"' in networking_outputs
    assert "module.networking." not in vsi_main
    assert 'var.subnet_ids["app_net"]' in vsi_main
    assert "vpc     = var.vpc_id" in vsi_main
    assert 'output "vpc_id"' in networking_outputs
    assert "vpc_id             = module.networking.vpc_id" in root_main
    assert "subnet_ids         = module.networking.subnet_ids" in root_main
    assert 'source  = "IBM-Cloud/ibm"' in networking_main
    assert 'source  = "IBM-Cloud/ibm"' in vsi_main
    assert 'source  = "IBM-Cloud/ibm"' in storage_main
