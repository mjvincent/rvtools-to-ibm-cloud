import csv
import io
import json


REQUIRED_TABS = [
    "vInfo", "vDisk", "vCPU", "vMemory", "vHost", "vCluster", "vNetwork"
]

OPTIONAL_READINESS_TABS = ["vSnapshot", "vTools", "vCD", "vUSB", "vHealth"]

CONFIDENCE_RANK = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


TAB_IMPACTS = {
    "vInfo": "Primary VM inventory, scope, power state, guest OS, and fallback network/storage metadata.",
    "vDisk": "Detailed disk capacity and boot/data disk planning.",
    "vCPU": "CPU demand, contention, throttling, and right-sizing safety signals.",
    "vMemory": "Memory pressure, constraints, and conservative RAM sizing.",
    "vHost": "Host CPU capacity for vCPU-to-pCore and headroom signals.",
    "vCluster": "Cluster capacity for estate-level headroom signals.",
    "vNetwork": "NIC, port group, IP, MAC, switch, and subnet mapping confidence.",
    "vSnapshot": "Snapshot cleanup and migration readiness findings.",
    "vTools": "VMware Tools, heartbeat, app status, and guest operation readiness.",
    "vCD": "Connected ISO/CD media migration blockers.",
    "vUSB": "Attached USB device migration blockers.",
    "vHealth": "RVTools health warnings that may need remediation.",
}


def _status_for(tab_name, sheets, available_sheet_names):
    if tab_name not in available_sheet_names:
        return "Missing"
    df = sheets.get(tab_name)
    if df is None or df.empty:
        return "Empty"
    return "Present"


def _row_count(tab_name, sheets):
    df = sheets.get(tab_name)
    if df is None:
        return 0
    return int(len(df))


def _has_any_column(df, candidates):
    if df is None or df.empty:
        return False
    columns = {str(column).strip() for column in df.columns}
    return any(candidate in columns for candidate in candidates)


def _network_fallback_available(sheets):
    df_vinfo = sheets.get("vInfo")
    if df_vinfo is None or df_vinfo.empty:
        return False
    return any(
        "Network" in str(column) or "Port" in str(column)
        for column in df_vinfo.columns
    )


def _storage_fallback_available(sheets):
    df_vinfo = sheets.get("vInfo")
    if df_vinfo is None or df_vinfo.empty:
        return False
    return _has_any_column(df_vinfo, ["Disks", "Provisioned MiB"])


def _confidence_for_tab(tab_name, status, sheets):
    if status == "Present":
        return "High"
    if tab_name == "vNetwork" and _network_fallback_available(sheets):
        return "Medium"
    if tab_name == "vDisk" and _storage_fallback_available(sheets):
        return "Medium"
    return "Low"


def _tab_record(tab_name, category, sheets, available_sheet_names):
    status = _status_for(tab_name, sheets, available_sheet_names)
    return {
        "tab": tab_name,
        "category": category,
        "status": status,
        "row_count": _row_count(tab_name, sheets),
        "confidence": _confidence_for_tab(tab_name, status, sheets),
        "planning_impact": TAB_IMPACTS.get(tab_name, ""),
    }


def _confidence_min(values):
    if not values:
        return "Low"
    lowest = min(values, key=lambda value: CONFIDENCE_RANK.get(value, 0))
    return lowest


def _domain_confidence(tab_rows, tab_name):
    row = next((item for item in tab_rows if item["tab"] == tab_name), None)
    return row["confidence"] if row else "Low"


def _migration_readiness_confidence(tab_rows):
    optional_rows = [
        row for row in tab_rows if row["category"] == "Optional readiness"
    ]
    present = len([row for row in optional_rows if row["status"] == "Present"])
    if present == len(OPTIONAL_READINESS_TABS):
        return "High"
    if present > 0:
        return "Medium"
    return "Low"


def build_assessment_quality_report(sheets, available_sheet_names):
    """Build advisory workbook coverage and confidence metadata."""
    available_sheet_names = set(available_sheet_names or [])
    tab_rows = [
        _tab_record(tab, "Required", sheets, available_sheet_names)
        for tab in REQUIRED_TABS
    ] + [
        _tab_record(tab, "Optional readiness", sheets, available_sheet_names)
        for tab in OPTIONAL_READINESS_TABS
    ]

    required_present = len([
        row for row in tab_rows
        if row["category"] == "Required" and row["status"] == "Present"
    ])
    optional_present = len([
        row for row in tab_rows
        if row["category"] == "Optional readiness" and row["status"] == "Present"
    ])
    missing_or_empty = len([
        row for row in tab_rows if row["status"] in ["Missing", "Empty"]
    ])

    inventory_confidence = _domain_confidence(tab_rows, "vInfo")
    storage_confidence = _domain_confidence(tab_rows, "vDisk")
    network_confidence = _domain_confidence(tab_rows, "vNetwork")
    memory_confidence = _domain_confidence(tab_rows, "vMemory")
    migration_confidence = _migration_readiness_confidence(tab_rows)
    overall_confidence = _confidence_min([
        inventory_confidence,
        storage_confidence,
        network_confidence,
        memory_confidence,
        migration_confidence,
    ])

    return {
        "schema_version": "1.0",
        "summary": {
            "overall_confidence": overall_confidence,
            "inventory_confidence": inventory_confidence,
            "storage_confidence": storage_confidence,
            "network_confidence": network_confidence,
            "memory_confidence": memory_confidence,
            "migration_readiness_confidence": migration_confidence,
            "required_tabs_present": required_present,
            "required_tabs_total": len(REQUIRED_TABS),
            "optional_readiness_tabs_present": optional_present,
            "optional_readiness_tabs_total": len(OPTIONAL_READINESS_TABS),
            "missing_or_empty_tabs": missing_or_empty,
        },
        "tabs": tab_rows,
    }


def generate_assessment_quality_json(report):
    return json.dumps(report or {}, indent=2, sort_keys=True)


def generate_assessment_quality_csv(report):
    output = io.StringIO()
    fieldnames = [
        "Tab", "Category", "Status", "Row Count", "Confidence",
        "Planning Impact"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in (report or {}).get("tabs", []):
        writer.writerow({
            "Tab": row.get("tab", ""),
            "Category": row.get("category", ""),
            "Status": row.get("status", ""),
            "Row Count": row.get("row_count", 0),
            "Confidence": row.get("confidence", ""),
            "Planning Impact": row.get("planning_impact", ""),
        })
    return output.getvalue()
