"""Snapshot tests for Wave Planning tab UI.

Tests cover:
- Wave planning table display (columns, sample data)
- Bulk assignment workflow (select VMs, apply wave)
- Conflict detection warnings (apps with different cutover groups, dependency groups with different waves)
- Status badge (Complete/Incomplete counts)
"""
import json
import pandas as pd


def test_wave_planning_table_display_snapshot(assert_matches_snapshot):
    """Test wave planning table columns and sample data display."""
    # Create sample active VMs dataframe (excluding excluded VMs)
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "John Doe",
            "Application": "Web Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "Jane Smith",
            "Application": "API Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Wave": "Wave 2",
            "Cutover Group": "CG-B",
            "Owner": "Bob Johnson",
            "Application": "Database",
            "Priority": "Medium",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
    ])

    # Extract display columns
    display_cols = [
        "VM Key", "VM Name", "Wave", "Cutover Group", "Owner",
        "Application", "Priority", "Dependency Group"
    ]
    table_data = df[display_cols].to_json(orient="records", indent=2)

    assert_matches_snapshot("wave_planning_table.json", table_data)


def test_wave_planning_bulk_assignment_workflow_snapshot(assert_matches_snapshot):
    """Test bulk assignment workflow: select VMs, apply wave fields."""
    # Create initial dataframe
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": False,
        },
    ])

    # Simulate bulk assignment to first two VMs
    selected_vms = ["vm-001", "vm-002"]
    assign_fields = {
        "Wave": "Wave 1",
        "Cutover Group": "CG-A",
        "Owner": "John Doe",
        "Application": "Web Tier",
    }

    # Apply assignment
    for vmk in selected_vms:
        mask = df["VM Key"] == vmk
        for field, value in assign_fields.items():
            df.loc[mask, field] = value

    # Verify result
    result = df.to_json(orient="records", indent=2)
    assert_matches_snapshot("wave_planning_bulk_assignment.json", result)


def test_wave_planning_conflict_detection_app_cutover_snapshot(
    assert_matches_snapshot,
):
    """Test conflict detection: applications with different cutover groups."""
    # Create dataframe with conflicting app-cutover mappings
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Application": "Web Server",
            "Cutover Group": "CG-A",
            "Wave": "Wave 1",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Application": "Web Server",  # Same app
            "Cutover Group": "CG-B",  # Different cutover group -> CONFLICT
            "Wave": "Wave 1",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Application": "Database",
            "Cutover Group": "CG-C",
            "Wave": "Wave 2",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
    ])

    # Detect conflicts: Application vs Cutover Group
    active_df = df[~df["Exclude?"]].copy()
    conflicts = []
    for app, group in active_df.groupby("Application"):
        vals = set(group["Cutover Group"].dropna().astype(str).unique())
        vals = {v for v in vals if v}
        if len(vals) > 1:
            conflicts.append({"application": app, "cutover_groups": sorted(vals)})

    result = json.dumps({"app_cutover_conflicts": conflicts}, indent=2) + "\n"
    assert_matches_snapshot("wave_planning_conflict_app_cutover.json", result)


def test_wave_planning_conflict_detection_dependency_wave_snapshot(
    assert_matches_snapshot,
):
    """Test conflict detection: dependency groups with different waves."""
    # Create dataframe with conflicting dependency-wave mappings
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Application": "Web Server",
            "Cutover Group": "CG-A",
            "Wave": "Wave 1",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Application": "API Server",
            "Cutover Group": "CG-A",
            "Wave": "Wave 2",  # Different wave -> CONFLICT
            "Dependency Group": "DG-01",  # Same dependency group
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Application": "Database",
            "Cutover Group": "CG-B",
            "Wave": "Wave 2",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
    ])

    # Detect conflicts: Dependency Group vs Wave
    active_df = df[~df["Exclude?"]].copy()
    conflicts = []
    for dep, group in active_df.groupby("Dependency Group"):
        vals = set(group["Wave"].dropna().astype(str).unique())
        vals = {v for v in vals if v}
        if len(vals) > 1:
            conflicts.append({"dependency_group": dep, "waves": sorted(vals)})

    result = json.dumps({"dependency_wave_conflicts": conflicts}, indent=2) + "\n"
    assert_matches_snapshot("wave_planning_conflict_dependency_wave.json", result)


def test_wave_planning_status_badge_complete_snapshot(assert_matches_snapshot):
    """Test status badge when all required fields are complete."""
    # Create dataframe with all required fields filled
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "John Doe",
            "Application": "Web Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "Jane Smith",
            "Application": "API Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "excluded-vm",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": True,  # Excluded VMs don't count
        },
    ])

    # Calculate completion status (only for non-excluded VMs)
    active_vms = df[~df["Exclude?"]]
    total = len(active_vms)
    required = ["Wave", "Cutover Group", "Owner", "Application"]
    complete = 0
    for _, r in active_vms.iterrows():
        if all(r.get(c) not in (None, "") for c in required):
            complete += 1

    status_result = {
        "total": total,
        "complete": complete,
        "incomplete": total - complete,
        "status": "Complete" if complete == total else "Incomplete",
    }

    result = json.dumps(status_result, indent=2) + "\n"
    assert_matches_snapshot("wave_planning_status_complete.json", result)


def test_wave_planning_status_badge_incomplete_snapshot(assert_matches_snapshot):
    """Test status badge when some required fields are missing."""
    # Create dataframe with incomplete required fields
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "John Doe",
            "Application": "Web Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Wave": "",  # Missing wave
            "Cutover Group": "CG-A",
            "Owner": "Jane Smith",
            "Application": "API Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Wave": "Wave 2",
            "Cutover Group": "",  # Missing cutover group
            "Owner": "Bob Johnson",
            "Application": "Database",
            "Priority": "Medium",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
    ])

    # Calculate completion status
    active_vms = df[~df["Exclude?"]]
    total = len(active_vms)
    required = ["Wave", "Cutover Group", "Owner", "Application"]
    complete = 0
    for _, r in active_vms.iterrows():
        if all(r.get(c) not in (None, "") for c in required):
            complete += 1

    status_result = {
        "total": total,
        "complete": complete,
        "incomplete": total - complete,
        "status": "Complete" if complete == total else "Incomplete",
    }

    result = json.dumps(status_result, indent=2) + "\n"
    assert_matches_snapshot("wave_planning_status_incomplete.json", result)


def test_wave_planning_empty_form_state_snapshot(assert_matches_snapshot):
    """Test initial form state with no assignments."""
    # Create initial state with empty wave fields
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": False,
        },
    ])

    display_cols = [
        "VM Key", "VM Name", "Wave", "Cutover Group", "Owner",
        "Application", "Priority", "Dependency Group"
    ]
    result = df[display_cols].to_json(orient="records", indent=2)
    assert_matches_snapshot("wave_planning_empty_form.json", result)


def test_wave_planning_multi_wave_assignment_snapshot(assert_matches_snapshot):
    """Test complex scenario: multiple waves with different groupings."""
    # Create dataframe with multiple waves and groups
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "John Doe",
            "Application": "Web Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "app-02",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "John Doe",
            "Application": "Web Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Wave": "Wave 2",
            "Cutover Group": "CG-B",
            "Owner": "Bob Johnson",
            "Application": "Database",
            "Priority": "Medium",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-004",
            "VM Name": "db-02",
            "Wave": "Wave 2",
            "Cutover Group": "CG-B",
            "Owner": "Bob Johnson",
            "Application": "Database",
            "Priority": "Medium",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-005",
            "VM Name": "cache-01",
            "Wave": "Wave 3",
            "Cutover Group": "CG-C",
            "Owner": "Alice Lee",
            "Application": "Cache",
            "Priority": "Low",
            "Dependency Group": "DG-03",
            "Exclude?": False,
        },
    ])

    display_cols = [
        "VM Key", "VM Name", "Wave", "Cutover Group", "Owner",
        "Application", "Priority", "Dependency Group"
    ]
    result = df[display_cols].to_json(orient="records", indent=2)
    assert_matches_snapshot("wave_planning_multi_wave_assignment.json", result)


def test_wave_planning_table_with_excluded_vms_snapshot(assert_matches_snapshot):
    """Test that excluded VMs are not displayed in the wave planning table."""
    # Create dataframe with some excluded VMs
    df = pd.DataFrame([
        {
            "VM Key": "vm-001",
            "VM Name": "app-01",
            "Wave": "Wave 1",
            "Cutover Group": "CG-A",
            "Owner": "John Doe",
            "Application": "Web Server",
            "Priority": "High",
            "Dependency Group": "DG-01",
            "Exclude?": False,
        },
        {
            "VM Key": "vm-002",
            "VM Name": "excluded-vm",
            "Wave": "",
            "Cutover Group": "",
            "Owner": "",
            "Application": "",
            "Priority": "Medium",
            "Dependency Group": "",
            "Exclude?": True,  # This VM is excluded
        },
        {
            "VM Key": "vm-003",
            "VM Name": "db-01",
            "Wave": "Wave 2",
            "Cutover Group": "CG-B",
            "Owner": "Bob Johnson",
            "Application": "Database",
            "Priority": "Medium",
            "Dependency Group": "DG-02",
            "Exclude?": False,
        },
    ])

    # Filter to active VMs only
    active_df = df[~df["Exclude?"]].copy()
    display_cols = [
        "VM Key", "VM Name", "Wave", "Cutover Group", "Owner",
        "Application", "Priority", "Dependency Group"
    ]
    result = active_df[display_cols].to_json(orient="records", indent=2)
    assert_matches_snapshot("wave_planning_with_excluded_vms.json", result)
