import json
from datetime import datetime, timezone

from .utils import _clean_value, _normalize_vms, _safe_vm_key


PLANNING_STATE_SCHEMA_VERSION = "1.0"

WAVE_STATE_COLUMNS = [
    "Wave",
    "Cutover Group",
    "Owner",
    "Application",
    "Priority",
    "Dependency Group",
]


def _record_value(record, *keys):
    for key in keys:
        value = _clean_value(record.get(key))
        if value not in ("", None):
            return value
    return ""


def _wave_row(record):
    return {
        "VM Key": _record_value(record, "VM Key", "vm_key")
        or _safe_vm_key(record.get("VM Name")),
        "VM Name": _safe_vm_key(record.get("VM Name")),
        "Wave": _record_value(record, "Wave", "wave"),
        "Cutover Group": _record_value(record, "Cutover Group", "cutover_group"),
        "Owner": _record_value(record, "Owner", "owner"),
        "Application": _record_value(record, "Application", "application"),
        "Priority": _record_value(record, "Priority", "priority"),
        "Dependency Group": _record_value(
            record, "Dependency Group", "dependency_group"
        ),
    }


def build_planning_state(
    final_vms,
    remediation_tracker=None,
    image_import_status=None,
    metadata=None,
):
    """Build a JSON-serializable planning-state bundle."""
    final_vms = _normalize_vms(final_vms)
    metadata = metadata or {}
    return {
        "schema_version": PLANNING_STATE_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "project_name": _clean_value(metadata.get("project_name")),
            "target_region": _clean_value(metadata.get("target_region")),
            "target_zone": _clean_value(metadata.get("target_zone")),
        },
        "wave_planning": [_wave_row(record) for record in final_vms],
        "remediation_tracker": remediation_tracker or {},
        "image_import_status": image_import_status or {},
    }


def generate_planning_state_json(
    final_vms,
    remediation_tracker=None,
    image_import_status=None,
    metadata=None,
):
    """Create a stable JSON planning-state export."""
    state = build_planning_state(
        final_vms,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
        metadata=metadata,
    )
    return json.dumps(state, indent=2, sort_keys=True)


def load_planning_state_json(source):
    """Load planning-state JSON from text, bytes, or an uploaded file."""
    if hasattr(source, "read"):
        source = source.read()
    if isinstance(source, bytes):
        source = source.decode("utf-8")
    if not isinstance(source, str):
        raise ValueError("Planning state must be JSON text or bytes.")
    state = json.loads(source)
    if not isinstance(state, dict):
        raise ValueError("Planning state must be a JSON object.")
    if state.get("schema_version") != PLANNING_STATE_SCHEMA_VERSION:
        raise ValueError("Unsupported planning state schema version.")
    return state


def extract_remediation_tracker(state):
    """Return remediation tracker data from a planning-state bundle."""
    tracker = state.get("remediation_tracker", {})
    return tracker if isinstance(tracker, dict) else {}


def extract_image_import_status(state):
    """Return image import status data from a planning-state bundle."""
    status = state.get("image_import_status", {})
    return status if isinstance(status, dict) else {}
