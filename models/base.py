def clean_value(value, default=""):
    """Return JSON/CSV friendly scalar values from pandas/Streamlit records."""
    if value is None:
        return default
    try:
        if value != value:
            return default
    except TypeError:
        pass
    if isinstance(value, str):
        stripped = value.strip()
        return default if stripped.lower() == "nan" else stripped
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return default
    return value


def as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(clean_value(value)).strip().lower()
    if not text:
        return default
    return text in ["true", "yes", "1", "connected", "poweredon"]


def get_record_value(record, key, default=""):
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


def clean_number(value, default=0):
    value = clean_value(value, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _prefer(current, nested, default=""):
    current_value = clean_value(current, default)
    nested_value = clean_value(nested, default)
    if current_value in ["", None]:
        return nested_value
    if current_value == default and nested_value not in ["", None, default]:
        return nested_value
    return current_value

