import math

from models import clean_value

IMAGE_MAX_GB = 250
IMAGE_MIN_GB = 10
SNAPSHOT_BLOCK_SIZE_MIB = 10240
MEMORY_PRESSURE_MIB = 1024


def _clean_value(value, default=""):
    """Return JSON/CSV friendly values from pandas and Streamlit records."""
    return clean_value(value, default)


def _clean_text(value):
    return str(_clean_value(value)).strip()


def _clean_number(value, default=0):
    value = _clean_value(value, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def assess_image_readiness(guest_os, firmware, boot_disk_gb,
                           disk_count, power_state):
    """
    Assess whether VM metadata is ready for IBM Cloud VPC image planning.

    This is advisory only. It does not automate conversion, COS upload, image
    import, or Terraform provisioning from custom images.
    """
    reasons = []
    blockers = []
    guest_os_text = _clean_text(guest_os)
    firmware_text = _clean_text(firmware)
    power_text = _clean_text(power_state).lower()
    boot_gb = round(_clean_number(boot_disk_gb, 0), 2)
    disks = int(_clean_number(disk_count, 0))
    os_lower = guest_os_text.lower()

    if "windows" in os_lower:
        guest_customization = "cloudbase-init required"
    elif any(token in os_lower for token in [
        "linux", "ubuntu", "debian", "red hat", "rhel",
        "centos", "suse", "oracle"
    ]):
        guest_customization = "cloud-init required"
    elif guest_os_text:
        guest_customization = "validate guest initialization"
        reasons.append("Guest OS not recognized by rule; confirm IBM OS value")
    else:
        guest_customization = "unknown"
        reasons.append("Guest OS missing; confirm IBM OS value")

    if not firmware_text:
        reasons.append("Firmware missing; confirm BIOS or EFI boot mode")

    if boot_gb <= 0:
        reasons.append("Boot disk size missing; confirm image size")
    elif boot_gb > IMAGE_MAX_GB:
        blockers.append("Boot disk exceeds IBM Cloud custom image 250 GB limit")
    elif boot_gb < IMAGE_MIN_GB:
        reasons.append("Boot disk below 10 GB minimum; IBM rounds up to 10 GB")

    if disks > 1:
        reasons.append("Multiple disks detected; map data disks separately")

    if power_text == "poweredoff":
        reasons.append("VM is powered off; validate source state before export")

    if blockers:
        status = "Blocked"
    elif reasons:
        status = "Review"
    else:
        status = "Ready"
        reasons.append(
            "No metadata blockers found; convert to qcow2/vhd and stage in COS"
        )

    return {
        "status": status,
        "reasons": "; ".join(blockers + reasons),
        "firmware": firmware_text,
        "boot_disk_gb": boot_gb,
        "guest_customization": guest_customization,
        "required_image_format": "qcow2 or vhd",
        "requires_cos_staging": True,
        "max_custom_image_gb": IMAGE_MAX_GB,
        "min_custom_image_gb": IMAGE_MIN_GB,
    }


def _round_memory_mib(value):
    memory = max(2048, _clean_number(value, 2048))
    return int(math.ceil(memory / 1024) * 1024)


def assess_memory_readiness(configured_mib, active_mib, consumed_mib,
                            ballooned_mib, swapped_mib, reservation_mib,
                            limit_mib, hot_add, source_available=True):
    """
    Assess memory pressure and return conservative sizing guidance.

    This is advisory and uses RVTools vMemory telemetry. It avoids reducing
    memory when pressure, reservations, or limits make sizing risky.
    """
    configured = _clean_number(configured_mib, 0)
    active = _clean_number(active_mib, 0)
    consumed = _clean_number(consumed_mib, 0)
    ballooned = _clean_number(ballooned_mib, 0)
    swapped = _clean_number(swapped_mib, 0)
    reservation = _clean_number(reservation_mib, 0)
    limit = _clean_number(limit_mib, -1)
    hot_add_text = _clean_text(hot_add)
    reasons = []
    blockers = []

    if not source_available and configured > 0:
        return {
            "status": "Review",
            "reasons": "vMemory data missing; preserve configured memory",
            "configured_mib": round(configured, 2),
            "active_mib": active,
            "consumed_mib": consumed,
            "ballooned_mib": ballooned,
            "swapped_mib": swapped,
            "reservation_mib": reservation,
            "limit_mib": limit,
            "hot_add": hot_add_text,
            "sizing_memory_mib": _round_memory_mib(configured),
            "sizing_basis": "missing-vmemory-preserve-configured-memory",
        }

    if configured <= 0:
        return {
            "status": "Review",
            "reasons": "vMemory data missing; preserve configured memory",
            "configured_mib": 0,
            "active_mib": active,
            "consumed_mib": consumed,
            "ballooned_mib": ballooned,
            "swapped_mib": swapped,
            "reservation_mib": reservation,
            "limit_mib": limit,
            "hot_add": hot_add_text,
            "sizing_memory_mib": 2048,
            "sizing_basis": "missing-vmemory",
        }

    pressure_threshold = max(MEMORY_PRESSURE_MIB, configured * 0.05)
    severe_pressure = swapped >= pressure_threshold or ballooned >= pressure_threshold

    if severe_pressure:
        blockers.append(
            "Severe memory pressure detected; preserve configured memory"
        )
    elif swapped > 0 or ballooned > 0:
        reasons.append(
            "Memory swapping or ballooning detected; validate before resizing"
        )

    if limit > 0 and limit < configured:
        blockers.append(
            "Memory limit is below configured memory; remove or validate limit"
        )

    if reservation > 0:
        reasons.append(
            "Memory reservation detected; confirm target sizing requirement"
        )

    if hot_add_text.lower() == "true":
        reasons.append("Memory hot-add enabled; confirm guest support in target")

    consumed_ratio = consumed / configured if configured else 0
    active_ratio = active / configured if configured else 0
    if consumed_ratio >= 0.9 and active <= 0:
        reasons.append(
            "Consumed memory is high and active memory is missing; preserve memory"
        )

    preserve_memory = bool(blockers) or swapped > 0 or ballooned > 0
    preserve_memory = preserve_memory or reservation > 0
    preserve_memory = preserve_memory or (consumed_ratio >= 0.9 and active <= 0)

    if preserve_memory:
        sizing_memory = configured
        sizing_basis = "preserve-configured-memory"
    elif active > 0 and active_ratio <= 0.5:
        sizing_memory = max(active * 2, configured * 0.5, 2048)
        sizing_basis = "active-memory-with-50-percent-floor"
        reasons.append(
            "Active memory is materially below configured memory; conservative reduction applied"
        )
    else:
        sizing_memory = configured * 0.8
        sizing_basis = "configured-memory-80-percent"

    if reservation > 0:
        sizing_memory = max(sizing_memory, reservation)

    sizing_memory = max(2048, min(configured, _round_memory_mib(sizing_memory)))

    if blockers:
        status = "Blocked"
    elif reasons:
        status = "Review"
    else:
        status = "Ready"
        reasons.append("No memory pressure or constraints detected")

    return {
        "status": status,
        "reasons": "; ".join(blockers + reasons),
        "configured_mib": round(configured, 2),
        "active_mib": round(active, 2),
        "consumed_mib": round(consumed, 2),
        "ballooned_mib": round(ballooned, 2),
        "swapped_mib": round(swapped, 2),
        "reservation_mib": round(reservation, 2),
        "limit_mib": round(limit, 2),
        "hot_add": hot_add_text,
        "sizing_memory_mib": sizing_memory,
        "sizing_basis": sizing_basis,
    }


def _as_record(value):
    if hasattr(value, "to_record"):
        return value.to_record()
    return value


def make_readiness_finding(finding_type, severity, source_tab, evidence,
                           recommended_action):
    """Create a normalized migration readiness finding record."""
    return {
        "finding_type": _clean_value(finding_type),
        "severity": _clean_value(severity, "Review"),
        "source_tab": _clean_value(source_tab),
        "evidence": _clean_value(evidence),
        "recommended_action": _clean_value(recommended_action),
    }


def summarize_migration_readiness(findings):
    """Summarize VM migration readiness findings into Ready/Review/Blocked."""
    clean_findings = [
        _as_record(finding) for finding in findings
        if _clean_value(_as_record(finding).get('severity'))
    ]
    if not clean_findings:
        return {
            "status": "Ready",
            "reasons": "No migration readiness blockers found",
        }

    severities = [
        _clean_value(finding.get('severity')).lower()
        for finding in clean_findings
    ]
    status = "Blocked" if "blocked" in severities else "Review"
    reasons = []
    for finding in clean_findings:
        label = _clean_value(finding.get('finding_type'), 'Finding')
        evidence = _clean_value(finding.get('evidence'))
        reason = f"{label}: {evidence}" if evidence else label
        reasons.append(reason)

    return {
        "status": status,
        "reasons": "; ".join(reasons),
    }
