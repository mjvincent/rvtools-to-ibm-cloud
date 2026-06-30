import csv
import io

from models.network_planning import (
    NetworkPlanningState,
    PlanningMetadata,
    SecurityGroupPlan,
    StorageProfilePlan,
    SubnetPlan,
    VmNetworkAssignment,
    VpcPlan,
    WavePlan,
)
from prototype.api.carbon_handoff import (
    carbon_decision_audit_csv,
    carbon_decision_audit_records,
    carbon_image_import_status,
    carbon_remediation_tracker,
    carbon_full_handoff_files,
    carbon_state_native_handoff_files,
    normalize_pricing_catalog_for_decision_audit,
)
from handoff import (
    generate_disk_mapping_csv,
    generate_memory_readiness_csv,
    generate_nic_mapping_csv,
    generate_readiness_findings_csv,
    generate_vm_mapping_csv,
)


def _rows(csv_text):
    return list(csv.DictReader(io.StringIO(csv_text)))


def _camel_source_row(record):
    return {
        "id": record["VM Key"],
        "name": record["VM Name"],
        "power": record["Power State"],
        "guestOs": record["Guest OS"],
        "sourceIp": record["Source IP"],
        "network": record["Network"],
        "profile": record["IBM Profile"],
        "storageTier": record["Storage Tier"],
        "subnet": record["Subnet"],
        "securityGroup": record["Security Group"],
        "diskCount": str(record["Disk Count"]),
        "dataDiskCount": str(record["Data Disk Count"]),
        "totalStorageGb": str(record["Total Storage GB"]),
        "image": record["Image Readiness"],
        "imageReasons": record["Readiness Reasons"],
        "migration": record["Migration Readiness"],
        "migrationReasons": record["Migration Readiness Reasons"],
        "networkReadiness": record["Network Readiness"],
        "networkReasons": record["Network Readiness Reasons"],
        "memory": record["Memory Readiness"],
        "memoryReasons": record["Memory Readiness Reasons"],
        "originalSpecs": record["Original Specs"],
        "configuredMemoryMib": str(record["Configured Memory MiB"]),
        "activeMemoryMib": str(record["Active Memory MiB"]),
        "consumedMemoryMib": str(record["Consumed Memory MiB"]),
        "balloonedMemoryMib": str(record["Ballooned Memory MiB"]),
        "swappedMemoryMib": str(record["Swapped Memory MiB"]),
        "memoryReservationMib": str(record["Memory Reservation MiB"]),
        "memoryLimitMib": str(record["Memory Limit MiB"]),
        "memoryHotAdd": record["Memory Hot Add"],
        "sizingMemoryMib": str(record["Sizing Memory MiB"]),
        "memorySizingBasis": record["Memory Sizing Basis"],
        "diskDetails": record["Disk Details"],
        "networkDetails": record["Network Details"],
        "readinessFindings": record["Readiness Findings"],
        "networkReadinessFindings": record["Network Readiness Findings"],
        "computeMonthly": str(record["Compute (Mo)"]),
        "storageMonthly": str(record["Storage (Mo)"]),
        "monthlyCost": str(record["Monthly Cost"]),
        "baselineCostMonthly": str(record["Baseline Cost (Mo)"]),
        "savingsMonthly": str(record["Savings (Mo)"]),
        "pricingSource": record["Pricing Source"],
        "pricingConfidence": record["Pricing Confidence"],
        "pricingLastUpdated": record["Pricing Last Updated"],
        "pricingStatus": record["Pricing Status"],
        "profileHourly": str(record["Profile Hourly"]),
    }


def _plan_for_record(record):
    return NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        subnets=[
            SubnetPlan(
                id="subnet-app",
                name=record["Subnet"],
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr="10.0.1.0/24",
                source_network=record["Network"],
            )
        ],
        security_groups=[
            SecurityGroupPlan(
                id="sg-app",
                name=record["Security Group"],
                vpc_id="vpc-1",
            )
        ],
        vm_assignments=[
            VmNetworkAssignment(
                vm_key=record["VM Key"],
                vm_name=record["VM Name"],
                primary_subnet_id="subnet-app",
                primary_security_group_id="sg-app",
                ibm_profile=record["IBM Profile"],
                storage_tier=record["Storage Tier"],
                guest_os=record["Guest OS"],
            )
        ],
        metadata=PlanningMetadata(
            project_name="Migration",
            target_region="us-south",
            target_zone="us-south-1",
        ),
    )


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


def test_carbon_full_handoff_files_cover_remaining_streamlit_artifacts():
    plan = NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        vm_assignments=[
            VmNetworkAssignment(
                vm_key="vm-1",
                vm_name="app-01",
                primary_subnet_id="subnet-app",
                primary_security_group_id="sg-app",
                ibm_profile="bx2-2x8",
                guest_os="Linux",
            )
        ],
        metadata=PlanningMetadata(
            project_name="Migration",
            target_region="us-south",
            target_zone="us-south-1",
        ),
    )
    planning_state = {
        "carbon_summary": {
            "assessment_quality": {
                "summary": {"confidence": "high"},
                "worksheets": {},
            }
        },
        "carbon_assignment_rows": [
            {
                "id": "vm-1",
                "name": "app-01",
                "image": "Ready",
                "imageReasons": "rhel-8-template",
                "migration": "Ready",
                "memory": "Ready",
                "networkReadiness": "Ready",
                "profile": "bx2-2x8",
                "storageTier": "3iops-tier",
                "owner": "App owner",
                "application": "Orders",
                "wave": "Wave 1",
                "cutoverGroup": "CG-A",
                "power": "poweredOn",
            }
        ],
    }

    files = carbon_full_handoff_files(plan, planning_state, {
        "profiles": [{"name": "bx2-2x8", "hourly": 0.114}],
        "storage_tier_rates": {"3iops-tier": 0.10},
        "metadata": {"mode": "static", "region": "us-south"},
    })

    assert sorted(files) == [
        "assessment-quality.csv",
        "assessment-quality.json",
        "disk-mapping.csv",
        "image-import-variables.tfvars.example",
        "memory-readiness.csv",
        "migration-manifest.json",
        "migration-runbook.md",
        "nic-mapping.csv",
        "partition-mapping.csv",
        "preflight-report.csv",
        "preflight-report.json",
        "pricing-diagnostics.csv",
        "pricing-diagnostics.json",
        "readiness-findings.csv",
        "vm-mapping.csv",
    ]
    assert '"package_type": "rvtools-to-ibm-cloud-migration-handoff"' in files["migration-manifest.json"]
    assert "app-01" in files["vm-mapping.csv"]
    assert "replace-with-imported-image-id" in files["image-import-variables.tfvars.example"]
    assert "Migration Handoff Runbook" in files["migration-runbook.md"]
    assert '"summary"' in files["preflight-report.json"]


def test_carbon_handoff_records_preserve_workbook_detail_fidelity(sample_vm_record):
    plan = _plan_for_record(sample_vm_record)
    planning_state = {
        "carbon_assignment_rows": [_camel_source_row(sample_vm_record)]
    }
    carbon_record = carbon_decision_audit_records(plan, planning_state)[0]

    assert carbon_record["Disk Details"] == sample_vm_record["Disk Details"]
    assert carbon_record["Network Details"] == sample_vm_record["Network Details"]
    assert carbon_record["Readiness Findings"] == sample_vm_record["Readiness Findings"]
    assert carbon_record["Configured Memory MiB"] == sample_vm_record["Configured Memory MiB"]

    streamlit_vm_mapping = _rows(generate_vm_mapping_csv([sample_vm_record]))[0]
    carbon_vm_mapping = _rows(generate_vm_mapping_csv([carbon_record]))[0]
    assert carbon_vm_mapping["Source IP"] == streamlit_vm_mapping["Source IP"]
    assert carbon_vm_mapping["Disk Count"] == streamlit_vm_mapping["Disk Count"]
    assert carbon_vm_mapping["Configured Memory MiB"] == streamlit_vm_mapping["Configured Memory MiB"]

    streamlit_disk_rows = _rows(generate_disk_mapping_csv([sample_vm_record]))
    carbon_disk_rows = _rows(generate_disk_mapping_csv([carbon_record]))
    assert carbon_disk_rows[1]["Terraform Volume"] == streamlit_disk_rows[1]["Terraform Volume"]
    assert carbon_disk_rows[1]["Target Action"] == "create-and-attach-volume"

    streamlit_nic_rows = _rows(generate_nic_mapping_csv([sample_vm_record]))
    carbon_nic_rows = _rows(generate_nic_mapping_csv([carbon_record]))
    assert carbon_nic_rows[0]["VLAN / Segment"] == streamlit_nic_rows[0]["VLAN / Segment"]
    assert carbon_nic_rows[1]["Source Network"] == "db-net"

    assert _rows(generate_memory_readiness_csv([carbon_record]))[0]["Sizing Memory MiB"] == "8192"
    assert _rows(generate_readiness_findings_csv([carbon_record]))[0]["Evidence"] == "toolsOld"
