import io
import zipfile

import pandas as pd
import streamlit as st

from catalog_pricing import get_pricing_catalog, pricing_status_summary
from assessment_quality import (
    generate_assessment_quality_csv,
    generate_assessment_quality_json,
)
from handoff import (
    decision_audit_export,
    generate_disk_mapping_csv,
    generate_image_import_tfvars,
    image_import_export,
    generate_memory_readiness_csv,
    generate_migration_manifest,
    generate_migration_runbook,
    generate_nic_mapping_csv,
    generate_partition_mapping_csv,
    generate_pricing_diagnostics_csv,
    generate_pricing_diagnostics_json,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
    remediation_tracker_export,
)
from models import MigrationVm
from preflight import (
    generate_preflight_report_csv,
    generate_preflight_report_json,
    has_blockers,
    run_package_preflight,
)
from rvtools_parser import normalize_network_name, parse_rvtools_workbook
from terraform_renderer import generate_tfvars, render_terraform_templates
from ui import (
    DECISION_COLUMNS,
    DISABLED_COLS,
    apply_preflight_quick_fixes,
    build_table_config,
    merge_decision_edits,
    render_assessment_quality,
    render_estate_summary,
    render_network_planning,
    render_preflight_guidance,
    render_readiness_legend,
    render_readiness_triage,
    render_storage_planning,
)


st.set_page_config(
    page_title="IBM Cloud Terraform Generator",
    layout="wide"
)

col1, col2 = st.columns([1, 8])
with col1:
    logo = (
        "https://upload.wikimedia.org/wikipedia/commons/5/51/"
        "IBM_logo.svg"
    )
    st.image(logo, width=80)
with col2:
    st.title("RVTools to IBM Cloud VPC")

st.sidebar.header("Migration Settings")
target_region = st.sidebar.selectbox(
    "Target IBM Region", ["us-south", "us-east", "eu-gb", "jp-tok"]
)

st.sidebar.header("Right-Sizing Settings")
modes = [
    "Conservative (30%)", "IBM Standard (40%)",
    "Moderate (50%)", "Aggressive (70%)", "Custom"
]
threshold_mode = st.sidebar.selectbox("Standard Thresholds", modes, index=1)
if threshold_mode == "Custom":
    utilization_threshold = st.sidebar.slider(
        "Custom CPU Threshold (%)", 1, 100, 40
    )
else:
    utilization_threshold = int(''.join(filter(
        str.isdigit, threshold_mode
    )))

project_name = st.sidebar.text_input("Project Name", "my-ibm-migration")
region_zones = {
    "us-south": ["us-south-1", "us-south-2", "us-south-3"],
    "us-east": ["us-east-1", "us-east-2", "us-east-3"],
    "eu-gb": ["eu-gb-1"],
    "jp-tok": ["jp-tok-1"]
}
target_zone = st.sidebar.selectbox(
    "Target IBM Zone",
    region_zones.get(target_region, [f"{target_region}-1"])
)

st.sidebar.header("Pricing Settings")
pricing_mode_label = st.sidebar.selectbox(
    "Pricing Mode",
    ["Static fallback", "Cached IBM catalog", "Live IBM profile discovery"],
    index=0
)
pricing_mode_map = {
    "Static fallback": "static",
    "Cached IBM catalog": "cached",
    "Live IBM profile discovery": "live",
}
pricing_catalog = get_pricing_catalog(
    pricing_mode_map[pricing_mode_label],
    region=target_region
)
pricing_metadata = pricing_catalog.get("metadata", {})
catalog_profiles = pricing_catalog.get("profiles", [])
storage_tier_rates = pricing_catalog.get("storage_tier_rates")
st.sidebar.caption(pricing_status_summary(pricing_catalog))
if pricing_metadata.get("status"):
    st.sidebar.info(pricing_metadata["status"])

generate_security_groups = st.sidebar.checkbox(
    "Generate Security Groups", value=True
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Upload RVTools, review blockers first, adjust only the decisions that "
    "need human intent, then build the Terraform handoff package."
)
uploaded_file = st.sidebar.file_uploader("Upload RVTools", type=["xlsx"])

if uploaded_file is not None:
    parsed = parse_rvtools_workbook(
        uploaded_file,
        target_region,
        utilization_threshold,
        generate_security_groups,
        catalog_profiles=catalog_profiles,
        storage_tier_rates=storage_tier_rates,
        pricing_metadata=pricing_metadata,
    )

    processed_vms = parsed.processed_vms
    unique_nets = parsed.unique_nets
    disk_details = parsed.disk_details
    nic_details = parsed.nic_details
    assessment_quality = parsed.assessment_quality

    df_f = pd.DataFrame([vm.to_record() for vm in processed_vms])
    df_table = df_f.drop(
        columns=[
            "Disk Details", "Partition Details", "Network Details",
            "Readiness Findings"
        ],
        errors="ignore"
    )
    table_config = build_table_config(unique_nets, catalog_profiles)

    render_estate_summary(df_f)

    overview, readiness, remediation_backlog, vm_review, wave_planning, image_import, networks, storage, export = st.tabs([
        "Overview", "Readiness", "Remediation Backlog", "VM Review", "Wave Planning", "Image Import Planning", "Networks", "Storage", "Export"
    ])

    edited_df = df_table.copy()

    def build_final_vms(source_df):
        final_vm_records = [
            v for v in source_df.to_dict('records')
            if not v.get('Exclude?')
        ]
        final_vms = []
        for vm in final_vm_records:
            vm["Disk Details"] = disk_details.get(vm.get("VM Key"), [])
            vm["Partition Details"] = next(
                (
                    source.get("Partition Details", [])
                    for source in processed_vms
                    if source.get("VM Key") == vm.get("VM Key")
                ),
                []
            )
            vm["Network Details"] = nic_details.get(vm.get("VM Key"), [])
            vm["Readiness Findings"] = next(
                (
                    source.get("Readiness Findings", [])
                    for source in processed_vms
                    if source.get("VM Key") == vm.get("VM Key")
                ),
                []
            )
            final_vms.append(MigrationVm.from_record(vm))
        return final_vms

    with overview:
        st.subheader("Estate Health")
        active_df = df_f[~df_f['Exclude?']]
        c1, c2, c3 = st.columns(3)
        c1.metric("Image Blocked", len(active_df[active_df["Image Readiness"] == "Blocked"]))
        c2.metric("Migration Blocked", len(active_df[active_df["Migration Readiness"] == "Blocked"]))
        c3.metric("Memory Blocked", len(active_df[active_df["Memory Readiness"] == "Blocked"]))
        st.subheader("Recommended Next Actions")
        st.write("1. Resolve Blocked readiness items before migration execution.")
        st.write("2. Validate Review items with workload owners and VMware administrators.")
        st.write("3. Confirm profile, storage tier, network, subnet, and security group overrides in VM Review.")
        st.write("4. Confirm Terraform deployment settings in Export and build the package.")
        render_assessment_quality(assessment_quality)

    with readiness:
        render_readiness_legend()
        render_readiness_triage(df_f)

    with remediation_backlog:
        st.subheader("Remediation Backlog")
        st.caption("Track readiness blockers and remediation status.")

        # Session state persistence note
        st.info(
            "**Note:** Remediation tracker data is stored for this session only. "
            "To persist your tracking data across sessions, export the CSV below and re-import it by adding it back to the backlog."
        )

        # Initialize remediation tracker storage
        #
        # DESIGN: Remediation Tracker State Management
        # ============================================
        # Current Implementation: Session-only storage via st.session_state
        # - Storage Location: st.session_state["remediation_tracker"]
        # - Structure: {blocker_id: {status, due_date, notes, owner}, ...}
        # - Scope: Current session only; lost on page refresh or browser close
        # - Use Case: In-session tracking during migration planning workflow
        #
        # Future Persistence Design (JSON File Storage):
        # - File Location: {project_dir}/.remediation_tracker.json
        # - Format:
        #   {
        #     "metadata": {
        #       "version": "1.0",
        #       "project_name": "<project>",
        #       "export_timestamp": "2024-01-15T10:30:00Z"
        #     },
        #     "blockers": {
        #       "<blocker_id>": {
        #         "vm_key": "<vm_key>",
        #         "vm_name": "<vm_name>",
        #         "blocker_type": "<type>",
        #         "status": "Open|In Progress|Resolved|Deferred",
        #         "due_date": "YYYY-MM-DD",
        #         "notes": "<notes>",
        #         "owner": "<owner>",
        #         "created_at": "2024-01-15T10:00:00Z",
        #         "updated_at": "2024-01-15T10:30:00Z"
        #       }
        #     }
        #   }
        # - Implementation Strategy:
        #   1. Add load_remediation_state(project_dir) to handoff.py
        #   2. Add save_remediation_state(state, project_dir) to handoff.py
        #   3. Load on app init if exists
        #   4. Provide import/export buttons in Remediation Backlog tab
        #   5. Auto-save after editor changes (with confirmation)
        if "remediation_tracker" not in st.session_state:
            st.session_state["remediation_tracker"] = {}

        # Collect blockers from VM readiness findings
        backlog_items = []
        _counter = 0
        for vm in processed_vms:
            # Aggregate findings from various readiness sources
            findings = []
            findings.extend(getattr(vm, "readiness_findings", []) or [])
            findings.extend(getattr(vm, "network_readiness_findings", []) or [])
            findings.extend(getattr(vm, "migration", {}).findings if getattr(vm, "migration", None) else [])
            for f in findings:
                blocker_id = f"{vm.vm_key}::{_counter}"
                _counter += 1
                desc = f.recommended_action or f.evidence or f.severity or ""
                state_entry = st.session_state["remediation_tracker"].get(blocker_id, {})
                backlog_items.append({
                    "blocker_id": blocker_id,
                    "VM Key": vm.vm_key,
                    "VM Name": vm.vm_name,
                    "Owner": vm.owner or "",
                    "Blocker Type": f.finding_type,
                    "Blocker Description": desc,
                    "Status": state_entry.get("status", "Open"),
                    "Due Date": state_entry.get("due_date", ""),
                    "Notes": state_entry.get("notes", ""),
                })

        if not backlog_items:
            st.info("No readiness blockers found.")
        else:
            backlog_df = pd.DataFrame(backlog_items)
            col_cfg = {
                "blocker_id": st.column_config.TextColumn("ID", disabled=True),
                "VM Key": st.column_config.TextColumn("VM Key", disabled=True),
                "VM Name": st.column_config.TextColumn("VM Name", disabled=True),
                "Owner": st.column_config.TextColumn("Owner"),
                "Blocker Type": st.column_config.TextColumn("Blocker Type", disabled=True),
                "Blocker Description": st.column_config.TextColumn("Blocker Description", disabled=True),
                "Status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Resolved", "Deferred"]),
                "Due Date": st.column_config.TextColumn("Due Date"),
                "Notes": st.column_config.TextColumn("Notes"),
            }

            edited_backlog = st.data_editor(
                backlog_df,
                column_config=col_cfg,
                hide_index=True,
                use_container_width=True,
                key="remediation_editor"
            )

            # Persist edits into session_state mapping
            if isinstance(edited_backlog, pd.DataFrame):
                for row in edited_backlog.to_dict("records"):
                    bid = row.get("blocker_id")
                    if not bid:
                        continue
                    st.session_state["remediation_tracker"][bid] = {
                        "status": row.get("Status", "Open"),
                        "due_date": row.get("Due Date", ""),
                        "notes": row.get("Notes", ""),
                        "owner": row.get("Owner", ""),
                    }

            # Summary section
            st.write("---")
            st.subheader("Backlog Summary")
            df_for_summary = edited_backlog if isinstance(edited_backlog, pd.DataFrame) else backlog_df
            status_counts = df_for_summary["Status"].value_counts().to_dict() if not df_for_summary.empty else {}
            owner_counts = df_for_summary["Owner"].fillna("").value_counts().to_dict() if not df_for_summary.empty else {}

            c1, c2, c3 = st.columns(3)
            c1.metric("Open", int(status_counts.get("Open", 0)))
            c2.metric("In Progress", int(status_counts.get("In Progress", 0)))
            c3.metric("Resolved", int(status_counts.get("Resolved", 0)))

            st.write("### By Owner")
            if owner_counts:
                owner_df = pd.DataFrame([{"Owner": k, "Count": v} for k, v in owner_counts.items()])
                st.dataframe(owner_df, use_container_width=True)
            else:
                st.write("No owners assigned yet.")

            # Overdue items
            try:
                due_parsed = pd.to_datetime(df_for_summary.get("Due Date", pd.Series([], dtype=object)), errors="coerce")
                overdue_mask = due_parsed < pd.Timestamp.now()
                overdue = df_for_summary.loc[overdue_mask]
                st.write(f"Overdue items: {len(overdue)}")
                if not overdue.empty:
                    st.dataframe(overdue[["VM Key", "VM Name", "Owner", "Blocker Type", "Blocker Description", "Status", "Due Date", "Notes"]], use_container_width=True)
            except Exception:
                # If parsing fails, skip overdue calculation
                pass

            # Export
            csv_bytes = df_for_summary.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Export Remediation Backlog",
                data=csv_bytes,
                file_name="p4-remediation-backlog.csv",
                mime="text/csv",
                use_container_width=True,
                key="p4-tracker-export"
            )

    with vm_review:
        st.subheader("VM Decisions")
        st.caption("This view keeps the active decisions in front. Raw generated fields remain available below for audit and troubleshooting.")
        decision_table = apply_preflight_quick_fixes(
            df_table,
            st.session_state.get("preflight_quick_fixes", {}),
        )
        decision_input_columns = ["VM Key"] + [
            column for column in DECISION_COLUMNS
            if column in decision_table.columns
        ]
        edited_decisions = st.data_editor(
            decision_table[decision_input_columns],
            column_config=table_config,
            column_order=[
                column for column in DECISION_COLUMNS
                if column in decision_table.columns
            ],
            disabled=[
                column for column in DISABLED_COLS
                if column in decision_input_columns
            ],
            hide_index=True,
            use_container_width=True,
            key="vm_decision_editor"
        )
        edited_df = merge_decision_edits(decision_table, edited_decisions)
        with st.expander("Advanced generated fields"):
            st.dataframe(edited_df, hide_index=True, use_container_width=True)

    with wave_planning:
        st.subheader("Wave Planning")
        st.caption("Bulk assign waves, cutover groups, owners, and applications to active VMs.")

        # Prepare active VMs table
        active_df = edited_df[~edited_df['Exclude?']].copy()
        # Ensure wave planning columns exist
        for col in ["Wave", "Cutover Group", "Owner", "Application", "Priority", "Dependency Group"]:
            if col not in active_df.columns:
                active_df[col] = "" if col != "Priority" else "Medium"

        # Selection controls
        st.write("### Select VMs to assign")
        vm_options = active_df["VM Key"].tolist()
        selected = st.multiselect(
            "Select VMs (by VM Key)", vm_options,
            default=st.session_state.get("wave_selected_vms", [])
        )
        st.session_state["wave_selected_vms"] = selected

        c1, c2, c3 = st.columns([2, 2, 6])
        with c1:
            assign_wave_value = st.text_input("Quick Wave Value", "")
            if st.button("Assign All to Wave", use_container_width=True):
                if assign_wave_value:
                    edited_df.loc[~edited_df['Exclude?'], 'Wave'] = assign_wave_value
                    st.success(f"Assigned wave '{assign_wave_value}' to all active VMs")
                else:
                    st.warning("Enter a Wave value to assign to all active VMs.")
        with c2:
            if st.button("Assign Wave", use_container_width=True):
                st.session_state["show_assign_wave_form"] = True
        with c3:
            st.write("")

        # Bulk assign form
        if st.session_state.get("show_assign_wave_form"):
            with st.form("assign_wave_form"):
                st.write("Assign fields to selected VMs")
                f_wave = st.text_input("Wave")
                f_cut = st.text_input("Cutover Group")
                f_owner = st.text_input("Owner")
                f_app = st.text_input("Application")
                submitted = st.form_submit_button("Apply to Selected VMs")
                if submitted:
                    if not selected:
                        st.warning("No VMs selected for assignment.")
                    else:
                        for vmk in selected:
                            mask = edited_df['VM Key'] == vmk
                            if f_wave:
                                edited_df.loc[mask, 'Wave'] = f_wave
                            if f_cut:
                                edited_df.loc[mask, 'Cutover Group'] = f_cut
                            if f_owner:
                                edited_df.loc[mask, 'Owner'] = f_owner
                            if f_app:
                                edited_df.loc[mask, 'Application'] = f_app
                        st.success(f"Assigned fields to {len(selected)} VMs")
                        st.session_state["show_assign_wave_form"] = False

        # Configure columns for data editor using existing table_config where possible
        wave_table_cfg = dict(table_config)
        wave_table_cfg.update({
            "VM Key": st.column_config.TextColumn("VM Key", disabled=True),
            "VM Name": st.column_config.TextColumn("VM Name", disabled=True),
            "Wave": st.column_config.TextColumn("Wave"),
            "Cutover Group": st.column_config.TextColumn("Cutover Group"),
            "Owner": st.column_config.TextColumn("Owner"),
            "Application": st.column_config.TextColumn("Application"),
            "Priority": st.column_config.SelectboxColumn("Priority", options=["", "High", "Medium", "Low"]),
            "Dependency Group": st.column_config.TextColumn("Dependency Group"),
        })

        # Display editable grid
        display_cols = [
            "VM Key", "VM Name", "Wave", "Cutover Group", "Owner",
            "Application", "Priority", "Dependency Group"
        ]
        wave_editor = st.data_editor(
            active_df[display_cols],
            column_config=wave_table_cfg,
            hide_index=True,
            use_container_width=True,
            key="wave_planning_editor"
        )

        # Persist edits back to edited_df by VM Key
        if isinstance(wave_editor, pd.DataFrame):
            for row in wave_editor.to_dict('records'):
                vmk = row.get('VM Key')
                mask = edited_df['VM Key'] == vmk
                for col in ["Wave", "Cutover Group", "Owner", "Application", "Priority", "Dependency Group"]:
                    if col in row:
                        edited_df.loc[mask, col] = row.get(col)

        # Conflict detection
        st.write("### Conflict Detection")
        # Application vs Cutover Group
        app_conflicts = []
        apps = active_df.groupby('Application') if 'Application' in active_df.columns else []
        for app, group in apps:
            vals = set(group['Cutover Group'].dropna().astype(str).unique())
            vals = {v for v in vals if v}
            if len(vals) > 1:
                app_conflicts.append((app, vals))
        if app_conflicts:
            for app, vals in app_conflicts:
                st.warning(f"Application '{app}' has multiple Cutover Groups: {', '.join(vals)}")

        # Dependency Group vs Wave
        dep_conflicts = []
        deps = active_df.groupby('Dependency Group') if 'Dependency Group' in active_df.columns else []
        for dep, group in deps:
            vals = set(group['Wave'].dropna().astype(str).unique())
            vals = {v for v in vals if v}
            if len(vals) > 1:
                dep_conflicts.append((dep, vals))
        if dep_conflicts:
            for dep, vals in dep_conflicts:
                st.warning(f"Dependency Group '{dep}' spans multiple Waves: {', '.join(vals)}")

        # Completion status
        total = len(active_df)
        if total:
            required = ["Wave", "Cutover Group", "Owner", "Application"]
            complete = 0
            for _, r in edited_df[~edited_df['Exclude?']].iterrows():
                if all(r.get(c) not in (None, "") for c in required):
                    complete += 1
            if complete == total:
                st.success(f"Complete: {complete}/{total} VMs")
            else:
                st.info(f"Incomplete: {complete}/{total} VMs")

        # Expose advanced fields for audit
        with st.expander("Advanced wave planning data"):
            st.dataframe(edited_df[["VM Key", "VM Name", "Wave", "Cutover Group", "Owner", "Application", "Priority", "Dependency Group"]], hide_index=True, use_container_width=True)

    with networks:
        render_network_planning(edited_df, unique_nets)

    with storage:
        render_storage_planning(edited_df, processed_vms)

    with image_import:
        st.subheader("Image Import Planning")
        st.caption("Group active VMs by inferred source image and track import status.")

        # Initialize image import status storage
        if "image_import_status" not in st.session_state:
            st.session_state["image_import_status"] = {}

        # Build groups from active VMs
        active_images = edited_df[~edited_df['Exclude?']].copy()
        groups = {}
        for _, r in active_images.iterrows():
            source = r.get("Original Specs") or r.get("VM Name")
            source = str(source)
            entry = groups.setdefault(source, {"vms": [], "owners": set()})
            entry["vms"].append(r)
            owner = r.get("Owner") or r.get("owner") or ""
            if owner:
                entry["owners"].add(owner)

        rows = []
        for source in sorted(groups.keys()):
            entry = groups[source]
            count = len(entry["vms"])
            owners = "; ".join(sorted(entry["owners"])) if entry["owners"] else ""
            state = st.session_state["image_import_status"].get(source, {})
            rows.append({
                "Source Image": source,
                "Count of VMs": count,
                "Owners": owners,
                "Target Catalog ID": state.get("target_catalog_id", ""),
                "Import Status": state.get("import_status", ""),
                "Estimated Import Time": state.get("estimated_import_time", ""),
                "Notes": state.get("notes", ""),
            })

        if not rows:
            st.info("No active VMs to plan image imports for.")
        else:
            df_images = pd.DataFrame(rows)

            col_cfg = {
                "Source Image": st.column_config.TextColumn("Source Image", disabled=True),
                "Count of VMs": st.column_config.NumberColumn("Count of VMs", disabled=True),
                "Owners": st.column_config.TextColumn("Owners", disabled=True),
                "Target Catalog ID": st.column_config.TextColumn("Target Catalog ID"),
                "Import Status": st.column_config.SelectboxColumn(
                    "Import Status",
                    options=["", "Pending", "Scheduled", "Imported", "Failed", "Review"],
                ),
                "Estimated Import Time": st.column_config.TextColumn("Estimated Import Time"),
                "Notes": st.column_config.TextColumn("Notes"),
            }

            edited_images = st.data_editor(
                df_images,
                column_config=col_cfg,
                hide_index=True,
                use_container_width=True,
                key="image_import_editor",
            )

            # Persist edits into session_state mapping keyed by Source Image
            if isinstance(edited_images, pd.DataFrame):
                for row in edited_images.to_dict("records"):
                    src = row.get("Source Image")
                    if not src:
                        continue
                    st.session_state["image_import_status"][src] = {
                        "target_catalog_id": row.get("Target Catalog ID", ""),
                        "import_status": row.get("Import Status", ""),
                        "estimated_import_time": row.get("Estimated Import Time", ""),
                        "notes": row.get("Notes", ""),
                    }

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
                    ["", "Pending", "Scheduled", "Imported", "Failed", "Review"],
                    key="bulk_image_status",
                )
                if st.button("Apply Status to Selected", use_container_width=True):
                    if not selected_images:
                        st.warning("No images selected.")
                    else:
                        for src in selected_images:
                            cur = st.session_state["image_import_status"].get(src, {})
                            cur["import_status"] = bulk_status
                            st.session_state["image_import_status"][src] = cur
                        st.success(f"Updated import status for {len(selected_images)} images.")

            with c2:
                if st.button("Generate Image Import Export", use_container_width=True):
                    csv_text = image_import_export(build_final_vms(edited_df), st.session_state.get("image_import_status"))
                    st.session_state["last_image_import_csv"] = csv_text

                if st.session_state.get("last_image_import_csv"):
                    st.download_button(
                        label="Download Image Import CSV",
                        data=st.session_state.get("last_image_import_csv").encode("utf-8"),
                        file_name="image-import-plan.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="image_import_export_download",
                    )

    with export:
        st.subheader("Terraform Package")
        col1, col2 = st.columns(2)
        with col1:
            vpc_name = st.text_input("VPC Name", "migration-vpc")
            address_prefix_strategy = st.selectbox(
                "Address Prefix Strategy",
                ["manual", "auto"],
                index=0
            )
            deployment_target = st.selectbox(
                "Deployment Target",
                ["Plain CLI", "IBM Schematics"],
                index=0
            )
        with col2:
            st.markdown("**Custom CIDRs per Subnet**")
            custom_cidrs = {}
            for idx, net in enumerate(unique_nets):
                net_name = net.get('name', 'unknown-net')
                default_cidr = net.get('cidr', '10.0.0.0/24')
                sanitized_name = normalize_network_name(net_name)
                net_key = f"{sanitized_name}_{idx}"
                net['cidr_key'] = net_key
                custom_cidrs[net_key] = st.text_input(
                    f"{net_name} CIDR",
                    default_cidr,
                    key=f"cidr_{net_key}"
                )

        in_scope = len(edited_df[~edited_df['Exclude?']])
        blockers = sum(
            len(edited_df[(~edited_df['Exclude?']) & (edited_df[column] == "Blocked")])
            for column in [
                "Image Readiness", "Migration Readiness", "Memory Readiness"
            ]
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("VMs In Package", in_scope)
        c2.metric("Blocker Signals", blockers)
        c3.metric("Networks", len(unique_nets))

        st.download_button(
            label="Download Business Case (CSV)",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name=f"{project_name}_proposal.csv",
            mime="text/csv",
            use_container_width=True
        )

        preview_vms = build_final_vms(edited_df)
        preview_findings = run_package_preflight(
            preview_vms,
            unique_nets,
            target_region,
            custom_cidrs=custom_cidrs,
            enable_security_groups=generate_security_groups,
            catalog_profiles=catalog_profiles,
        )
        render_preflight_guidance(preview_findings, edited_df)
        if st.button("Re-run package preflight", use_container_width=True):
            st.session_state["preflight_needs_rerun"] = False
            st.rerun()

        if st.button("Build Terraform Project", use_container_width=True):
            with st.status("Packaging Project...") as status:
                try:
                    final_vms = build_final_vms(edited_df)

                    preflight_findings = run_package_preflight(
                        final_vms,
                        unique_nets,
                        target_region,
                        custom_cidrs=custom_cidrs,
                        enable_security_groups=generate_security_groups,
                        catalog_profiles=catalog_profiles,
                    )
                    if preflight_findings:
                        render_preflight_guidance(preflight_findings, edited_df)
                    if has_blockers(preflight_findings):
                        status.update(
                            label="Preflight blocked package build",
                            state="error",
                        )
                        st.session_state['build_done'] = False
                        st.error(
                            "Resolve package preflight blockers or exclude the "
                            "affected VMs before building the Terraform bundle."
                        )
                        st.stop()

                    terraform_files = render_terraform_templates(
                        final_vms,
                        unique_nets,
                        target_region,
                        target_zone,
                        generate_security_groups,
                        vpc_name,
                        custom_cidrs,
                        address_prefix_strategy,
                        deployment_target,
                        project_name
                    )
                    (
                        vsi, root_main, stor, net, root_vars, root_out,
                        net_vars, net_out, vsi_vars, vsi_out, stor_vars,
                        stor_out
                    ) = terraform_files

                    migration_context = {
                        'project_name': project_name,
                        'target_region': target_region,
                        'target_zone': target_zone,
                        'vpc_name': vpc_name,
                        'address_prefix_strategy': address_prefix_strategy,
                        'deployment_target': deployment_target,
                        'generate_security_groups': generate_security_groups,
                        'pricing_mode': pricing_metadata.get('mode'),
                        'pricing_source': pricing_metadata.get('source'),
                        'pricing_confidence': pricing_metadata.get('confidence'),
                        'pricing_status': pricing_metadata.get('pricing_status'),
                        'pricing_last_updated': pricing_metadata.get(
                            'last_updated'
                        ),
                        'assessment_quality': assessment_quality,
                    }

                    zip_b = io.BytesIO()
                    with zipfile.ZipFile(zip_b, "a") as zf:
                        zf.writestr("main.tf", root_main)
                        zf.writestr("variables.tf", root_vars)
                        zf.writestr("outputs.tf", root_out)
                        zf.writestr(
                            "terraform.tfvars",
                            generate_tfvars(
                                target_region, target_zone, project_name
                            )
                        )
                        zf.writestr("modules/networking/main.tf", net)
                        zf.writestr("modules/networking/variables.tf", net_vars)
                        zf.writestr("modules/networking/outputs.tf", net_out)
                        zf.writestr("modules/vsi/main.tf", vsi)
                        zf.writestr("modules/vsi/variables.tf", vsi_vars)
                        zf.writestr("modules/vsi/outputs.tf", vsi_out)
                        zf.writestr("modules/storage/main.tf", stor)
                        zf.writestr("modules/storage/variables.tf", stor_vars)
                        zf.writestr("modules/storage/outputs.tf", stor_out)
                        zf.writestr(
                            "migration-manifest.json",
                            generate_migration_manifest(final_vms, migration_context)
                        )
                        zf.writestr(
                            "assessment-quality.json",
                            generate_assessment_quality_json(assessment_quality)
                        )
                        zf.writestr(
                            "assessment-quality.csv",
                            generate_assessment_quality_csv(assessment_quality)
                        )
                        zf.writestr(
                            "preflight-report.json",
                            generate_preflight_report_json(preflight_findings)
                        )
                        zf.writestr(
                            "preflight-report.csv",
                            generate_preflight_report_csv(preflight_findings)
                        )
                        zf.writestr(
                            "pricing-diagnostics.json",
                            generate_pricing_diagnostics_json(
                                pricing_catalog, final_vms
                            )
                        )
                        zf.writestr(
                            "pricing-diagnostics.csv",
                            generate_pricing_diagnostics_csv(
                                pricing_catalog, final_vms
                            )
                        )
                        zf.writestr(
                            "decision-audit.csv",
                            decision_audit_export(final_vms, pricing_catalog)
                        )
                        zf.writestr(
                            "remediation-backlog.csv",
                            remediation_tracker_export(
                                final_vms,
                                st.session_state.get("remediation_tracker", {})
                            )
                        )
                        zf.writestr(
                            "image-import-plan.csv",
                            image_import_export(
                                final_vms,
                                st.session_state.get("image_import_status", {})
                            )
                        )
                        zf.writestr(
                            "vm-mapping.csv",
                            generate_vm_mapping_csv(final_vms)
                        )
                        zf.writestr(
                            "disk-mapping.csv",
                            generate_disk_mapping_csv(final_vms)
                        )
                        zf.writestr(
                            "partition-mapping.csv",
                            generate_partition_mapping_csv(final_vms)
                        )
                        zf.writestr(
                            "nic-mapping.csv",
                            generate_nic_mapping_csv(
                                final_vms, generate_security_groups
                            )
                        )
                        zf.writestr(
                            "memory-readiness.csv",
                            generate_memory_readiness_csv(final_vms)
                        )
                        zf.writestr(
                            "readiness-findings.csv",
                            generate_readiness_findings_csv(final_vms)
                        )
                        zf.writestr(
                            "image-import-variables.tfvars.example",
                            generate_image_import_tfvars(final_vms)
                        )
                        zf.writestr(
                            "migration-runbook.md",
                            generate_migration_runbook(migration_context)
                        )

                    st.session_state['zip_data'] = zip_b.getvalue()
                    st.session_state['build_done'] = True
                    status.update(label="Complete!", state="complete")
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.get('build_done'):
            st.write("---")
            st.write("### Project Ready")
            st.download_button(
                label="Download Terraform Bundle",
                data=st.session_state['zip_data'],
                file_name=f"{project_name}.zip",
                mime="application/zip",
                use_container_width=True
            )
