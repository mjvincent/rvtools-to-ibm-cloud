from dataclasses import dataclass

import pandas as pd


RVTOOLS_SHEET_NAMES = [
    "vInfo",
    "vDisk",
    "vCPU",
    "vMemory",
    "vHost",
    "vCluster",
    "vNetwork",
    "vSnapshot",
    "vTools",
    "vCD",
    "vUSB",
    "vHealth",
    "vPartition",
    "vPort",
    "dvPort",
    "vSwitch",
    "dvSwitch",
]


@dataclass
class LoadedRvtoolsWorkbook:
    sheets: dict
    sheet_names: list


def load_rvtools_sheets(uploaded_file):
    """Load known RVTools sheets and normalize column whitespace."""
    xls = pd.ExcelFile(uploaded_file)
    sheets = {}
    for sheet_name in RVTOOLS_SHEET_NAMES:
        if sheet_name in xls.sheet_names:
            sheet_df = pd.read_excel(xls, sheet_name=sheet_name)
        else:
            sheet_df = pd.DataFrame()
        if not sheet_df.empty:
            sheet_df.columns = sheet_df.columns.str.strip()
        sheets[sheet_name] = sheet_df
    return LoadedRvtoolsWorkbook(sheets=sheets, sheet_names=xls.sheet_names)
