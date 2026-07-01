import csv
import io
import json
from pathlib import Path
import zipfile

from fastapi.testclient import TestClient

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
from prototype.api.app import app
from prototype.api.handoff_parity import (
    CARBON_CURRENT_EXTRA_FILES,
    CARBON_PARITY_BLOCKERS,
    STREAMLIT_HANDOFF_FILES,
    STREAMLIT_PACKAGE_FILES,
    STREAMLIT_TERRAFORM_FILES,
)
from streamlit_app.package_builder import build_terraform_bundle

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"


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


def _carbon_package_files_from_records(
    records,
    *,
    assessment_quality=None,
    remediation_tracker=None,
    image_import_status=None,
):
    subnets = []
    security_groups = []
    assignments = []
    for index, record in enumerate(records, start=1):
        subnet_id = f"subnet-{index}"
        security_group_id = f"sg-{index}"
        subnets.append(
            SubnetPlan(
                id=subnet_id,
                name=record["Subnet"],
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr=f"10.0.{index}.0/24",
                source_network=record["Network"],
            )
        )
        security_groups.append(
            SecurityGroupPlan(
                id=security_group_id,
                name=record["Security Group"],
                vpc_id="vpc-1",
            )
        )
        assignments.append(
            VmNetworkAssignment(
                vm_key=record["VM Key"],
                vm_name=record["VM Name"],
                primary_subnet_id=subnet_id,
                primary_security_group_id=security_group_id,
                ibm_profile=record["IBM Profile"],
                storage_tier=record["Storage Tier"],
                guest_os=record["Guest OS"],
                network=record["Network"],
                owner=record["Owner"],
                application=record["Application"],
                boot_disk_gb=record["Boot Disk GB"],
            )
        )

    plan = NetworkPlanningState(
        vpcs=[VpcPlan(id="vpc-1", name="migration-vpc", region="us-south")],
        subnets=subnets,
        security_groups=security_groups,
        vm_assignments=assignments,
        metadata=PlanningMetadata(
            project_name="Migration",
            target_region="us-south",
            target_zone="us-south-1",
            deployment_target="Plain CLI",
        ),
    )
    planning_state = {
        "carbon_assignment_rows": [_carbon_assignment_row(record) for record in records],
        "carbon_remediation_tracker": remediation_tracker or {},
        "carbon_image_import_status": image_import_status or {},
        "carbon_summary": {"assessment_quality": assessment_quality or {}},
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
            record["IBM Profile"]: {"hourly": record["Profile Hourly"]}
            for record in records
            if record.get("IBM Profile")
        },
        "storage_tiers": {
            record["Storage Tier"]: {"monthly_per_gb": 0.10}
            for record in records
            if record.get("Storage Tier")
        },
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


def _csv_rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def _sample_workbook_summary():
    client = TestClient(app)
    sample_path = SAMPLES_DIR / "rvtools-small-complete.xlsx"
    with sample_path.open("rb") as workbook:
        response = client.post(
            "/api/workbooks/summary",
            files={
                "workbook": (
                    sample_path.name,
                    workbook,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    assert response.status_code == 200
    return response.json()


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


def test_carbon_sample_workbook_populates_phase4_handoff_artifacts():
    summary = _sample_workbook_summary()
    records = summary["assignment_rows"]

    assert {record["VM Name"] for record in records} == {
        "sample-db-01",
        "sample-web-01",
    }

    carbon_files = _carbon_package_files_from_records(
        records,
        assessment_quality=summary["assessment_quality"],
        remediation_tracker={
            "sample-db-01::migration": {
                "vm_key": "sample-db-01",
                "owner": "db-team",
                "status": "Open",
                "due_date": "2026-07-15",
                "notes": "Validate VMware Tools before cutover.",
                "blocker_type": "Migration",
                "blocker_description": "VMware Tools status requires review",
            }
        },
        image_import_status={
            "4v / 16384M": {
                "target_catalog_id": "r001-sample-db-image",
                "import_status": "Pending",
                "estimated_import_time": "60m",
                "notes": "Track Windows image import before migration.",
            }
        },
    )

    for file_name in {
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
        "planning-state.json",
    }:
        assert file_name in carbon_files
        assert carbon_files[file_name].strip(), file_name

    audit_rows = _csv_rows(carbon_files["decision-audit.csv"])
    audit_by_vm = {
        row["VM Name"]: row
        for row in audit_rows
        if row["VM Name"] and row["VM Name"] != "TOTAL"
    }
    assert set(audit_by_vm) == {"sample-db-01", "sample-web-01"}
    assert audit_rows[0].keys() >= {
        "VM Key",
        "VM Name",
        "Original Profile",
        "Chosen Profile",
        "Original Storage Tier",
        "Chosen Storage Tier",
        "vCPU Cost Delta",
        "Storage Cost Delta",
        "Total Pricing Impact",
    }
    assert audit_by_vm["sample-db-01"] | {
        "VM Key": "sample-db-01",
        "Original Profile": "mx2-2x16",
        "Chosen Profile": "mx2-2x16",
        "Original Storage Tier": "10iops-tier",
        "Chosen Storage Tier": "10iops-tier",
        "Include/Exclude": "Include",
        "Total Pricing Impact": "0.0",
    } == audit_by_vm["sample-db-01"]

    remediation_rows = _csv_rows(carbon_files["remediation-backlog.csv"])
    remediation_row = next(row for row in remediation_rows if row["VM Key"] == "sample-db-01")
    assert remediation_row == {
        "VM Key": "sample-db-01",
        "VM Name": "unknown-vm",
        "Owner": "db-team",
        "Blocker Type": "Migration",
        "Blocker Description": "VMware Tools status requires review",
        "Status": "Open",
        "Due Date": "2026-07-15",
        "Notes": "Validate VMware Tools before cutover.",
    }

    image_rows = _csv_rows(carbon_files["image-import-plan.csv"])
    image_by_source = {row["Source Image"]: row for row in image_rows}
    assert image_by_source["2v / 8192M"]["Count of VMs"] == "1"
    assert image_by_source["4v / 16384M"] | {
        "Count of VMs": "1",
        "Target Catalog ID": "r001-sample-db-image",
        "Import Status": "Pending",
        "Estimated Import Time": "60m",
        "Notes": "Track Windows image import before migration.",
    } == image_by_source["4v / 16384M"]
    assert image_by_source["TOTAL"]["Count of VMs"] == "2"

    cutover_rows = _csv_rows(carbon_files["cutover-readiness.csv"])
    db_cutover_rows = [row for row in cutover_rows if row["VM Name"] == "sample-db-01"]
    assert db_cutover_rows
    assert any(row["Blocker Category"] == "Missing Planning" for row in db_cutover_rows)
    assert any(row["Blocker Category"] == "Readiness Review" for row in db_cutover_rows)
    assert any(
        row["Blocker Category"] == "Image Import Pending"
        and row["Blocker Reason"] == "4v / 16384M import status is Pending"
        for row in db_cutover_rows
    )
    assert any(
        row["Blocker Category"] == "Unresolved Remediation"
        and row["Blocker Reason"] == "Migration: VMware Tools status requires review (Open)"
        for row in db_cutover_rows
    )

    planning_state = json.loads(carbon_files["planning-state.json"])
    assert planning_state["schema_version"] == "1.0"
    assert planning_state["metadata"] == {
        "project_name": "Migration",
        "target_region": "us-south",
        "target_zone": "us-south-1",
    }
    assert len(planning_state["vm_decisions"]) == 2
    assert {row["VM Name"] for row in planning_state["vm_decisions"]} == {
        "sample-db-01",
        "sample-web-01",
    }
    assert planning_state["remediation_tracker"]["sample-db-01::migration"] == {
        "blocker_description": "VMware Tools status requires review",
        "blocker_type": "Migration",
        "due_date": "2026-07-15",
        "notes": "Validate VMware Tools before cutover.",
        "owner": "db-team",
        "status": "Open",
        "vm_key": "sample-db-01",
    }
    assert planning_state["image_import_status"]["4v / 16384M"] == {
        "estimated_import_time": "60m",
        "import_status": "Pending",
        "notes": "Track Windows image import before migration.",
        "target_catalog_id": "r001-sample-db-image",
    }
