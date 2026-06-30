import csv
import io

from models.network_planning import (
    NetworkPlanningState,
    PlanningMetadata,
    StorageProfilePlan,
    VmNetworkAssignment,
    VpcPlan,
    WavePlan,
)
from prototype.api.carbon_handoff import (
    carbon_decision_audit_csv,
    carbon_decision_audit_records,
    carbon_image_import_status,
    carbon_remediation_tracker,
    carbon_state_native_handoff_files,
    normalize_pricing_catalog_for_decision_audit,
)


def _rows(csv_text):
    return list(csv.DictReader(io.StringIO(csv_text)))


def test_carbon_decision_audit_records_merge_network_plan_and_ui_rows():
    plan = NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        storage_profiles=[
            StorageProfilePlan(id="storage-db", name="database-storage", tier="10iops-tier"),
        ],
        waves=[WavePlan(id="wave-2", name="Wave 2", owner="DB owner")],
        vm_assignments=[
            VmNetworkAssignment(
                vm_key="vm-1",
                vm_name="db-01",
                primary_subnet_id="subnet-db",
                primary_security_group_id="sg-db",
                storage_profile_id="storage-db",
                wave_id="wave-2",
                excluded=True,
                exclusion_reason="Retired before migration",
                ibm_profile="bx2-4x16",
                override_profile="mx2-16x128",
                override_profile_reason="Database cache needs extra memory",
            )
        ],
        metadata=PlanningMetadata(project_name="Migration"),
    )
    planning_state = {
        "carbon_assignment_rows": [
            {
                "id": "vm-1",
                "name": "db-01",
                "storageTier": "3iops-tier",
                "overrideStorageTier": "10iops-tier",
                "overrideStorageTierReason": "Production write latency target",
                "owner": "DB owner",
                "application": "Database",
                "network": "db-net",
            }
        ]
    }

    record = carbon_decision_audit_records(plan, planning_state)[0]
    assert record | {
        "VM Key": "vm-1",
        "VM Name": "db-01",
        "Owner": "DB owner",
        "Application": "Database",
        "Wave": "Wave 2",
        "IBM Profile": "bx2-4x16",
        "Override Profile": "mx2-16x128",
        "Override Profile Reason": "Database cache needs extra memory",
        "Storage Tier": "3iops-tier",
        "Override Storage Tier": "10iops-tier",
        "Override Storage Tier Reason": "Production write latency target",
        "Network": "db-net",
        "Exclude?": True,
        "Exclusion Reason": "Retired before migration",
        "Total Storage GB": "",
    } == record


def test_carbon_decision_audit_csv_includes_pricing_impact_columns():
    plan = NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        vm_assignments=[
            VmNetworkAssignment(
                vm_key="vm-1",
                vm_name="app-01",
                primary_subnet_id="subnet-app",
                primary_security_group_id="sg-app",
                ibm_profile="bx2-2x8",
                override_profile="bx2-4x16",
                override_profile_reason="More headroom",
                storage_tier="3iops-tier",
            )
        ],
    )
    pricing_catalog = normalize_pricing_catalog_for_decision_audit({
        "profiles": [
            {"name": "bx2-2x8", "hourly": 0.114},
            {"name": "bx2-4x16", "hourly": 0.228},
        ],
        "storage_tier_rates": {"3iops-tier": 0.10},
    })

    rows = _rows(carbon_decision_audit_csv(plan, {}, pricing_catalog))

    assert rows[0]["Original Profile"] == "bx2-2x8"
    assert rows[0]["Chosen Profile"] == "bx2-4x16"
    assert rows[0]["Profile Override Reason"] == "More headroom"
    assert rows[0]["vCPU Cost Delta"] == "82.08"
    assert rows[0]["Total Pricing Impact"] == "82.08"


def test_carbon_state_native_handoff_files_use_saved_tracker_and_image_state():
    plan = NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        vm_assignments=[
            VmNetworkAssignment(
                vm_key="vm-1",
                vm_name="app-01",
                primary_subnet_id="subnet-app",
                primary_security_group_id="sg-app",
                ibm_profile="bx2-2x8",
            )
        ],
        metadata=PlanningMetadata(
            project_name="Migration",
            target_region="us-south",
            target_zone="us-south-1",
        ),
    )
    planning_state = {
        "carbon_assignment_rows": [
            {
                "id": "vm-1",
                "name": "app-01",
                "image": "Review",
                "imageReasons": "rhel-8-template",
                "migration": "Blocked",
                "migrationReasons": "Resolve source tools finding",
                "memory": "Ready",
                "networkReadiness": "Ready",
                "profile": "bx2-2x8",
                "storageTier": "3iops-tier",
                "owner": "App owner",
                "application": "Orders",
                "wave": "Wave 1",
                "cutoverGroup": "CG-A",
            }
        ],
        "carbon_remediation_tracker": {
            "vm-1::migration": {
                "status": "In Progress",
                "owner": "App owner",
                "dueDate": "2026-08-01",
                "notes": "App team reviewing",
            }
        },
        "carbon_image_import_status": {
            "rhel-8-template": {
                "targetCatalogId": "r001-image",
                "importStatus": "Imported",
                "estimatedImportTime": "45m",
                "notes": "Ready for VSI",
            }
        },
    }

    files = carbon_state_native_handoff_files(plan, planning_state)

    assert sorted(files) == [
        "cutover-readiness.csv",
        "image-import-plan.csv",
        "planning-state.json",
        "remediation-backlog.csv",
    ]
    assert "Resolve source tools finding" in files["remediation-backlog.csv"]
    assert "rhel-8-template,1,App owner,r001-image,Imported,45m,Ready for VSI" in files["image-import-plan.csv"]
    assert "Unresolved Remediation" in files["cutover-readiness.csv"]
    assert '"project_name": "Migration"' in files["planning-state.json"]
    assert carbon_remediation_tracker(planning_state, carbon_decision_audit_records(plan, planning_state))["vm-1::migration"]["due_date"] == "2026-08-01"
    assert carbon_image_import_status(planning_state)["rhel-8-template"]["target_catalog_id"] == "r001-image"
