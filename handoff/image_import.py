import csv
import io

from models import MigrationVm

from .utils import _clean_value, _normalize_vms, _safe_vm_key


def generate_image_import_tfvars(final_vms):
    """Create an example tfvars map for imported IBM Cloud custom images."""
    final_vms = _normalize_vms(final_vms)
    lines = [
        "# Populate these values after VMware images are converted, uploaded,",
        "# and imported as IBM Cloud VPC custom images.",
        "# Copy this file, replace every placeholder, and pass it to Terraform",
        "# with -var-file when provisioning VSIs from the imported images.",
        "custom_image_ids = {",
    ]
    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        lines.append(f'  "{vm_name}" = "replace-with-imported-image-id"')
    lines.append("}")
    return "\n".join(lines) + "\n"


def image_import_export(vms: list[MigrationVm], image_import_status: dict = None) -> str:
    """Generate a CSV to plan image imports grouped by source image.

    Columns:
    Source Image, Count of VMs, Owners, Target Catalog ID,
    Import Status, Estimated Import Time, Notes

    image_import_status may be a mapping keyed by source image or VM key.
    """
    final_vms = _normalize_vms(vms)
    image_import_status = image_import_status or {}

    # Group VMs by inferred source image (fallback to VM name when missing)
    groups = {}
    total_vms = 0
    for vm in final_vms:
        vm_name = _safe_vm_key(vm.get('VM Name'))
        source_image = _clean_value(vm.get('Original Specs')) or vm_name
        entry = groups.setdefault(source_image, {"vms": [], "owners": set()})
        entry["vms"].append(vm)
        owner = _clean_value(vm.get('owner')) or _clean_value(vm.get('Owner'))
        if owner:
            entry["owners"].add(owner)

    output = io.StringIO()
    fieldnames = [
        "Source Image", "Count of VMs", "Owners",
        "Target Catalog ID", "Import Status", "Estimated Import Time", "Notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for source in sorted(groups.keys()):
        entry = groups[source]
        count = len(entry["vms"])
        total_vms += count
        owners = "; ".join(sorted(entry["owners"])) if entry["owners"] else ""

        # Resolve status info from image_import_status mapping.
        target_catalog_id = ""
        import_status = ""
        estimated_time = ""
        notes = ""

        if isinstance(image_import_status, dict):
            val = image_import_status.get(source)
            if val is None:
                # try per-VM keys
                for vm in entry["vms"]:
                    vm_key = _safe_vm_key(vm.get('VM Name'))
                    if vm_key in image_import_status:
                        val = image_import_status.get(vm_key)
                        break
            if isinstance(val, dict):
                target_catalog_id = _clean_value(val.get('target_catalog_id'))
                import_status = _clean_value(val.get('import_status')) or _clean_value(val.get('status'))
                estimated_time = _clean_value(val.get('estimated_import_time')) or _clean_value(val.get('estimated_time'))
                notes = _clean_value(val.get('notes'))
            elif val is not None:
                import_status = _clean_value(val)

        writer.writerow({
            "Source Image": source,
            "Count of VMs": count,
            "Owners": owners,
            "Target Catalog ID": target_catalog_id,
            "Import Status": import_status,
            "Estimated Import Time": estimated_time,
            "Notes": notes,
        })

    # summary row
    writer.writerow({
        "Source Image": "TOTAL",
        "Count of VMs": total_vms,
        "Owners": "",
        "Target Catalog ID": "",
        "Import Status": "",
        "Estimated Import Time": "",
        "Notes": "",
    })

    return output.getvalue()


