import pandas as pd
import streamlit as st

from handoff import image_import_export
from streamlit_app.final_vms import build_final_vms


IMPORT_STATUS_OPTIONS = [
    "",
    "Pending",
    "Scheduled",
    "Imported",
    "Failed",
    "Review",
]


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


def apply_bulk_import_status(image_import_status, selected_images, bulk_status):
    """Apply an import status to selected source image groups."""
    updated = dict(image_import_status)
    for source in selected_images:
        current = dict(updated.get(source, {}))
        current["import_status"] = bulk_status
        updated[source] = current
    return updated


def render_image_import_tab(edited_df, processed_vms, disk_details, nic_details):
    """Render Image Import Planning and update session state."""
    st.subheader("Image Import Planning")
    st.caption("Group active VMs by inferred source image and track import status.")

    if "image_import_status" not in st.session_state:
        st.session_state["image_import_status"] = {}

    df_images = build_image_import_rows(
        edited_df,
        st.session_state["image_import_status"],
    )

    if df_images.empty:
        st.info("No active VMs to plan image imports for.")
        return

    col_cfg = {
        "Source Image": st.column_config.TextColumn(
            "Source Image", disabled=True
        ),
        "Count of VMs": st.column_config.NumberColumn(
            "Count of VMs", disabled=True
        ),
        "Owners": st.column_config.TextColumn("Owners", disabled=True),
        "Target Catalog ID": st.column_config.TextColumn("Target Catalog ID"),
        "Import Status": st.column_config.SelectboxColumn(
            "Import Status",
            options=IMPORT_STATUS_OPTIONS,
        ),
        "Estimated Import Time": st.column_config.TextColumn(
            "Estimated Import Time"
        ),
        "Notes": st.column_config.TextColumn("Notes"),
    }

    edited_images = st.data_editor(
        df_images,
        column_config=col_cfg,
        hide_index=True,
        use_container_width=True,
        key="image_import_editor",
    )

    st.session_state["image_import_status"] = persist_image_import_edits(
        edited_images,
        st.session_state["image_import_status"],
    )

    st.write("---")
    st.subheader("Bulk Actions")
    image_options = df_images["Source Image"].tolist()
    selected_images = st.multiselect(
        "Select images to update",
        image_options,
        default=st.session_state.get("image_import_selected", []),
        key="image_import_multiselect",
    )
    st.session_state["image_import_selected"] = selected_images

    c1, c2 = st.columns([2, 6])
    with c1:
        bulk_status = st.selectbox(
            "Set Import Status",
            IMPORT_STATUS_OPTIONS,
            key="bulk_image_status",
        )
        if st.button("Apply Status to Selected", use_container_width=True):
            if not selected_images:
                st.warning("No images selected.")
            else:
                st.session_state["image_import_status"] = (
                    apply_bulk_import_status(
                        st.session_state["image_import_status"],
                        selected_images,
                        bulk_status,
                    )
                )
                st.success(
                    f"Updated import status for {len(selected_images)} images."
                )

    with c2:
        if st.button("Generate Image Import Export", use_container_width=True):
            csv_text = image_import_export(
                build_final_vms(
                    edited_df, processed_vms, disk_details, nic_details
                ),
                st.session_state.get("image_import_status"),
            )
            st.session_state["last_image_import_csv"] = csv_text

        if st.session_state.get("last_image_import_csv"):
            st.download_button(
                label="Download Image Import CSV",
                data=st.session_state.get("last_image_import_csv").encode(
                    "utf-8"
                ),
                file_name="image-import-plan.csv",
                mime="text/csv",
                use_container_width=True,
                key="image_import_export_download",
            )
