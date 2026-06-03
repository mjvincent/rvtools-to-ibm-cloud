import csv
import io

from .utils import _clean_value, _normalize_vms, _safe_vm_key


CUTOVER_READINESS_FIELDS = [
    "VM Name",
    "Wave",
    "Cutover Group",
    "Owner",
    "Application",
    "Cutover Status",
    "Blocker Category",
    "Blocker Reason",
    "Recommended Next Action",
]

REQUIRED_PLANNING_FIELDS = [
    ("Wave", "wave"),
    ("Cutover Group", "cutover_group"),
    ("Owner", "owner"),
    ("Application", "application"),
]

READINESS_FIELDS = [
    ("Image Readiness", "Readiness Reasons", "Resolve image readiness blockers."),
    (
        "Migration Readiness",
        "Migration Readiness Reasons",
        "Resolve migration readiness blockers.",
    ),
    ("Memory Readiness", "Memory Readiness Reasons", "Resolve memory readiness blockers."),
    (
        "Network Readiness",
        "Network Readiness Reasons",
        "Resolve network readiness blockers.",
    ),
]

RESOLVED_REMEDIATION_STATUSES = {"resolved", "closed", "complete", "completed"}


def _record_value(record, *keys, default=""):
    for key in keys:
        value = _clean_value(record.get(key))
        if value not in ("", None):
            return value
    return default


def _source_image(record):
    return _record_value(record, "Original Specs") or _safe_vm_key(
        record.get("VM Name")
    )


def _image_status(source_image, image_import_status):
    entry = (image_import_status or {}).get(source_image, {})
    if isinstance(entry, dict):
        return _clean_value(entry.get("import_status")) or _clean_value(
            entry.get("status")
        )
    return _clean_value(entry)


def _base_row(record):
    return {
        "VM Name": _safe_vm_key(record.get("VM Name")),
        "Wave": _record_value(record, "Wave", "wave"),
        "Cutover Group": _record_value(record, "Cutover Group", "cutover_group"),
        "Owner": _record_value(record, "Owner", "owner"),
        "Application": _record_value(record, "Application", "application"),
    }


def _status_for_blockers(blocker_categories):
    if not blocker_categories:
        return "Ready"
    if any(category != "Readiness Review" for category in blocker_categories):
        return "Blocked"
    return "Review"


def _remediation_rows_by_vm(remediation_tracker):
    rows_by_vm = {}
    for blocker_id, blocker in (remediation_tracker or {}).items():
        if not isinstance(blocker, dict):
            continue
        status = _clean_value(blocker.get("status"), "Open")
        if status.strip().lower() in RESOLVED_REMEDIATION_STATUSES:
            continue
        vm_key = _clean_value(blocker.get("vm_key")) or str(blocker_id).split(
            "::", 1
        )[0]
        vm_key = vm_key.split(":", 1)[0]
        if not vm_key:
            continue
        rows_by_vm.setdefault(vm_key, []).append((blocker_id, blocker))
    return rows_by_vm


def build_cutover_readiness_rows(
    final_vms,
    remediation_tracker=None,
    image_import_status=None,
):
    """Build row-level cutover readiness blockers for migration operations."""
    records = _normalize_vms(final_vms)
    remediation_by_vm = _remediation_rows_by_vm(remediation_tracker)
    rows = []

    for record in records:
        vm_key = _record_value(record, "VM Key", "vm_key")
        base = _base_row(record)
        blockers = []

        missing = [
            label
            for label, key in REQUIRED_PLANNING_FIELDS
            if not _record_value(record, label, key)
        ]
        if missing:
            blockers.append((
                "Missing Planning",
                f"Missing required planning fields: {', '.join(missing)}",
                "Complete Wave Planning fields before scheduling cutover.",
            ))

        for status_field, reason_field, action in READINESS_FIELDS:
            status = _clean_value(record.get(status_field), "Review")
            if status.strip().lower() == "blocked":
                reason = _clean_value(record.get(reason_field))
                blockers.append((
                    "Readiness Blocker",
                    f"{status_field}: {reason or 'Blocked'}",
                    action,
                ))
            elif status.strip().lower() == "review":
                reason = _clean_value(record.get(reason_field))
                blockers.append((
                    "Readiness Review",
                    f"{status_field}: {reason or 'Needs review'}",
                    f"Review {status_field.lower()} before cutover.",
                ))

        for blocker_id, blocker in remediation_by_vm.get(vm_key, []):
            blocker_type = _clean_value(
                blocker.get("blocker_type") or blocker.get("type"),
                "Remediation item",
            )
            description = _clean_value(
                blocker.get("blocker_description")
                or blocker.get("description")
                or blocker.get("notes")
            )
            status = _clean_value(blocker.get("status"), "Open")
            blockers.append((
                "Unresolved Remediation",
                f"{blocker_type}: {description or blocker_id} ({status})",
                "Resolve or formally defer the remediation backlog item.",
            ))

        source = _source_image(record)
        import_status = _image_status(source, image_import_status)
        if import_status != "Imported":
            blockers.append((
                "Image Import Pending",
                (
                    f"{source} import status is "
                    f"{import_status or 'not started'}"
                ),
                "Import the source image and record status as Imported.",
            ))

        categories = [category for category, _, _ in blockers]
        cutover_status = _status_for_blockers(categories)
        if blockers:
            for category, reason, action in blockers:
                rows.append({
                    **base,
                    "Cutover Status": cutover_status,
                    "Blocker Category": category,
                    "Blocker Reason": reason,
                    "Recommended Next Action": action,
                })
        else:
            rows.append({
                **base,
                "Cutover Status": "Ready",
                "Blocker Category": "Ready",
                "Blocker Reason": "No cutover blockers found",
                "Recommended Next Action": "Proceed with cutover scheduling.",
            })

    return rows


def summarize_cutover_readiness(rows, group_field):
    """Summarize cutover readiness counts by wave or cutover group."""
    summary = {}
    for row in rows:
        group = _clean_value(row.get(group_field), "Unassigned")
        group_summary = summary.setdefault(group, {
            group_field: group,
            "VMs": set(),
            "Ready": set(),
            "Review": set(),
            "Blocked": set(),
            "Missing Planning": 0,
            "Unresolved Remediation": 0,
            "Image Pending": 0,
        })
        vm_name = row.get("VM Name")
        group_summary["VMs"].add(vm_name)
        status = row.get("Cutover Status")
        if status in ("Ready", "Review", "Blocked"):
            group_summary[status].add(vm_name)
        category = row.get("Blocker Category")
        if category == "Missing Planning":
            group_summary["Missing Planning"] += 1
        elif category == "Unresolved Remediation":
            group_summary["Unresolved Remediation"] += 1
        elif category == "Image Import Pending":
            group_summary["Image Pending"] += 1

    output = []
    for group in sorted(summary):
        item = summary[group]
        output.append({
            group_field: item[group_field],
            "VMs": len(item["VMs"]),
            "Ready": len(item["Ready"]),
            "Review": len(item["Review"]),
            "Blocked": len(item["Blocked"]),
            "Missing Planning": item["Missing Planning"],
            "Unresolved Remediation": item["Unresolved Remediation"],
            "Image Pending": item["Image Pending"],
        })
    return output


def generate_cutover_readiness_csv(
    final_vms,
    remediation_tracker=None,
    image_import_status=None,
):
    """Create the cutover readiness CSV for migration operations teams."""
    rows = build_cutover_readiness_rows(
        final_vms,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CUTOVER_READINESS_FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()
