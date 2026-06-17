from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from catalog_pricing import get_pricing_catalog, pricing_status_summary

SAMPLE_WORKBOOK_SESSION_KEY = "use_sample_workbook"
SAMPLE_WORKBOOK_RELATIVE_PATH = Path("samples") / "rvtools-small-complete.xlsx"

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


def get_sample_workbook_path(repo_root=None):
    """Return the bundled small sample workbook path when it exists."""
    base_path = Path(repo_root) if repo_root is not None else Path(__file__).parents[1]
    sample_path = base_path / SAMPLE_WORKBOOK_RELATIVE_PATH
    if sample_path.exists():
        return sample_path
    return None


def select_active_workbook(uploaded_file, sample_enabled, sample_path):
    """Return the uploaded workbook or bundled sample path for parsing."""
    if uploaded_file is not None:
        return uploaded_file
    if sample_enabled and sample_path is not None:
        return sample_path
    return None


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
        "Target IBM Region",
        ["us-south", "us-east", "eu-gb", "jp-tok"],
        help="IBM Cloud region where the generated VPC, subnets, storage, and VSI resources will be planned.",
    )

    st.sidebar.header("Right-Sizing Settings")
    threshold_mode = st.sidebar.selectbox(
        "Standard Thresholds",
        THRESHOLD_MODES,
        index=1,
        help="Right-sizing aggressiveness. Lower thresholds keep more headroom; higher thresholds reduce target CPU more aggressively.",
    )
    threshold = _threshold_from_mode(threshold_mode)
    if threshold is None:
        utilization_threshold = st.sidebar.slider(
            "Custom CPU Threshold (%)",
            1,
            100,
            40,
            help="CPU utilization target used when the standard threshold mode is set to Custom.",
        )
    else:
        utilization_threshold = threshold

    project_name = st.sidebar.text_input(
        "Project Name",
        "my-ibm-migration",
        help="Used for generated file names and Terraform package naming. Keep it short and shell-friendly.",
    )
    target_zone = st.sidebar.selectbox(
        "Target IBM Zone",
        REGION_ZONES.get(target_region, [f"{target_region}-1"]),
        help="IBM Cloud availability zone for generated VSI and block storage resources.",
    )

    st.sidebar.header("Pricing Settings")
    pricing_mode_label = st.sidebar.selectbox(
        "Pricing Mode",
        list(PRICING_MODE_MAP),
        index=0,
        help="Controls whether estimates use static fallback rates, a cached IBM catalog, or live IBM profile discovery.",
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
        "Generate Security Groups",
        value=True,
        help="When enabled, the Terraform package includes per-network security groups and attaches VM NICs to them.",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Upload RVTools, review blockers first, adjust only the decisions that "
        "need human intent, then build the Terraform handoff package."
    )
    st.sidebar.info(
        "RVTools exports can contain sensitive infrastructure inventory. "
        "Use an approved device or hosted environment before uploading."
    )
    uploaded_file = st.sidebar.file_uploader(
        "Upload RVTools",
        type=["xlsx"],
        help="Upload a standard RVTools Excel workbook. Use samples/rvtools-small-complete.xlsx for a first test run.",
    )
    sample_path = get_sample_workbook_path()
    if st.sidebar.button(
        "Load Sample Workbook",
        disabled=sample_path is None,
        help=(
            "Load the bundled small RVTools sample directly into the app for "
            "a first test run."
        ),
        width="stretch",
    ):
        st.session_state[SAMPLE_WORKBOOK_SESSION_KEY] = True
    if uploaded_file is not None:
        st.session_state[SAMPLE_WORKBOOK_SESSION_KEY] = False

    active_workbook = select_active_workbook(
        uploaded_file,
        st.session_state.get(SAMPLE_WORKBOOK_SESSION_KEY, False),
        sample_path,
    )
    if active_workbook == sample_path and sample_path is not None:
        st.sidebar.success("Using bundled sample workbook.")
    elif sample_path is None:
        st.sidebar.warning("Bundled sample workbook is unavailable.")

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
    return settings, active_workbook
