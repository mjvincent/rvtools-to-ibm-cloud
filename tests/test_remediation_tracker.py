"""
Snapshot tests for remediation tracker UI and export functionality.

Tests cover:
- Remediation backlog display with sample blockers
- Editing status/due date/notes in the data editor
- Export CSV generation with verification of rows and summary
- Overdue detection logic
"""

import pandas as pd
from datetime import datetime, timedelta
from handoff import remediation_tracker_export


def test_remediation_backlog_display_sample_blockers(sample_vm_model, assert_matches_snapshot):
    """Test remediation backlog display with sample blockers."""
    # Create sample backlog items (simulating what the UI would show)
    backlog_items = [
        {
            "blocker_id": f"{sample_vm_model.vm_key}::0",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "team-a",
            "Blocker Type": "VMware Tools status",
            "Blocker Description": "Update VMware Tools",
            "Status": "Open",
            "Due Date": "2024-12-31",
            "Notes": "Requires downtime window",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::1",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "team-b",
            "Blocker Type": "Storage Configuration",
            "Blocker Description": "Multiple disks detected",
            "Status": "In Progress",
            "Due Date": "2024-11-30",
            "Notes": "Mapping disks to storage tiers",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::2",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "team-a",
            "Blocker Type": "Network Configuration",
            "Blocker Description": "Multi-NIC setup",
            "Status": "Resolved",
            "Due Date": "2024-11-15",
            "Notes": "Configured in migration spec",
        },
    ]
    
    # Create DataFrame as the UI would
    backlog_df = pd.DataFrame(backlog_items)
    
    # Convert to CSV format (what would be displayed)
    csv_output = backlog_df.to_csv(index=False)
    
    assert_matches_snapshot("remediation_backlog_display.csv", csv_output)


def test_remediation_editor_data_persistence(sample_vm_model, assert_matches_snapshot):
    """Test editing status/due date/notes in the data editor with persistence."""
    # Simulate user edits to backlog items
    backlog_items = [
        {
            "blocker_id": f"{sample_vm_model.vm_key}::0",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "john.doe@company.com",
            "Blocker Type": "VMware Tools status",
            "Blocker Description": "Update VMware Tools",
            "Status": "Open",
            "Due Date": "",
            "Notes": "",
        },
    ]
    
    backlog_df = pd.DataFrame(backlog_items)
    
    # Simulate user edits
    edited_data = {
        "blocker_id": f"{sample_vm_model.vm_key}::0",
        "VM Key": sample_vm_model.vm_key,
        "VM Name": sample_vm_model.vm_name,
        "Owner": "john.doe@company.com",
        "Blocker Type": "VMware Tools status",
        "Blocker Description": "Update VMware Tools",
        "Status": "In Progress",
        "Due Date": "2024-12-25",
        "Notes": "Scheduled for weekend maintenance",
    }
    
    # Update session state mapping (as the UI would do)
    tracker_state = {
        f"{sample_vm_model.vm_key}::0": {
            "status": edited_data["Status"],
            "due_date": edited_data["Due Date"],
            "notes": edited_data["Notes"],
            "owner": edited_data["Owner"],
        }
    }
    
    # Create output showing both original and edited states
    output = "Original Blocker:\n"
    output += backlog_df.to_csv(index=False)
    output += "\n---\n\nPersisted State:\n"
    for bid, state in sorted(tracker_state.items()):
        output += f"Blocker ID: {bid}\n"
        output += f"  Status: {state['status']}\n"
        output += f"  Due Date: {state['due_date']}\n"
        output += f"  Notes: {state['notes']}\n"
        output += f"  Owner: {state['owner']}\n"
    
    assert_matches_snapshot("remediation_editor_persistence.txt", output)


def test_remediation_export_csv_generation(sample_vm_model, assert_matches_snapshot):
    """Test export CSV generation using remediation_tracker_export()."""
    # Create multiple VMs with various blocker states
    vms = [
        {
            "VM Key": "vm-001",
            "VM Name": "app-server-01",
            "Owner": "team-a",
            "Power State": "poweredOn",
        },
        {
            "VM Key": "vm-002",
            "VM Name": "db-server-01",
            "Owner": "team-b",
            "Power State": "poweredOn",
        },
    ]
    
    # Create remediation tracker with various states
    remediation_tracker = {
        "vm-001::blocker1": {
            "status": "Open",
            "due_date": "2024-12-31",
            "notes": "Waiting for vendor response",
            "owner": "team-a",
            "blocker_type": "Firmware Update",
            "blocker_description": "Update server firmware",
        },
        "vm-001::blocker2": {
            "status": "In Progress",
            "due_date": "2024-11-30",
            "notes": "In queue for maintenance",
            "owner": "team-a",
            "blocker_type": "VMware Tools",
            "blocker_description": "Update VMware Tools",
        },
        "vm-002::blocker1": {
            "status": "Resolved",
            "due_date": "2024-11-15",
            "notes": "Completed",
            "owner": "team-b",
            "blocker_type": "Database Configuration",
            "blocker_description": "Adjust DB parameters",
        },
    }
    
    # Generate CSV export
    csv_output = remediation_tracker_export(vms, remediation_tracker)
    
    assert_matches_snapshot("remediation_export.csv", csv_output)


def test_remediation_export_rows_and_summary(assert_matches_snapshot):
    """Test export CSV generation with verification of rows and summary section."""
    # Create a detailed test case with multiple blockers and owners
    vms = [
        {
            "VM Key": "prod-web-01",
            "VM Name": "production-web-server-01",
            "Owner": "platform-team",
            "Power State": "poweredOn",
        },
        {
            "VM Key": "prod-db-01",
            "VM Name": "production-database-01",
            "Owner": "data-team",
            "Power State": "poweredOn",
        },
        {
            "VM Key": "dev-app-01",
            "VM Name": "development-app-server",
            "Owner": "app-team",
            "Power State": "poweredOn",
        },
    ]
    
    # Create diverse remediation tracker scenarios
    remediation_tracker = {
        # Web server blockers
        "prod-web-01::ssl-cert": {
            "status": "Open",
            "due_date": "2024-12-15",
            "notes": "Need to purchase new certificate",
            "owner": "platform-team",
            "blocker_type": "SSL Certificate",
            "blocker_description": "SSL certificate expires soon",
        },
        "prod-web-01::dns": {
            "status": "In Progress",
            "due_date": "2024-11-30",
            "notes": "Working with network team",
            "owner": "platform-team",
            "blocker_type": "DNS Configuration",
            "blocker_description": "DNS records need update",
        },
        # Database blockers
        "prod-db-01::backup": {
            "status": "Resolved",
            "due_date": "2024-11-01",
            "notes": "Backup procedure implemented",
            "owner": "data-team",
            "blocker_type": "Backup Strategy",
            "blocker_description": "Implement backup strategy",
        },
        "prod-db-01::replication": {
            "status": "Open",
            "due_date": "2024-12-01",
            "notes": "Waiting for replication infrastructure",
            "owner": "data-team",
            "blocker_type": "Replication",
            "blocker_description": "Setup database replication",
        },
        # App server blockers
        "dev-app-01::dependency": {
            "status": "In Progress",
            "due_date": "2024-11-20",
            "notes": "Resolving package version conflicts",
            "owner": "app-team",
            "blocker_type": "Dependency",
            "blocker_description": "Resolve application dependencies",
        },
    }
    
    # Generate CSV export
    csv_output = remediation_tracker_export(vms, remediation_tracker)
    
    assert_matches_snapshot("remediation_export_summary.csv", csv_output)


def test_overdue_detection_logic(assert_matches_snapshot):
    """Test overdue detection logic in export function."""
    vms = [
        {
            "VM Key": "vm-overdue",
            "VM Name": "overdue-test-vm",
            "Owner": "test-team",
            "Power State": "poweredOn",
        },
    ]
    
    # Create trackers with mix of overdue/current/resolved dates
    today = datetime(2026, 6, 1).date()
    past_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
    future_date = (today + timedelta(days=5)).strftime('%Y-%m-%d')
    
    remediation_tracker = {
        "vm-overdue::past1": {
            "status": "Open",
            "due_date": past_date,
            "notes": "This should be marked overdue",
            "owner": "test-team",
            "blocker_type": "Test Blocker",
            "blocker_description": "Overdue blocker with Open status",
        },
        "vm-overdue::past2": {
            "status": "In Progress",
            "due_date": past_date,
            "notes": "This should be marked overdue",
            "owner": "test-team",
            "blocker_type": "Test Blocker",
            "blocker_description": "Overdue blocker with In Progress status",
        },
        "vm-overdue::past3": {
            "status": "Resolved",
            "due_date": past_date,
            "notes": "This should NOT be marked overdue",
            "owner": "test-team",
            "blocker_type": "Test Blocker",
            "blocker_description": "Past due date but Resolved",
        },
        "vm-overdue::future": {
            "status": "Open",
            "due_date": future_date,
            "notes": "This should NOT be marked overdue",
            "owner": "test-team",
            "blocker_type": "Test Blocker",
            "blocker_description": "Future due date",
        },
    }
    
    # Generate CSV export
    csv_output = remediation_tracker_export(
        vms,
        remediation_tracker,
        today=today,
    )
    
    assert_matches_snapshot("remediation_overdue_detection.csv", csv_output)


def test_remediation_backlog_summary_metrics(sample_vm_model, assert_matches_snapshot):
    """Test summary metrics extraction from backlog."""
    # Create a complex backlog with multiple statuses and owners
    backlog_items = [
        {
            "blocker_id": f"{sample_vm_model.vm_key}::0",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "alice",
            "Blocker Type": "Type A",
            "Blocker Description": "Desc A",
            "Status": "Open",
            "Due Date": "2024-12-31",
            "Notes": "Note A",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::1",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "bob",
            "Blocker Type": "Type B",
            "Blocker Description": "Desc B",
            "Status": "Open",
            "Due Date": "2024-11-30",
            "Notes": "Note B",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::2",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "alice",
            "Blocker Type": "Type C",
            "Blocker Description": "Desc C",
            "Status": "In Progress",
            "Due Date": "2024-12-15",
            "Notes": "Note C",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::3",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "charlie",
            "Blocker Type": "Type D",
            "Blocker Description": "Desc D",
            "Status": "In Progress",
            "Due Date": "2024-11-20",
            "Notes": "Note D",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::4",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "bob",
            "Blocker Type": "Type E",
            "Blocker Description": "Desc E",
            "Status": "Resolved",
            "Due Date": "2024-11-01",
            "Notes": "Note E",
        },
        {
            "blocker_id": f"{sample_vm_model.vm_key}::5",
            "VM Key": sample_vm_model.vm_key,
            "VM Name": sample_vm_model.vm_name,
            "Owner": "alice",
            "Blocker Type": "Type F",
            "Blocker Description": "Desc F",
            "Status": "Resolved",
            "Due Date": "2024-10-30",
            "Notes": "Note F",
        },
    ]
    
    backlog_df = pd.DataFrame(backlog_items)
    
    # Extract summary metrics
    status_counts = backlog_df["Status"].value_counts().to_dict()
    owner_counts = backlog_df["Owner"].fillna("").value_counts().to_dict()
    
    # Create summary output
    output = "BACKLOG SUMMARY\n"
    output += "=" * 50 + "\n\n"
    
    output += "Status Counts:\n"
    for status in sorted(status_counts.keys()):
        output += f"  {status}: {status_counts[status]}\n"
    
    output += "\nOwner Counts:\n"
    for owner in sorted(owner_counts.keys()):
        output += f"  {owner}: {owner_counts[owner]}\n"
    
    output += f"\nTotal Blockers: {len(backlog_df)}\n"
    
    assert_matches_snapshot("remediation_backlog_summary.txt", output)


def test_remediation_export_with_missing_vm_data(assert_matches_snapshot):
    """Test export when remediation tracker includes blockers for VMs not in the VMs list."""
    vms = [
        {
            "VM Key": "vm-found",
            "VM Name": "found-vm",
            "Owner": "team-a",
            "Power State": "poweredOn",
        },
    ]
    
    # Include blocker for a VM not in the vms list
    remediation_tracker = {
        "vm-found::blocker1": {
            "status": "Open",
            "due_date": "2024-12-31",
            "notes": "For known VM",
            "owner": "team-a",
            "blocker_type": "Type A",
            "blocker_description": "Blocker for found VM",
        },
        "vm-not-found::blocker1": {
            "status": "In Progress",
            "due_date": "2024-12-15",
            "notes": "For unknown VM",
            "owner": "unknown-team",
            "blocker_type": "Type B",
            "blocker_description": "Blocker for missing VM",
        },
    }
    
    # Generate CSV export
    csv_output = remediation_tracker_export(vms, remediation_tracker)
    
    assert_matches_snapshot("remediation_export_missing_vm.csv", csv_output)


def test_remediation_export_empty_tracker(assert_matches_snapshot):
    """Test export with empty remediation tracker."""
    vms = [
        {
            "VM Key": "vm-001",
            "VM Name": "test-vm",
            "Owner": "team-a",
            "Power State": "poweredOn",
        },
    ]
    
    remediation_tracker = {}
    
    # Generate CSV export
    csv_output = remediation_tracker_export(vms, remediation_tracker)
    
    assert_matches_snapshot("remediation_export_empty.csv", csv_output)


def test_remediation_export_special_characters(assert_matches_snapshot):
    """Test export with special characters in descriptions and notes."""
    vms = [
        {
            "VM Key": "vm-special",
            "VM Name": "special-char-vm",
            "Owner": "team-a",
            "Power State": "poweredOn",
        },
    ]
    
    remediation_tracker = {
        "vm-special::blocker1": {
            "status": "Open",
            "due_date": "2024-12-31",
            "notes": 'Contains "quotes", commas, and newline\ncharacters',
            "owner": "team-a",
            "blocker_type": "Special Characters",
            "blocker_description": "Description with 'apostrophes' & ampersands",
        },
        "vm-special::blocker2": {
            "status": "In Progress",
            "due_date": "2024-11-30",
            "notes": "Unicode: café, naïve, résumé",
            "owner": "team-a",
            "blocker_type": "Unicode Test",
            "blocker_description": "Test unicode characters: 测试, Тест",
        },
    }
    
    # Generate CSV export
    csv_output = remediation_tracker_export(vms, remediation_tracker)
    
    assert_matches_snapshot("remediation_export_special_chars.csv", csv_output)
