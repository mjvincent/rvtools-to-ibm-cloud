import csv
import io
from datetime import datetime

from models import MigrationVm

from .utils import _clean_value, _normalize_vms, _safe_vm_key


def remediation_tracker_export(
    vms: list[MigrationVm],
    remediation_tracker: dict,
    today=None,
) -> str:
    """Generate a CSV capturing remediation blockers and their resolution tracking.
    
    Columns:
    VM Key, VM Name, Owner, Blocker Type, Blocker Description, Status, Due Date, Notes
    
    Summary section includes:
    - Counts by status
    - Counts by owner
    - Overdue items count
    
    remediation_tracker format: {blocker_id: {status, due_date, notes, owner}, ...}
    Each blocker_id should follow pattern: {vm_key}:{blocker_type}:{description_hash}
    """
    final_vms = _normalize_vms(vms)
    remediation_tracker = remediation_tracker or {}
    
    output = io.StringIO()
    fieldnames = [
        "VM Key", "VM Name", "Owner", "Blocker Type", "Blocker Description",
        "Status", "Due Date", "Notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Build a mapping of vm_key to vm for quick lookup
    vm_map = {}
    for vm in final_vms:
        vm_key = _clean_value(vm.get('vm_key')) or _clean_value(vm.get('VM Key'))
        if vm_key:
            vm_map[vm_key] = vm
    
    # Track summary stats
    status_counts = {}
    owner_counts = {}
    overdue_count = 0
    today = today or datetime.now().date()
    
    # Process each blocker
    rows_data = []
    for blocker_id, blocker_info in sorted(remediation_tracker.items()):
        if not isinstance(blocker_info, dict):
            continue
        
        # Parse blocker_id format: {vm_key}:{blocker_type}:{description_hash}
        # or just store as-is if it doesn't follow pattern
        parts = str(blocker_id).split(':', 1)
        vm_key = parts[0] if parts else ""
        
        # Get VM details
        vm = vm_map.get(vm_key, {})
        if not vm:
            # Still include blockers even if VM not found
            vm = {"vm_key": vm_key, "vm_name": ""}
        
        vm_key_out = _clean_value(vm.get('vm_key')) or _clean_value(vm.get('VM Key')) or vm_key
        vm_name = _safe_vm_key(vm.get('vm_name')) or _safe_vm_key(vm.get('VM Name'))
        
        # Get blocker-specific fields
        owner = _clean_value(blocker_info.get('owner'))
        blocker_type = _clean_value(blocker_info.get('blocker_type')) or _clean_value(blocker_info.get('type'))
        blocker_desc = _clean_value(blocker_info.get('blocker_description')) or _clean_value(blocker_info.get('description'))
        status = _clean_value(blocker_info.get('status'), 'Open')
        due_date = _clean_value(blocker_info.get('due_date'))
        notes = _clean_value(blocker_info.get('notes'))
        
        # Update summary stats
        status_counts[status] = status_counts.get(status, 0) + 1
        if owner:
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
        
        # Check if overdue
        if due_date:
            try:
                due = datetime.strptime(str(due_date), '%Y-%m-%d').date()
                if due < today and status.lower() not in ['closed', 'resolved', 'complete']:
                    overdue_count += 1
            except (ValueError, TypeError):
                pass
        
        rows_data.append({
            "VM Key": vm_key_out,
            "VM Name": vm_name,
            "Owner": owner,
            "Blocker Type": blocker_type,
            "Blocker Description": blocker_desc,
            "Status": status,
            "Due Date": due_date,
            "Notes": notes,
        })
    
    # Write all blocker rows
    for row in rows_data:
        writer.writerow(row)
    
    # Write summary section
    # Blank row
    writer.writerow({
        "VM Key": "", "VM Name": "", "Owner": "", "Blocker Type": "",
        "Blocker Description": "", "Status": "", "Due Date": "", "Notes": "",
    })
    
    # Summary header
    writer.writerow({
        "VM Key": "", "VM Name": "SUMMARY", "Owner": "", "Blocker Type": "",
        "Blocker Description": "", "Status": "", "Due Date": "", "Notes": "",
    })
    
    # Status counts
    for status in sorted(status_counts.keys()):
        writer.writerow({
            "VM Key": "", "VM Name": f"Status: {status}", "Owner": "",
            "Blocker Type": "", "Blocker Description": "",
            "Status": status_counts[status], "Due Date": "", "Notes": "",
        })
    
    # Owner counts
    for owner in sorted(owner_counts.keys()):
        writer.writerow({
            "VM Key": "", "VM Name": f"Owner: {owner}", "Owner": "",
            "Blocker Type": "", "Blocker Description": "",
            "Status": owner_counts[owner], "Due Date": "", "Notes": "",
        })
    
    # Overdue count
    writer.writerow({
        "VM Key": "", "VM Name": "Overdue Items", "Owner": "",
        "Blocker Type": "", "Blocker Description": "",
        "Status": overdue_count, "Due Date": "", "Notes": "",
    })
    
    # Total count
    total_blockers = len(rows_data)
    writer.writerow({
        "VM Key": "", "VM Name": "TOTAL BLOCKERS", "Owner": "",
        "Blocker Type": "", "Blocker Description": "",
        "Status": total_blockers, "Due Date": "", "Notes": "",
    })
    
    return output.getvalue()

