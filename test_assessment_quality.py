import csv
import io
import json

import pandas as pd

from logic_engine import (
    build_assessment_quality_report,
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
    generate_migration_manifest,
)


def _sheet(rows=None, columns=None):
    if rows is not None:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=columns or [])


def _base_sheets():
    return {
        "vInfo": _sheet([{
            "VM": "app-01",
            "Network #1": "app-net",
            "Disks": 1,
            "Provisioned MiB": 81920,
        }]),
        "vDisk": _sheet([{"VM": "app-01", "Capacity MiB": 81920}]),
        "vCPU": _sheet([{"VM": "app-01", "Overall": 100}]),
        "vMemory": _sheet([{"VM": "app-01", "Active": 2048}]),
        "vHost": _sheet([{"Host": "host-01", "Speed": 2400}]),
        "vCluster": _sheet([{"Cluster": "cluster-01", "TotalCpu": 9600}]),
        "vNetwork": _sheet([{"VM": "app-01", "Network": "app-net"}]),
        "vSnapshot": _sheet([{"VM": "app-01", "Snapshot": "snap-1"}]),
        "vTools": _sheet([{"VM": "app-01", "Tools": "toolsOk"}]),
        "vCD": _sheet([{"VM": "app-01", "Connected": False}]),
        "vUSB": _sheet([{"VM": "app-01", "Connected": False}]),
        "vHealth": _sheet([{"Name": "app-01", "Message": "ok"}]),
        "vPartition": _sheet([{
            "VM": "app-01",
            "Disk Key": "2000",
            "Disk": "C:\\",
            "Capacity MiB": 81920,
        }]),
        "vPort": _sheet([{
            "VM": "app-01",
            "Network": "app-net",
            "Switch": "vSwitch0",
        }]),
        "dvPort": _sheet([{
            "VM": "app-01",
            "Network": "db-net",
            "dvSwitch": "dvs-prod",
        }]),
        "vSwitch": _sheet([{"Switch": "vSwitch0"}]),
        "dvSwitch": _sheet([{"dvSwitch": "dvs-prod"}]),
    }


def test_quality_report_high_confidence_when_all_tabs_present():
    sheets = _base_sheets()
    report = build_assessment_quality_report(sheets, sheets.keys())

    assert report["summary"]["overall_confidence"] == "High"
    assert report["summary"]["required_tabs_present"] == 7
    assert report["summary"]["optional_readiness_tabs_present"] == 5
    assert report["summary"]["optional_network_detail_tabs_present"] == 4
    assert report["summary"]["missing_or_empty_tabs"] == 0


def test_quality_report_lowers_migration_confidence_for_missing_optional_tabs():
    sheets = _base_sheets()
    available = [
        "vInfo", "vDisk", "vCPU", "vMemory", "vHost", "vCluster",
        "vNetwork"
    ]
    report = build_assessment_quality_report(sheets, available)

    assert report["summary"]["migration_readiness_confidence"] == "Low"
    assert report["summary"]["overall_confidence"] == "Low"
    assert report["summary"]["optional_readiness_tabs_present"] == 0


def test_quality_report_marks_present_required_empty_as_low_confidence():
    sheets = _base_sheets()
    sheets["vCPU"] = _sheet(columns=["VM", "Overall"])
    report = build_assessment_quality_report(sheets, sheets.keys())
    vcpu = next(row for row in report["tabs"] if row["tab"] == "vCPU")

    assert vcpu["status"] == "Empty"
    assert vcpu["row_count"] == 0
    assert vcpu["confidence"] == "Low"
    assert report["summary"]["required_tabs_present"] == 6


def test_quality_report_uses_vinfo_fallback_for_network_and_storage():
    sheets = _base_sheets()
    available = [
        "vInfo", "vCPU", "vMemory", "vHost", "vCluster",
        "vSnapshot", "vTools", "vCD", "vUSB", "vHealth"
    ]
    report = build_assessment_quality_report(sheets, available)

    assert report["summary"]["storage_confidence"] == "Medium"
    assert report["summary"]["network_confidence"] == "Medium"
    assert report["summary"]["overall_confidence"] == "Medium"


def test_quality_export_generators_have_stable_shape():
    sheets = _base_sheets()
    report = build_assessment_quality_report(sheets, sheets.keys())

    json_report = json.loads(generate_assessment_quality_json(report))
    csv_rows = list(csv.DictReader(
        io.StringIO(generate_assessment_quality_csv(report))
    ))

    assert json_report["schema_version"] == "1.0"
    assert csv_rows[0]["Tab"] == "vInfo"
    assert csv_rows[0]["Category"] == "Required"
    assert csv_rows[0]["Confidence"] == "High"


def test_quality_report_includes_vpartition_as_optional_storage_detail():
    sheets = _base_sheets()
    report = build_assessment_quality_report(sheets, sheets.keys())
    partition = next(row for row in report["tabs"] if row["tab"] == "vPartition")

    assert partition["category"] == "Optional storage detail"
    assert partition["status"] == "Present"
    assert partition["confidence"] == "High"


def test_quality_report_includes_optional_network_detail_tabs():
    sheets = _base_sheets()
    report = build_assessment_quality_report(sheets, sheets.keys())
    vport = next(row for row in report["tabs"] if row["tab"] == "vPort")

    assert vport["category"] == "Optional network detail"
    assert vport["status"] == "Present"
    assert report["summary"]["optional_network_detail_tabs_total"] == 4


def test_quality_report_uses_network_detail_when_vnetwork_missing():
    sheets = _base_sheets()
    sheets["vNetwork"] = _sheet(columns=["VM", "Network"])
    available = [tab for tab in sheets.keys() if tab != "vNetwork"]
    report = build_assessment_quality_report(sheets, available)

    assert report["summary"]["network_confidence"] == "Medium"


def test_manifest_includes_assessment_quality_additively():
    sheets = _base_sheets()
    report = build_assessment_quality_report(sheets, sheets.keys())
    manifest = json.loads(generate_migration_manifest([], {
        "project_name": "demo",
        "assessment_quality": report,
    }))

    assert manifest["handoff_files"]["assessment_quality_json"] == "assessment-quality.json"
    assert manifest["handoff_files"]["assessment_quality_csv"] == "assessment-quality.csv"
    assert manifest["assessment_quality"]["summary"]["overall_confidence"] == "High"


if __name__ == "__main__":
    test_quality_report_high_confidence_when_all_tabs_present()
    test_quality_report_lowers_migration_confidence_for_missing_optional_tabs()
    test_quality_report_marks_present_required_empty_as_low_confidence()
    test_quality_report_uses_vinfo_fallback_for_network_and_storage()
    test_quality_export_generators_have_stable_shape()
    test_quality_report_includes_vpartition_as_optional_storage_detail()
    test_quality_report_includes_optional_network_detail_tabs()
    test_quality_report_uses_network_detail_when_vnetwork_missing()
    test_manifest_includes_assessment_quality_additively()
    print("assessment quality tests ok")
