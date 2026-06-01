"""Test wave field parsing, editing, and roundtrip functionality."""
import csv
import io

from models import MigrationVm


def test_parse_wave_fields_from_record():
    """Verify MigrationVm.from_record() correctly maps wave fields."""
    record = {
        "VM Key": "vm-001",
        "VM Name": "app-01",
        "Power State": "poweredOn",
        "Source IP": "10.0.1.10",
        "Network": "app-net",
        "Guest OS": "Red Hat Enterprise Linux 9 (64-bit)",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "3iops-tier",
        "wave": "Wave 1",
        "cutover_group": "CG-A",
        "owner": "John Doe",
        "application": "Web Server",
        "priority": "P1",
        "dependency_group": "DG-01",
    }

    vm = MigrationVm.from_record(record)

    # Verify wave fields are correctly parsed
    assert vm.wave == "Wave 1"
    assert vm.cutover_group == "CG-A"
    assert vm.owner == "John Doe"
    assert vm.application == "Web Server"
    assert vm.priority == "P1"
    assert vm.dependency_group == "DG-01"

    # Verify other required fields are still parsed
    assert vm.vm_name == "app-01"
    assert vm.power_state == "poweredOn"
    assert vm.guest_os == "Red Hat Enterprise Linux 9 (64-bit)"


def test_wave_field_roundtrip():
    """Test wave field roundtrip: parse → edit → export → re-import → verify."""
    # Create a CSV with wave fields
    csv_data = """VM Key,VM Name,Power State,Source IP,Network,Guest OS,IBM Profile,Storage Tier,Disk Count,Total Storage GB,wave,cutover_group,owner,application,priority,dependency_group
vm-001,app-01,poweredOn,10.0.1.10,app-net,Red Hat Enterprise Linux 9 (64-bit),bx2-2x8,3iops-tier,2,200,Wave 1,CG-A,John Doe,Web Server,P1,DG-01
vm-002,app-02,poweredOn,10.0.1.11,app-net,Red Hat Enterprise Linux 8 (64-bit),bx2-4x16,3iops-tier,1,100,,CG-B,Jane Smith,Database,P2,
"""

    # Parse the CSV
    reader = csv.DictReader(io.StringIO(csv_data))
    records = list(reader)
    assert len(records) == 2

    # Create VMs from records
    vms = [MigrationVm.from_record(record) for record in records]

    # Verify wave fields were parsed correctly
    assert vms[0].wave == "Wave 1"
    assert vms[0].cutover_group == "CG-A"
    assert vms[0].owner == "John Doe"
    assert vms[0].application == "Web Server"
    assert vms[0].priority == "P1"
    assert vms[0].dependency_group == "DG-01"

    assert vms[1].wave == ""  # Empty wave field
    assert vms[1].cutover_group == "CG-B"
    assert vms[1].owner == "Jane Smith"
    assert vms[1].application == "Database"
    assert vms[1].priority == "P2"
    assert vms[1].dependency_group == ""  # Empty dependency_group

    # Edit wave fields in memory
    vms[0].wave = "Wave 2"
    vms[0].priority = "P0"
    vms[1].wave = "Wave 1"
    vms[1].dependency_group = "DG-02"

    # Export to CSV
    exported_records = [vm.to_record() for vm in vms]

    # Re-import from exported records
    reimported_vms = [MigrationVm.from_record(record) for record in exported_records]

    # Verify wave fields survived the roundtrip
    assert reimported_vms[0].wave == "Wave 2"
    assert reimported_vms[0].priority == "P0"
    assert reimported_vms[0].cutover_group == "CG-A"
    assert reimported_vms[0].owner == "John Doe"
    assert reimported_vms[0].application == "Web Server"
    assert reimported_vms[0].dependency_group == "DG-01"

    assert reimported_vms[1].wave == "Wave 1"
    assert reimported_vms[1].dependency_group == "DG-02"
    assert reimported_vms[1].cutover_group == "CG-B"
    assert reimported_vms[1].owner == "Jane Smith"
    assert reimported_vms[1].application == "Database"
    assert reimported_vms[1].priority == "P2"


def test_wave_field_empty_values():
    """Test that empty wave fields are handled correctly."""
    record = {
        "VM Key": "vm-003",
        "VM Name": "test-vm",
        "Power State": "poweredOn",
        "Source IP": "10.0.1.20",
        "Network": "test-net",
        "Guest OS": "Windows Server 2022",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "3iops-tier",
        "wave": "",
        "cutover_group": "",
        "owner": "",
        "application": "",
        "priority": "",
        "dependency_group": "",
    }

    vm = MigrationVm.from_record(record)

    # Verify empty fields are handled as empty strings
    assert vm.wave == ""
    assert vm.cutover_group == ""
    assert vm.owner == ""
    assert vm.application == ""
    assert vm.priority == ""
    assert vm.dependency_group == ""

    # Verify the VM can be exported and re-imported with empty fields
    exported = vm.to_record()
    reimported = MigrationVm.from_record(exported)

    assert reimported.wave == ""
    assert reimported.cutover_group == ""
    assert reimported.owner == ""
    assert reimported.application == ""
    assert reimported.priority == ""
    assert reimported.dependency_group == ""


def test_wave_field_missing_from_record():
    """Test that missing wave fields default to empty strings."""
    record = {
        "VM Key": "vm-004",
        "VM Name": "legacy-vm",
        "Power State": "poweredOn",
        "Source IP": "10.0.1.30",
        "Network": "legacy-net",
        "Guest OS": "Windows Server 2016",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "3iops-tier",
        # No wave fields provided
    }

    vm = MigrationVm.from_record(record)

    # Verify missing fields default to empty strings
    assert vm.wave == ""
    assert vm.cutover_group == ""
    assert vm.owner == ""
    assert vm.application == ""
    assert vm.priority == ""
    assert vm.dependency_group == ""
