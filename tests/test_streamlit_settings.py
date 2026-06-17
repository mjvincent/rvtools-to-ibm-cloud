from streamlit_app.settings import (
    SAMPLE_WORKBOOK_RELATIVE_PATH,
    get_sample_workbook_path,
    select_active_workbook,
)


def test_sample_path_resolves_when_workbook_exists(tmp_path):
    sample_path = tmp_path / SAMPLE_WORKBOOK_RELATIVE_PATH
    sample_path.parent.mkdir(parents=True)
    sample_path.write_bytes(b"sample")

    assert get_sample_workbook_path(tmp_path) == sample_path


def test_sample_path_returns_none_when_workbook_missing(tmp_path):
    assert get_sample_workbook_path(tmp_path) is None


def test_uploaded_workbook_takes_precedence_over_sample_path(tmp_path):
    uploaded = object()
    sample_path = tmp_path / SAMPLE_WORKBOOK_RELATIVE_PATH

    active_workbook = select_active_workbook(
        uploaded,
        sample_enabled=True,
        sample_path=sample_path,
    )

    assert active_workbook is uploaded


def test_sample_enabled_uses_sample_path_when_no_upload(tmp_path):
    sample_path = tmp_path / SAMPLE_WORKBOOK_RELATIVE_PATH

    assert select_active_workbook(None, True, sample_path) == sample_path


def test_missing_or_disabled_sample_leaves_no_active_workbook(tmp_path):
    sample_path = tmp_path / SAMPLE_WORKBOOK_RELATIVE_PATH

    assert select_active_workbook(None, False, sample_path) is None
    assert select_active_workbook(None, True, None) is None
