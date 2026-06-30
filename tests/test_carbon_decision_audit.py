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

    assert carbon_decision_audit_records(plan, planning_state)[0] == {
        "VM Key": "vm-1",
        "VM Name": "db-01",
        "owner": "DB owner",
        "application": "Database",
        "wave": "Wave 2",
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
    }


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
