import pandas as pd

from streamlit_app.wave_planning import (
    WAVE_DISPLAY_COLUMNS,
    active_wave_dataframe,
    apply_wave_fields,
    detect_app_cutover_conflicts,
    detect_dependency_wave_conflicts,
    persist_wave_editor_edits,
    wave_completion_status,
)


def test_active_wave_dataframe_filters_excluded_and_adds_defaults():
    df = pd.DataFrame([
        {"VM Key": "vm-1", "VM Name": "app-01", "Exclude?": False},
        {"VM Key": "vm-2", "VM Name": "skip-01", "Exclude?": True},
    ])

    active = active_wave_dataframe(df)

    assert active[WAVE_DISPLAY_COLUMNS].to_dict("records") == [{
        "VM Key": "vm-1",
        "VM Name": "app-01",
        "Wave": "",
        "Cutover Group": "",
        "Owner": "",
        "Application": "",
        "Priority": "Medium",
        "Dependency Group": "",
    }]


def test_apply_wave_fields_only_applies_non_empty_values():
    df = pd.DataFrame([
        {
            "VM Key": "vm-1",
            "Wave": "",
            "Cutover Group": "Existing",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-2",
            "Wave": "",
            "Cutover Group": "",
            "Exclude?": False,
        },
    ])

    updated = apply_wave_fields(
        df,
        ["vm-1"],
        {"Wave": "Wave 1", "Cutover Group": ""},
    )

    assert updated.loc[0, "Wave"] == "Wave 1"
    assert updated.loc[0, "Cutover Group"] == "Existing"
    assert updated.loc[1, "Wave"] == ""


def test_persist_wave_editor_edits_updates_matching_vm_rows():
    df = pd.DataFrame([
        {
            "VM Key": "vm-1",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": False,
        }
    ])
    editor = pd.DataFrame([
        {
            "VM Key": "vm-1",
            "Wave": "Wave 2",
            "Cutover Group": "CG-B",
            "Owner": "platform",
            "Application": "payments",
            "Priority": "High",
            "Dependency Group": "DG-2",
        }
    ])

    updated = persist_wave_editor_edits(df, editor)

    assert updated.loc[0, "Wave"] == "Wave 2"
    assert updated.loc[0, "Cutover Group"] == "CG-B"
    assert updated.loc[0, "Priority"] == "High"


def test_wave_conflict_helpers_return_sorted_conflicts():
    active = pd.DataFrame([
        {
            "Application": "app",
            "Cutover Group": "CG-B",
            "Dependency Group": "DG-1",
            "Wave": "Wave 2",
        },
        {
            "Application": "app",
            "Cutover Group": "CG-A",
            "Dependency Group": "DG-1",
            "Wave": "Wave 1",
        },
    ])

    assert detect_app_cutover_conflicts(active) == [("app", ["CG-A", "CG-B"])]
    assert detect_dependency_wave_conflicts(active) == [
        ("DG-1", ["Wave 1", "Wave 2"])
    ]


def test_wave_completion_status_counts_active_vms_only():
    df = pd.DataFrame([
        {
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "platform",
            "Application": "web",
            "Exclude?": False,
        },
        {
            "Wave": "",
            "Cutover Group": "CG-B",
            "Owner": "platform",
            "Application": "db",
            "Exclude?": False,
        },
        {
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Exclude?": True,
        },
    ])

    assert wave_completion_status(df) == {
        "total": 2,
        "complete": 1,
        "incomplete": 1,
        "status": "Incomplete",
    }
