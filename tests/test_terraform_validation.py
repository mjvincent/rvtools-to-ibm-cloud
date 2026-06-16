from scripts.validate_terraform_package import (
    _is_provider_download_failure,
    _write_sample_package,
    validate_package,
)


def test_terraform_validation_skips_when_binary_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: None)

    assert validate_package(tmp_path) == 0


def test_validate_package_returns_fmt_failure(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: "terraform")

    def fake_run(command, cwd):
        assert command[1] == "fmt"
        return 3, "fmt failed"

    monkeypatch.setattr("scripts.validate_terraform_package._run", fake_run)

    assert validate_package(tmp_path, run_init_validate=True) == 3


def test_validate_package_provider_failure_is_strict_by_default(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: "terraform")

    def fake_run(command, cwd):
        if command[1] == "fmt":
            return 0, ""
        if command[1] == "init":
            return 1, (
                "Error while installing ibm-cloud/ibm: could not query provider "
                "registry for registry.terraform.io/ibm-cloud/ibm: context "
                "deadline exceeded"
            )
        raise AssertionError(command)

    monkeypatch.setattr("scripts.validate_terraform_package._run", fake_run)

    assert validate_package(tmp_path, run_init_validate=True) == 1
    output = capsys.readouterr().out
    assert "Terraform provider download failed during terraform init." in output
    assert "registry.terraform.io" in output
    assert "strict init validation remains nonzero" in output


def test_validate_package_provider_failure_can_be_allowed(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: "terraform")

    def fake_run(command, cwd):
        if command[1] == "fmt":
            return 0, ""
        if command[1] == "init":
            return 1, (
                "Failed to query available provider packages: could not connect "
                "to registry.terraform.io: lookup registry.terraform.io: no such host"
            )
        raise AssertionError(command)

    monkeypatch.setattr("scripts.validate_terraform_package._run", fake_run)

    assert (
        validate_package(
            tmp_path,
            run_init_validate=True,
            allow_provider_download_failure=True,
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "ALLOW: provider download failure was tolerated" in output


def test_validate_package_non_provider_init_failure_stays_nonzero(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: "terraform")

    def fake_run(command, cwd):
        if command[1] == "fmt":
            return 0, ""
        if command[1] == "init":
            return 2, "Error: invalid provider configuration"
        raise AssertionError(command)

    monkeypatch.setattr("scripts.validate_terraform_package._run", fake_run)

    assert (
        validate_package(
            tmp_path,
            run_init_validate=True,
            allow_provider_download_failure=True,
        )
        == 2
    )
    assert "provider download failed" not in capsys.readouterr().out


def test_validate_package_runs_validate_after_successful_init(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: "terraform")
    commands = []

    def fake_run(command, cwd):
        commands.append(command[1])
        return 0, ""

    monkeypatch.setattr("scripts.validate_terraform_package._run", fake_run)

    assert validate_package(tmp_path, run_init_validate=True) == 0
    assert commands == ["fmt", "init", "validate"]


def test_provider_failure_detection_matches_registry_network_errors():
    assert _is_provider_download_failure(
        'Get "https://registry.terraform.io/.well-known/terraform.json": '
        "dial tcp: lookup registry.terraform.io: no such host"
    )
    assert _is_provider_download_failure(
        "Error while installing ibm-cloud/ibm: Client.Timeout exceeded "
        "while awaiting headers"
    )
    assert not _is_provider_download_failure("Error: invalid Terraform syntax")


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
