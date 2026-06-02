from dataclasses import dataclass

import streamlit as st

from catalog_pricing import get_pricing_catalog, pricing_status_summary


THRESHOLD_MODES = [
    "Conservative (30%)",
    "IBM Standard (40%)",
    "Moderate (50%)",
    "Aggressive (70%)",
    "Custom",
]

PRICING_MODE_MAP = {
    "Static fallback": "static",
    "Cached IBM catalog": "cached",
    "Live IBM profile discovery": "live",
}

REGION_ZONES = {
    "us-south": ["us-south-1", "us-south-2", "us-south-3"],
    "us-east": ["us-east-1", "us-east-2", "us-east-3"],
    "eu-gb": ["eu-gb-1"],
    "jp-tok": ["jp-tok-1"],
}


@dataclass
class MigrationSettings:
    target_region: str
    utilization_threshold: int
    project_name: str
    target_zone: str
    pricing_catalog: dict
    pricing_metadata: dict
    catalog_profiles: list
    storage_tier_rates: dict | None
    generate_security_groups: bool


def _threshold_from_mode(threshold_mode: str) -> int | None:
    if threshold_mode == "Custom":
        return None
    return int("".join(filter(str.isdigit, threshold_mode)))


def render_sidebar_settings():
    """Render sidebar controls and return selected migration settings."""
    st.sidebar.header("Migration Settings")
    target_region = st.sidebar.selectbox(
        "Target IBM Region", ["us-south", "us-east", "eu-gb", "jp-tok"]
    )

    st.sidebar.header("Right-Sizing Settings")
    threshold_mode = st.sidebar.selectbox(
        "Standard Thresholds", THRESHOLD_MODES, index=1
    )
    threshold = _threshold_from_mode(threshold_mode)
    if threshold is None:
        utilization_threshold = st.sidebar.slider(
            "Custom CPU Threshold (%)", 1, 100, 40
        )
    else:
        utilization_threshold = threshold

    project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")
    target_zone = st.sidebar.selectbox(
        "Target IBM Zone",
        REGION_ZONES.get(target_region, [f"{target_region}-1"]),
    )

    st.sidebar.header("Pricing Settings")
    pricing_mode_label = st.sidebar.selectbox(
        "Pricing Mode",
        list(PRICING_MODE_MAP),
        index=0,
    )
    pricing_catalog = get_pricing_catalog(
        PRICING_MODE_MAP[pricing_mode_label],
        region=target_region,
    )
    pricing_metadata = pricing_catalog.get("metadata", {})
    catalog_profiles = pricing_catalog.get("profiles", [])
    storage_tier_rates = pricing_catalog.get("storage_tier_rates")
    st.sidebar.caption(pricing_status_summary(pricing_catalog))
    if pricing_metadata.get("status"):
        st.sidebar.info(pricing_metadata["status"])

    generate_security_groups = st.sidebar.checkbox(
        "Generate Security Groups", value=True
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Upload RVTools, review blockers first, adjust only the decisions that "
        "need human intent, then build the Terraform handoff package."
    )
    uploaded_file = st.sidebar.file_uploader("Upload RVTools", type=["xlsx"])

    settings = MigrationSettings(
        target_region=target_region,
        utilization_threshold=utilization_threshold,
        project_name=project_name,
        target_zone=target_zone,
        pricing_catalog=pricing_catalog,
        pricing_metadata=pricing_metadata,
        catalog_profiles=catalog_profiles,
        storage_tier_rates=storage_tier_rates,
        generate_security_groups=generate_security_groups,
    )
    return settings, uploaded_file
