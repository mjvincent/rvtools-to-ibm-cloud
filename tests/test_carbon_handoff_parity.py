import io
import json
import zipfile

from models.network_planning import (
    NetworkPlanningState,
    PlanningMetadata,
    SecurityGroupPlan,
    SubnetPlan,
    VmNetworkAssignment,
    VpcPlan,
)
from prototype.api.carbon_handoff import (
    carbon_decision_audit_csv,
    carbon_full_handoff_files,
    carbon_state_native_handoff_files,
)
from prototype.api.handoff_parity import (
    CARBON_CURRENT_EXTRA_FILES,
    CARBON_PARITY_BLOCKERS,
    STREAMLIT_HANDOFF_FILES,
    STREAMLIT_PACKAGE_FILES,
    STREAMLIT_TERRAFORM_FILES,
)
from streamlit_app.package_builder import build_terraform_bundle


def _streamlit_package_files(
    final_vms,
    *,
    pricing_catalog,
    remediation_tracker,
    image_import_status,
):
    bundle = build_terraform_bundle(
        final_vms,
        [{"name": "app-net", "vlan": "101", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
        True,
        "migration-vpc",
        {"app-net": "10.0.1.0/24"},
        "manual",
        "Plain CLI",
        "Migration",
        "",
        pricing_catalog["metadata"],
        {},
        pricing_catalog,
        [],
        remediation_tracker,
        image_import_status,
    )
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        return {
            name: archive.read(name).decode("utf-8")
            for name in archive.namelist()
        }


def _carbon_package_files(
    record,
    *,
    pricing_catalog,
    remediation_tracker,
    image_import_status,
):
    plan = NetworkPlanningState(
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
                network=record["Network"],
                owner=record["Owner"],
                application=record["Application"],
                boot_disk_gb=record["Boot Disk GB"],
            )
        ],
        metadata=PlanningMetadata(
            project_name="Migration",
            target_region="us-south",
            target_zone="us-south-1",
            deployment_target="Plain CLI",
        ),
    )
    planning_state = {
        "carbon_assignment_rows": [_carbon_assignment_row(record)],
        "carbon_remediation_tracker": remediation_tracker,
        "carbon_image_import_status": image_import_status,
        "carbon_summary": {"assessment_quality": {}},
    }
    return {
        "decision-audit.csv": carbon_decision_audit_csv(
            plan,
            planning_state,
            pricing_catalog,
        ),
        **carbon_state_native_handoff_files(plan, planning_state),
        **carbon_full_handoff_files(plan, planning_state, pricing_catalog),
    }


def _carbon_assignment_row(record):
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
        "image": record["Image Readiness"],
        "imageReasons": record["Readiness Reasons"],
        "originalSpecs": record["Original Specs"],
        "migration": record["Migration Readiness"],
        "migrationReasons": record["Migration Readiness Reasons"],
        "networkReadiness": record["Network Readiness"],
        "networkReasons": record["Network Readiness Reasons"],
        "memory": record["Memory Readiness"],
        "memoryReasons": record["Memory Readiness Reasons"],
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
        "diskCount": str(record["Disk Count"]),
        "dataDiskCount": str(record["Data Disk Count"]),
        "totalStorageGb": str(record["Total Storage GB"]),
        "bootDiskGb": str(record["Boot Disk GB"]),
        "diskDetails": record["Disk Details"],
        "partitionDetails": record.get("Partition Details", []),
        "partitionCount": str(record.get("Partition Count", "")),
        "unmatchedPartitionCount": str(record.get("Unmatched Partition Count", "")),
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
        "owner": record["Owner"],
        "application": record["Application"],
        "wave": record["Wave"],
        "cutoverGroup": record["Cutover Group"],
        "priority": record["Priority"],
        "dependencyGroup": record["Dependency Group"],
    }


def _operational_planning_state(text):
    state = json.loads(text)
    state.pop("generated_at", None)
    return state


def test_streamlit_package_parity_inventory_covers_expected_handoff_files():
    assert STREAMLIT_HANDOFF_FILES == {
        "migration-manifest.json",
        "assessment-quality.json",
        "assessment-quality.csv",
        "preflight-report.json",
        "preflight-report.csv",
        "pricing-diagnostics.json",
        "pricing-diagnostics.csv",
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
        "planning-state.json",
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
        "image-import-variables.tfvars.example",
        "migration-runbook.md",
    }


def test_streamlit_package_parity_inventory_covers_terraform_files():
    assert {
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "modules/networking/main.tf",
        "modules/vsi/main.tf",
        "modules/storage/main.tf",
    }.issubset(STREAMLIT_TERRAFORM_FILES)


def test_carbon_parity_blockers_are_subset_of_streamlit_package():
    assert CARBON_PARITY_BLOCKERS.issubset(STREAMLIT_PACKAGE_FILES)


def test_carbon_current_extra_files_are_documented():
    assert CARBON_CURRENT_EXTRA_FILES == {"network-plan.json"}


def test_carbon_package_handoff_contents_match_streamlit_fixture(sample_vm_record):
    record = {
        **sample_vm_record,
        "Owner": "app-team",
        "Application": "orders",
        "Wave": "Wave 1",
        "Cutover Group": "CG-A",
        "Priority": "high",
        "Dependency Group": "payments",
        "Boot Disk GB": 80,
    }
    pricing_catalog = {
        "metadata": {
            "mode": "static",
            "source": "static",
            "confidence": "fallback-static",
            "pricing_status": "static_fallback",
            "region": "us-south",
            "country": "us",
            "currency": "USD",
            "last_updated": "2026-05-12T00:00:00+00:00",
        },
        "profiles": {
            "bx2-2x8": {"hourly": record["Profile Hourly"]},
        },
        "storage_tiers": {
            "5iops-tier": {"monthly_per_gb": 0.13},
        },
    }
    remediation_tracker = {
        "vm-001::migration": {
            "vm_key": "vm-001",
            "owner": "app-team",
            "status": "Open",
            "due_date": "2026-07-15",
            "notes": "Update VMware Tools",
            "blocker_type": "Migration",
            "blocker_description": "VMware Tools status: toolsOld",
        }
    }
    image_import_status = {
        "rhel-9-template": {
            "target_catalog_id": "r001-12345678",
            "import_status": "Imported",
            "estimated_import_time": "45m",
            "notes": "Imported from COS",
        }
    }

    streamlit_files = _streamlit_package_files(
        [record],
        pricing_catalog=pricing_catalog,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    carbon_files = _carbon_package_files(
        record,
        pricing_catalog=pricing_catalog,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )

    exact_handoff_files = {
        "decision-audit.csv",
        "assessment-quality.json",
        "assessment-quality.csv",
        "pricing-diagnostics.json",
        "pricing-diagnostics.csv",
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
        "image-import-variables.tfvars.example",
        "migration-runbook.md",
    }
    for file_name in exact_handoff_files:
        assert carbon_files[file_name] == streamlit_files[file_name], file_name

    assert _operational_planning_state(
        carbon_files["planning-state.json"]
    ) == _operational_planning_state(streamlit_files["planning-state.json"])

    carbon_manifest = json.loads(carbon_files["migration-manifest.json"])
    streamlit_manifest = json.loads(streamlit_files["migration-manifest.json"])
    assert carbon_manifest["handoff_files"] == streamlit_manifest["handoff_files"]
    assert carbon_manifest["project"] == streamlit_manifest["project"]
    assert (
        carbon_manifest["decision_audit_summary"]
        == streamlit_manifest["decision_audit_summary"]
    )
    assert (
        carbon_manifest["remediation_tracker_summary"]
        == streamlit_manifest["remediation_tracker_summary"]
    )
    assert (
        carbon_manifest["image_import_summary"]
        == streamlit_manifest["image_import_summary"]
    )
    assert carbon_manifest["virtual_machines"] == streamlit_manifest["virtual_machines"]
