import pandas as pd


def normalize_network_name(name):
    cleaned = str(name).strip()
    if not cleaned or cleaned.lower() == 'nan':
        cleaned = 'unknown'
    return cleaned.lower().replace(" ", "_").replace("-", "_")


def get_row_identity(row, fallback):
    for col in ["VM", "VM UUID", "VM ID"]:
        value = row.get(col)
        if value is not None and not pd.isna(value):
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
    return fallback


def get_vm_display_name(row, fallback):
    for col in ["VM", "DNS Name", "VM UUID", "VM ID"]:
        value = row.get(col)
        if value is not None and not pd.isna(value):
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
    return fallback


def as_bool(value):
    if value is None or pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ["true", "yes", "1", "connected"]


def as_float(value, default=0.0):
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_cell(value, default=""):
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return default if text.lower() == "nan" else text


def clean_disk_key(value):
    cleaned = clean_cell(value)
    try:
        numeric = float(cleaned)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return cleaned


def is_unhealthy_status(value):
    text = clean_cell(value).lower()
    if not text:
        return False
    healthy_tokens = ["green", "ok", "toolsok", "running", "ready"]
    if any(token in text for token in healthy_tokens):
        return False
    unhealthy_tokens = [
        "gray", "red", "yellow", "not", "old", "upgrade", "error",
        "fail", "false", "none", "unknown"
    ]
    return any(token in text for token in unhealthy_tokens)


def first_present(record, candidates, default=""):
    for candidate in candidates:
        value = record.get(candidate)
        if value is not None and not pd.isna(value):
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
    return default


def normalize_match_key(value):
    return clean_cell(value).lower()


def row_matches_any(row, candidates, expected):
    expected = normalize_match_key(expected)
    if not expected:
        return False
    return any(
        normalize_match_key(row.get(candidate)) == expected
        for candidate in candidates
    )


