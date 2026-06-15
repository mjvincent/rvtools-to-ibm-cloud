import pandas as pd
import streamlit as st


READINESS_COLUMNS = [
    "VM Name", "Power State", "Image Readiness", "Readiness Reasons",
    "Migration Readiness", "Migration Readiness Reasons",
    "Memory Readiness", "Memory Readiness Reasons",
    "Network Readiness", "Network Readiness Reasons", "Data Status"
]

READINESS_STATUS_COLUMNS = [
    "Image Readiness",
    "Migration Readiness",
    "Memory Readiness",
    "Network Readiness",
]


def active_df(df_f):
    return df_f[~df_f["Exclude?"]]


def count_status(df, column, status):
    return len(df[df[column] == status])


def calculate_estate_summary(df_f):
    active = active_df(df_f)
    blocked = sum(
        count_status(active, column, "Blocked")
        for column in READINESS_STATUS_COLUMNS
    )
    review = sum(
        count_status(active, column, "Review")
        for column in READINESS_STATUS_COLUMNS
    )
    return {
        "in_scope": len(active),
        "excluded": len(df_f) - len(active),
        "monthly": active["Monthly Cost"].sum(),
        "savings": active["Savings (Mo)"].sum(),
        "blocked": blocked,
        "review": review,
    }


def calculate_overview_blockers(df_f):
    active = active_df(df_f)
    return {
        "image": count_status(active, "Image Readiness", "Blocked"),
        "migration": count_status(active, "Migration Readiness", "Blocked"),
        "memory": count_status(active, "Memory Readiness", "Blocked"),
    }


def render_estate_summary(df_f):
    summary = calculate_estate_summary(df_f)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("In Scope", summary["in_scope"])
    c2.metric("Excluded", summary["excluded"])
    c3.metric("Monthly Estimate", f"${summary['monthly']:,.2f}")
    c4.metric("Potential Savings", f"${summary['savings']:,.2f}")
    c5.metric("Readiness Blockers", summary["blocked"])

    if summary["blocked"]:
        st.warning(
            f"{summary['blocked']} blocker signal(s) need remediation before "
            "export, replication, image import, or cutover planning."
        )
    elif summary["review"]:
        st.info(
            f"{summary['review']} review signal(s) should be validated with "
            "workload owners before migration waves are finalized."
        )
    else:
        st.success(
            "No readiness blockers or review signals were detected for "
            "in-scope VMs."
        )


def render_assessment_quality(report):
    summary = (report or {}).get("summary", {})
    tabs = (report or {}).get("tabs", [])
    required_present = summary.get("required_tabs_present", 0)
    required_total = summary.get("required_tabs_total", 0)
    optional_present = summary.get("optional_readiness_tabs_present", 0)
    optional_total = summary.get("optional_readiness_tabs_total", 0)
    optional_network_present = summary.get(
        "optional_network_detail_tabs_present", 0
    )
    optional_network_total = summary.get("optional_network_detail_tabs_total", 0)

    st.subheader("Assessment Quality")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall Confidence", summary.get("overall_confidence", "Low"))
    c2.metric("Required Tabs", f"{required_present}/{required_total}")
    c3.metric("Optional Readiness Tabs", f"{optional_present}/{optional_total}")
    c4.metric(
        "Network Detail Tabs",
        f"{optional_network_present}/{optional_network_total}"
    )
    c5.metric("Missing or Empty Tabs", summary.get("missing_or_empty_tabs", 0))

    confidence = summary.get("overall_confidence", "Low")
    if confidence == "High":
        st.success("RVTools coverage supports high-confidence planning signals.")
    elif confidence == "Medium":
        st.info(
            "RVTools coverage is usable, with some fallback or partial "
            "confidence signals."
        )
    else:
        st.warning(
            "RVTools coverage is limited. Review missing or empty tabs before "
            "relying on planning outputs."
        )

    with st.expander("Worksheet coverage details"):
        if tabs:
            st.dataframe(
                pd.DataFrame(tabs),
                hide_index=True,
                width="stretch",
            )
        else:
            st.write("No worksheet quality data is available.")


def render_overview_tab(df_f, assessment_quality):
    st.subheader("Estate Health")
    blockers = calculate_overview_blockers(df_f)
    c1, c2, c3 = st.columns(3)
    c1.metric("Image Blocked", blockers["image"])
    c2.metric("Migration Blocked", blockers["migration"])
    c3.metric("Memory Blocked", blockers["memory"])
    st.subheader("Recommended Next Actions")
    st.write("1. Resolve Blocked readiness items before migration execution.")
    st.write("2. Validate Review items with workload owners and VMware administrators.")
    st.write(
        "3. Confirm profile, storage tier, network, subnet, and security "
        "group overrides in VM Review."
    )
    st.write(
        "4. Confirm Terraform deployment settings in Export and build the "
        "package."
    )
    render_assessment_quality(assessment_quality)


def render_readiness_triage(df_f):
    active = active_df(df_f)
    st.caption(
        "Blocked and Review items are shown first so planning effort starts "
        "where it matters most."
    )
    for label, column, reason_column in [
        ("Image", "Image Readiness", "Readiness Reasons"),
        ("Migration", "Migration Readiness", "Migration Readiness Reasons"),
        ("Memory", "Memory Readiness", "Memory Readiness Reasons"),
        ("Network", "Network Readiness", "Network Readiness Reasons"),
    ]:
        st.subheader(f"{label} Readiness")
        c1, c2, c3 = st.columns(3)
        c1.metric("Blocked", count_status(active, column, "Blocked"))
        c2.metric("Review", count_status(active, column, "Review"))
        c3.metric("Ready", count_status(active, column, "Ready"))
        ordered = active.copy()
        ordered["_status_order"] = ordered[column].map({
            "Blocked": 0,
            "Review": 1,
            "Ready": 2,
        }).fillna(3)
        view = ordered.sort_values(["_status_order", "VM Name"])[
            ["VM Name", column, reason_column, "Power State", "Data Status"]
        ]
        st.dataframe(view, hide_index=True, width="stretch")


def render_readiness_legend():
    st.caption(
        "Ready means no detected issue in available data. Review means owner "
        "validation is needed. Blocked means remediation should happen before "
        "migration execution."
    )
