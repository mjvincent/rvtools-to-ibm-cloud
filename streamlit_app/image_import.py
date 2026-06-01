import pandas as pd


def build_image_import_rows(edited_df, image_import_status):
    active_images = edited_df[~edited_df["Exclude?"]].copy()
    groups = {}
    for _, row in active_images.iterrows():
        source = str(row.get("Original Specs") or row.get("VM Name"))
        entry = groups.setdefault(source, {"vms": [], "owners": set()})
        entry["vms"].append(row)
        owner = row.get("Owner") or row.get("owner") or ""
        if owner:
            entry["owners"].add(owner)

    rows = []
    for source in sorted(groups.keys()):
        entry = groups[source]
        state = image_import_status.get(source, {})
        rows.append({
            "Source Image": source,
            "Count of VMs": len(entry["vms"]),
            "Owners": (
                "; ".join(sorted(entry["owners"]))
                if entry["owners"] else ""
            ),
            "Target Catalog ID": state.get("target_catalog_id", ""),
            "Import Status": state.get("import_status", ""),
            "Estimated Import Time": state.get("estimated_import_time", ""),
            "Notes": state.get("notes", ""),
        })
    return pd.DataFrame(rows)


def persist_image_import_edits(edited_images, image_import_status):
    if not isinstance(edited_images, pd.DataFrame):
        return image_import_status
    for row in edited_images.to_dict("records"):
        source = row.get("Source Image")
        if not source:
            continue
        image_import_status[source] = {
            "target_catalog_id": row.get("Target Catalog ID", ""),
            "import_status": row.get("Import Status", ""),
            "estimated_import_time": row.get("Estimated Import Time", ""),
            "notes": row.get("Notes", ""),
        }
    return image_import_status

