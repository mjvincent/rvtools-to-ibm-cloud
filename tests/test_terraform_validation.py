from scripts.validate_terraform_package import validate_package


def test_terraform_validation_skips_when_binary_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("scripts.validate_terraform_package.shutil.which", lambda _: None)

    assert validate_package(tmp_path) == 0
