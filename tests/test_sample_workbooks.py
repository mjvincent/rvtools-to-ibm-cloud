from pathlib import Path

import pandas as pd

from rvtools.workbook import RVTOOLS_SHEET_NAMES
from rvtools_parser import parse_rvtools_workbook


SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"


def test_small_sample_workbook_is_complete_and_parseable():
    sample_path = SAMPLES_DIR / "rvtools-small-complete.xlsx"

    workbook = pd.ExcelFile(sample_path)
    assert set(workbook.sheet_names) == set(RVTOOLS_SHEET_NAMES)

    parsed = parse_rvtools_workbook(
        sample_path,
        target_region="us-south",
        utilization_threshold=40,
        generate_security_groups=True,
    )

    assert len(parsed.processed_vms) == 3
    assert {network["name"] for network in parsed.unique_nets} == {
        "sample-app-net",
        "sample-db-net",
        "sample-backup-net",
    }
    assert parsed.disk_details
    assert parsed.nic_details


def test_workshop_sample_workbook_is_available_for_larger_user_tests():
    sample_path = SAMPLES_DIR / "SizingWorkshop-RVTools.xlsx"

    assert sample_path.exists()
    assert sample_path.stat().st_size > 0
