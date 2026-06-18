import streamlit as st


def build_help_samples_sections():
    """Return sidebar help content for first-run users."""
    return [
        {
            "title": "Small sample",
            "body": (
                "`Load Sample Workbook` uses "
                "`samples/rvtools-small-complete.xlsx` for a clean first run "
                "that should parse, render every tab, and build a Terraform "
                "handoff package."
            ),
        },
        {
            "title": "Workshop sample",
            "body": (
                "`samples/SizingWorkshop-RVTools.xlsx` is a larger practice "
                "workbook with expected readiness and preflight findings."
            ),
        },
        {
            "title": "Recommended workflow",
            "body": (
                "Load the sample or upload RVTools, review Overview and "
                "Readiness, apply safe tracking defaults if useful, complete "
                "planning tabs, review Migration Ops, then build the Export "
                "package."
            ),
        },
        {
            "title": "Documentation",
            "body": (
                "Start with `README.md` and `docs/user-manual.md`. Use "
                "`docs/testing.md`, `docs/migration-handoff-package.md`, and "
                "`docs/demo-video-guide.md` for validation, ZIP contents, and "
                "demo walkthroughs."
            ),
        },
        {
            "title": "Tool boundary",
            "body": (
                "The app generates Terraform and migration handoff files. It "
                "does not run Terraform, import images, or perform cutover."
            ),
        },
    ]


def build_workshop_sample_findings():
    """Return expected practice findings for the larger workshop workbook."""
    return [
        {
            "title": "Image import placeholders",
            "body": (
                "The workshop workbook intentionally leaves custom image IDs "
                "unresolved, so Export preflight should show image placeholder "
                "warnings that belong to Terraform operator review."
            ),
        },
        {
            "title": "Unknown target network",
            "body": (
                "The workbook can produce an `unknown-net` CIDR blocker. Use "
                "Export > Subnet CIDRs to provide a valid target CIDR before "
                "building the package."
            ),
        },
        {
            "title": "wowas3 network review",
            "body": (
                "`wowas3` is expected to show network readiness review because "
                "its connected source NIC lacks a usable network name. Correct "
                "the source RVTools/vSphere data or exclude it from the package "
                "when practicing blocker handling."
            ),
        },
    ]


def render_help_and_samples_panel():
    """Render compact first-run help in the sidebar."""
    with st.sidebar.expander("Help And Samples"):
        for section in build_help_samples_sections():
            st.markdown(f"**{section['title']}**")
            st.caption(section["body"])
        st.markdown("**Workshop practice findings**")
        for finding in build_workshop_sample_findings():
            st.caption(f"- **{finding['title']}:** {finding['body']}")
