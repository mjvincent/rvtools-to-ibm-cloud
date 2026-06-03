from io import BytesIO

import pandas as pd

from rvtools import RVTOOLS_SHEET_NAMES, load_rvtools_sheets


def test_load_rvtools_sheets_strips_columns_and_tracks_sheet_names():
    workbook = BytesIO()
    with pd.ExcelWriter(workbook) as writer:
        pd.DataFrame(
            [{"VM ": "app-01", " Powerstate": "poweredOn"}]
        ).to_excel(writer, sheet_name="vInfo", index=False)
    workbook.seek(0)

    loaded = load_rvtools_sheets(workbook)

    assert loaded.sheet_names == ["vInfo"]
    assert loaded.sheets["vInfo"].columns.tolist() == ["VM", "Powerstate"]


def test_load_rvtools_sheets_returns_empty_frames_for_missing_tabs():
    workbook = BytesIO()
    with pd.ExcelWriter(workbook) as writer:
        pd.DataFrame([{"VM": "app-01"}]).to_excel(
            writer, sheet_name="vInfo", index=False
        )
    workbook.seek(0)

    loaded = load_rvtools_sheets(workbook)

    assert set(loaded.sheets) == set(RVTOOLS_SHEET_NAMES)
    assert loaded.sheets["vDisk"].empty
