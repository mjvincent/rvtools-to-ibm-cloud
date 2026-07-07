import csv
import io
import json
from pathlib import Path
import zipfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from models.network_planning import (
    NetworkPlanningState,
    PlanningMetadata,
    SecurityGroupPlan,
    SubnetPlan,
    VmNetworkAssignment,
    VpcPlan,
    to_dict,
)
from prototype.api.carbon_handoff import (
    carbon_decision_audit_csv,
    carbon_full_handoff_files,
    carbon_state_native_handoff_files,
)
from prototype.api.app import app
from prototype.api.handoff_parity import (
    CARBON_MODULAR_TERRAFORM_FILES,
    CARBON_CURRENT_EXTRA_FILES,
    CARBON_PARITY_BLOCKERS,
    STREAMLIT_HANDOFF_FILES,
    STREAMLIT_PACKAGE_FILES,
    STREAMLIT_TERRAFORM_FILES,
)
from streamlit_app.package_builder import build_terraform_bundle

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"
CARBON_UI_PACKAGE_INVENTORY = (
    Path(__file__).resolve().parents[1]
    / "prototype"
    / "carbon-ui"
    / "utils"
    / "package-inventory.json"
)

SAMPLE_REMEDIATION_TRACKER = {
    "sample-db-01::migration": {
        "vm_key": "sample-db-01",
        "owner": "db-team",
        "status": "Open",
        "due_date": "2026-07-15",
        "notes": "Validate VMware Tools before cutover.",
        "blocker_type": "Migration",
        "blocker_description": "VMware Tools status requires review",
    }
}

SAMPLE_IMAGE_IMPORT_STATUS = {
    "4v / 16384M": {
        "target_catalog_id": "r001-sample-db-image",
        "import_status": "Pending",
        "estimated_import_time": "60m",
        "notes": "Track Windows image import before migration.",
    }
}


def _streamlit_package_files(
    final_vms,
    *,
    pricing_catalog,
    remediation_tracker,
    image_import_status,
    assessment_quality=None,
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
        assessment_quality or {},
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
    plan, planning_state, pricing_catalog = _carbon_plan_state_and_pricing_from_records(
        records,
        assessment_quality=assessment_quality,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    return {
        "decision-audit.csv": carbon_decision_audit_csv(
            plan,
            planning_state,
            pricing_catalog,
        ),
        **carbon_state_native_handoff_files(plan, planning_state),
        **carbon_full_handoff_files(plan, planning_state, pricing_catalog),
    }


def _carbon_plan_state_and_pricing_from_records(
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
                excluded=record.get("Exclude?", False),
                exclusion_reason=record.get("Exclusion Reason") or None,
                override_profile=record.get("Override Profile") or None,
                override_profile_reason=record.get("Override Profile Reason") or None,
                override_storage_tier=record.get("Override Storage Tier") or None,
                override_storage_tier_reason=(
                    record.get("Override Storage Tier Reason") or None
                ),
                custom_image_id=record.get("Custom Image ID") or None,
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
        "profiles": {},
        "storage_tiers": {},
    }
    for record in records:
        if record.get("IBM Profile"):
            pricing_catalog["profiles"][record["IBM Profile"]] = {
                "hourly": record["Profile Hourly"],
            }
        if record.get("Override Profile"):
            pricing_catalog["profiles"][record["Override Profile"]] = {
                "hourly": record.get("Override Profile Hourly", record["Profile Hourly"]),
            }
        if record.get("Storage Tier"):
            pricing_catalog["storage_tiers"][record["Storage Tier"]] = {
                "monthly_per_gb": record.get("Storage Tier Monthly Per GB", 0.10),
            }
        if record.get("Override Storage Tier"):
            pricing_catalog["storage_tiers"][record["Override Storage Tier"]] = {
                "monthly_per_gb": record.get(
                    "Override Storage Tier Monthly Per GB",
                    record.get("Storage Tier Monthly Per GB", 0.10),
                ),
            }
    return plan, planning_state, pricing_catalog


def _carbon_assignment_row(record):
    return {
        "id": record["VM Key"],
        "name": record["VM Name"],
        "power": record["Power State"],
        "guestOs": record["Guest OS"],
        "sourceIp": record["Source IP"],
        "network": record["Network"],
        "datacenter": record.get("Datacenter", ""),
        "cluster": record.get("Cluster", ""),
        "host": record.get("Host", ""),
        "firmware": record.get("Firmware", ""),
        "profile": record["IBM Profile"],
        "storageTier": record["Storage Tier"],
        "overrideProfile": record.get("Override Profile", ""),
        "overrideProfileReason": record.get("Override Profile Reason", ""),
        "overrideStorageTier": record.get("Override Storage Tier", ""),
        "overrideStorageTierReason": record.get("Override Storage Tier Reason", ""),
        "excluded": record.get("Exclude?", False),
        "exclusionReason": record.get("Exclusion Reason", ""),
        "customImageId": record.get("Custom Image ID", ""),
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


def _sample_carbon_project_fixture():
    summary = _sample_workbook_summary()
    records = summary["assignment_rows"]
    plan, planning_state, _pricing_catalog = _carbon_plan_state_and_pricing_from_records(
        records,
        assessment_quality=summary["assessment_quality"],
        remediation_tracker=SAMPLE_REMEDIATION_TRACKER,
        image_import_status=SAMPLE_IMAGE_IMPORT_STATUS,
    )
    project_id = "sample-carbon-parity"
    planning_state_json = {
        **planning_state,
        "carbon_network_plan": to_dict(plan),
    }
    project = {"id": project_id, "name": "Migration", "description": ""}
    project_state = {
        "target_region": "us-south",
        "target_zone": "us-south-1",
        "planning_state_json": planning_state_json,
    }
    return project_id, project, project_state


def _workshop_workbook_summary():
    client = TestClient(app)
    sample_path = SAMPLES_DIR / "SizingWorkshop-RVTools.xlsx"
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


def test_carbon_export_ui_inventory_matches_backend_zip_contract():
    inventory = json.loads(CARBON_UI_PACKAGE_INVENTORY.read_text())

    assert set(inventory["handoffPackageFiles"]) == STREAMLIT_HANDOFF_FILES
    assert set(inventory["terraformPackageFiles"]) == CARBON_MODULAR_TERRAFORM_FILES
    assert set(inventory["carbonPackageFiles"]) == CARBON_CURRENT_EXTRA_FILES


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


def test_carbon_edge_fixture_preserves_mapping_and_readiness_fidelity(sample_vm_record):
    record = {
        **sample_vm_record,
        "VM Key": "vm-edge-001",
        "VM Name": "edge-db-01",
        "Owner": "platform-team",
        "Application": "Inventory",
        "Wave": "Wave 2",
        "Cutover Group": "CG-DB",
        "Priority": "high",
        "Dependency Group": "inventory-core",
        "Boot Disk GB": 80,
        "Memory Readiness": "Review",
        "Memory Readiness Reasons": "Ballooned memory detected; memory hot-add enabled",
        "Ballooned Memory MiB": 512,
        "Swapped Memory MiB": 128,
        "Memory Reservation MiB": 2048,
        "Memory Limit MiB": 12288,
        "Memory Hot Add": "True",
        "Sizing Memory MiB": 12288,
        "Memory Sizing Basis": "active-plus-pressure-headroom",
        "Disk Count": 2,
        "Data Disk Count": 1,
        "Total Storage GB": 200,
        "Disk Details": [
            {
                "disk": "Hard disk 1",
                "capacity_gb": 80,
                "capacity_mib": 81920,
                "is_boot": True,
                "disk_key": "2000",
                "unit_number": 0,
                "partitions": [
                    {
                        "disk": "C:\\",
                        "disk_key": "2000",
                        "capacity_mib": 61440,
                        "consumed_mib": 40960,
                        "free_mib": 20480,
                        "free_pct": 33.33,
                        "matched": True,
                    }
                ],
            },
            {
                "disk": "Hard disk 2",
                "capacity_gb": 120,
                "capacity_mib": 122880,
                "is_boot": False,
                "disk_key": "2001",
                "unit_number": 1,
                "partitions": [
                    {
                        "disk": "D:\\",
                        "disk_key": "2001",
                        "capacity_mib": 102400,
                        "consumed_mib": 51200,
                        "free_mib": 51200,
                        "free_pct": 50.0,
                        "matched": True,
                    }
                ],
            },
        ],
        "Partition Details": [
            {
                "disk": "E:\\",
                "disk_key": "",
                "capacity_mib": 20480,
                "consumed_mib": 10240,
                "free_mib": 10240,
                "free_pct": 50.0,
                "matched": False,
            }
        ],
        "Partition Count": 3,
        "Unmatched Partition Count": 1,
        "Network Details": [
            {
                "label": "Network adapter 1",
                "adapter": "Vmxnet3",
                "network": "app-net",
                "switch": "vSwitch0",
                "connected": True,
                "starts_connected": True,
                "mac_address": "00:50:56:aa:00:01",
                "ipv4": "10.0.1.10",
                "ipv6": "",
                "switch_type": "standard",
                "port_group": "app-net",
                "vlan": "101",
                "port_status": "up",
                "backing_source_tab": "vPort",
                "match_confidence": "matched",
            },
            {
                "label": "Network adapter 2",
                "adapter": "Vmxnet3",
                "network": "db-net",
                "switch": "dvSwitch-db",
                "connected": True,
                "starts_connected": True,
                "mac_address": "00:50:56:aa:00:02",
                "ipv4": "10.0.2.10",
                "ipv6": "",
                "switch_type": "distributed",
                "port_group": "db-net",
                "vlan": "202",
                "port_key": "77",
                "port_status": "up",
                "backing_source_tab": "dvPort",
                "match_confidence": "matched",
            },
            {
                "label": "Network adapter 3",
                "adapter": "E1000",
                "network": "backup-net",
                "switch": "vSwitch1",
                "connected": False,
                "starts_connected": False,
                "mac_address": "00:50:56:aa:00:03",
                "ipv4": "",
                "ipv6": "",
                "switch_type": "standard",
                "port_group": "backup-net",
                "vlan": "303",
                "port_status": "down",
                "backing_source_tab": "vPort",
                "match_confidence": "matched",
            },
        ],
        "Readiness Findings": [
            {
                "finding_type": "Snapshot",
                "severity": "Blocked",
                "source_tab": "vSnapshot",
                "evidence": "Active snapshot found",
                "recommended_action": "Remove snapshots before migration",
            },
            {
                "finding_type": "VMware Tools status",
                "severity": "Review",
                "source_tab": "vTools",
                "evidence": "toolsOld",
                "recommended_action": "Update VMware Tools",
            },
        ],
        "Network Readiness Findings": [
            {
                "finding_type": "Disconnected NIC",
                "severity": "Review",
                "source_tab": "vNetwork",
                "evidence": "Network adapter 3 is disconnected",
                "recommended_action": "Confirm backup network requirement",
            }
        ],
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
            record["IBM Profile"]: {"hourly": record["Profile Hourly"]},
        },
        "storage_tiers": {
            record["Storage Tier"]: {"monthly_per_gb": 0.13},
        },
    }

    streamlit_files = _streamlit_package_files(
        [record],
        pricing_catalog=pricing_catalog,
        remediation_tracker={},
        image_import_status={},
    )
    carbon_files = _carbon_package_files(
        record,
        pricing_catalog=pricing_catalog,
        remediation_tracker={},
        image_import_status={},
    )

    rich_detail_files = {
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
    }
    for file_name in rich_detail_files:
        assert carbon_files[file_name] == streamlit_files[file_name], file_name

    def assert_row_fields(row, expected):
        assert {field: row[field] for field in expected} == expected

    disk_rows = _csv_rows(carbon_files["disk-mapping.csv"])
    assert {row["Disk"] for row in disk_rows} == {"Hard disk 1", "Hard disk 2"}
    assert_row_fields(
        next(row for row in disk_rows if row["Disk"] == "Hard disk 2"),
        {
            "Partition Labels": "D:\\",
            "Partition Count": "1",
            "Partition Capacity MiB": "102400.0",
        },
    )

    partition_rows = _csv_rows(carbon_files["partition-mapping.csv"])
    assert len(partition_rows) == 3
    assert_row_fields(
        next(row for row in partition_rows if row["Partition"] == "E:\\"),
        {
            "Matched To Disk": "False",
            "Capacity MiB": "20480",
        },
    )

    nic_rows = _csv_rows(carbon_files["nic-mapping.csv"])
    assert len(nic_rows) == 3
    assert_row_fields(
        next(row for row in nic_rows if row["NIC Label"] == "Network adapter 2"),
        {
            "Source Network": "db-net",
            "Switch Type": "distributed",
            "Port Key": "77",
            "Role": "secondary",
            "Planned": "True",
        },
    )
    assert_row_fields(
        next(row for row in nic_rows if row["NIC Label"] == "Network adapter 3"),
        {
            "Connected": "False",
            "Planned": "False",
            "Role": "disconnected",
        },
    )

    memory_rows = _csv_rows(carbon_files["memory-readiness.csv"])
    assert_row_fields(
        memory_rows[0],
        {
            "VM Name": "edge-db-01",
            "Memory Readiness": "Review",
            "Ballooned Memory MiB": "512",
            "Swapped Memory MiB": "128",
            "Sizing Memory MiB": "12288",
            "Memory Sizing Basis": "active-plus-pressure-headroom",
        },
    )

    finding_rows = _csv_rows(carbon_files["readiness-findings.csv"])
    assert any(
        row["VM Name"] == "edge-db-01"
        and row["Finding Type"] == "Snapshot"
        and row["Severity"] == "Blocked"
        for row in finding_rows
    )


def test_carbon_multi_vm_fixture_preserves_operational_handoff_parity(
    sample_vm_record,
):
    records = [
        {
            **sample_vm_record,
            "VM Key": "vm-app-001",
            "VM Name": "orders-app-01",
            "Owner": "app-team",
            "Application": "Orders",
            "Wave": "Wave 1",
            "Cutover Group": "CG-App",
            "Priority": "high",
            "Dependency Group": "orders-core",
            "Boot Disk GB": 80,
            "Network": "app-net",
            "Subnet": "module.networking.app_net_id",
            "Security Group": "module.networking.app_net_sg_id",
            "Image Readiness": "Ready",
            "Readiness Reasons": "Custom image available",
            "Migration Readiness": "Ready",
            "Migration Readiness Reasons": "No migration readiness blockers found",
            "Override Profile": "bx2-4x16",
            "Override Profile Reason": "CPU headroom for checkout burst",
            "Override Profile Hourly": 0.228,
            "Original Specs": "rhel-9-template",
            "Custom Image ID": "r001-orders-app-image",
        },
        {
            **sample_vm_record,
            "VM Key": "vm-db-001",
            "VM Name": "orders-db-01",
            "Owner": "db-team",
            "Application": "Orders",
            "Wave": "Wave 1",
            "Cutover Group": "CG-DB",
            "Priority": "critical",
            "Dependency Group": "orders-core",
            "Boot Disk GB": 100,
            "Network": "db-net",
            "Subnet": "module.networking.db_net_id",
            "Security Group": "module.networking.db_net_sg_id",
            "IBM Profile": "mx2-2x16",
            "Profile Hourly": 0.20,
            "Storage Tier": "5iops-tier",
            "Override Storage Tier": "10iops-tier",
            "Override Storage Tier Reason": "Production write latency target",
            "Storage Tier Monthly Per GB": 0.10,
            "Override Storage Tier Monthly Per GB": 0.13,
            "Image Readiness": "Review",
            "Readiness Reasons": "Image import pending",
            "Migration Readiness": "Review",
            "Migration Readiness Reasons": "Database quiesce runbook required",
            "Memory Readiness": "Review",
            "Memory Readiness Reasons": "Swapped memory detected",
            "Swapped Memory MiB": 256,
            "Original Specs": "windows-2019-template",
        },
        {
            **sample_vm_record,
            "VM Key": "vm-legacy-001",
            "VM Name": "legacy-batch-01",
            "Owner": "platform-team",
            "Application": "Batch",
            "Wave": "Wave 2",
            "Cutover Group": "CG-Legacy",
            "Priority": "medium",
            "Dependency Group": "legacy",
            "Boot Disk GB": 60,
            "Network": "legacy-net",
            "Subnet": "module.networking.legacy_net_id",
            "Security Group": "module.networking.legacy_net_sg_id",
            "Image Readiness": "Blocked",
            "Readiness Reasons": "Guest OS requires modernization",
            "Migration Readiness": "Blocked",
            "Migration Readiness Reasons": "Unsupported legacy agent installed",
            "Original Specs": "rhel-7-template",
            "Exclude?": True,
            "Exclusion Reason": "Retire before migration",
        },
    ]
    remediation_tracker = {
        "vm-db-001::migration": {
            "vm_key": "vm-db-001",
            "owner": "db-team",
            "status": "Open",
            "due_date": "2026-07-20",
            "notes": "Confirm quiesce steps with database owner.",
            "blocker_type": "Migration",
            "blocker_description": "Database quiesce runbook required",
        },
        "vm-legacy-001::image": {
            "vm_key": "vm-legacy-001",
            "owner": "platform-team",
            "status": "Closed",
            "due_date": "2026-07-01",
            "notes": "Retirement approved.",
            "blocker_type": "Image",
            "blocker_description": "Guest OS requires modernization",
        },
    }
    image_import_status = {
        "rhel-9-template": {
            "target_catalog_id": "r001-orders-app-image",
            "import_status": "Imported",
            "estimated_import_time": "45m",
            "notes": "Ready for Wave 1.",
        },
        "windows-2019-template": {
            "target_catalog_id": "r001-orders-db-image",
            "import_status": "Pending",
            "estimated_import_time": "90m",
            "notes": "Track before database cutover.",
        },
        "rhel-7-template": {
            "target_catalog_id": "",
            "import_status": "Not Required",
            "estimated_import_time": "",
            "notes": "VM excluded from migration.",
        },
    }
    _plan, _planning_state, pricing_catalog = (
        _carbon_plan_state_and_pricing_from_records(
            records,
            remediation_tracker=remediation_tracker,
            image_import_status=image_import_status,
        )
    )

    streamlit_files = _streamlit_package_files(
        records,
        pricing_catalog=pricing_catalog,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )
    carbon_files = _carbon_package_files_from_records(
        records,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )

    expected_package_files = (
        STREAMLIT_HANDOFF_FILES
        | CARBON_MODULAR_TERRAFORM_FILES
        | CARBON_CURRENT_EXTRA_FILES
    )
    assert set(carbon_files) == STREAMLIT_HANDOFF_FILES
    assert STREAMLIT_HANDOFF_FILES.issubset(expected_package_files)

    manifest = json.loads(carbon_files["migration-manifest.json"])
    assert manifest["handoff_files"] == {
        "assessment_quality_csv": "assessment-quality.csv",
        "assessment_quality_json": "assessment-quality.json",
        "cutover_readiness_csv": "cutover-readiness.csv",
        "decision_audit_csv": "decision-audit.csv",
        "disk_mapping_csv": "disk-mapping.csv",
        "image_import_plan_csv": "image-import-plan.csv",
        "image_import_tfvars_example": "image-import-variables.tfvars.example",
        "memory_readiness_csv": "memory-readiness.csv",
        "nic_mapping_csv": "nic-mapping.csv",
        "partition_mapping_csv": "partition-mapping.csv",
        "planning_state_json": "planning-state.json",
        "preflight_report_csv": "preflight-report.csv",
        "preflight_report_json": "preflight-report.json",
        "pricing_diagnostics_csv": "pricing-diagnostics.csv",
        "pricing_diagnostics_json": "pricing-diagnostics.json",
        "readiness_findings_csv": "readiness-findings.csv",
        "remediation_backlog_csv": "remediation-backlog.csv",
        "runbook": "migration-runbook.md",
        "vm_mapping_csv": "vm-mapping.csv",
    }
    assert {
        vm["vm_name"]: {
            "wave": vm["migration"]["wave"],
            "effective_profile": vm["target"]["effective_profile"],
            "effective_storage_tier": vm["target"]["effective_storage_tier"],
            "image_import_status": vm["target"]["image_import_status"],
        }
        for vm in manifest["virtual_machines"]
    } == {
        "orders-app-01": {
            "wave": "Wave 1",
            "effective_profile": "bx2-4x16",
            "effective_storage_tier": "5iops-tier",
            "image_import_status": "Imported",
        },
        "orders-db-01": {
            "wave": "Wave 1",
            "effective_profile": "mx2-2x16",
            "effective_storage_tier": "10iops-tier",
            "image_import_status": "Pending",
        },
        "legacy-batch-01": {
            "wave": "Wave 2",
            "effective_profile": "bx2-2x8",
            "effective_storage_tier": "5iops-tier",
            "image_import_status": "Not Required",
        },
    }
    assert manifest["remediation_tracker_summary"] == {
        "blocker_counts_by_status": {
            "Closed": 1,
            "Open": 1,
        },
        "overdue_count": 0,
        "total_blockers": 2,
    }
    assert manifest["image_import_summary"] == {
        "import_status_breakdown": {
            "Imported": 1,
            "Not Required": 1,
            "Pending": 1,
        },
        "total_images": 3,
        "total_vms_pending_import": 1,
    }

    operational_files = {
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
    }
    for file_name in operational_files:
        assert carbon_files[file_name] == streamlit_files[file_name], file_name
    assert _operational_planning_state(
        carbon_files["planning-state.json"]
    ) == _operational_planning_state(streamlit_files["planning-state.json"])

    def assert_row_fields(row, expected):
        assert {field: row[field] for field in expected} == expected

    audit_rows = _csv_rows(carbon_files["decision-audit.csv"])
    audit_by_vm = {
        row["VM Name"]: row
        for row in audit_rows
        if row["VM Name"] and row["VM Name"] != "TOTAL"
    }
    assert set(audit_by_vm) == {
        "orders-app-01",
        "orders-db-01",
        "legacy-batch-01",
    }
    assert_row_fields(
        audit_by_vm["orders-app-01"],
        {
            "Chosen Profile": "bx2-4x16",
            "Profile Override Reason": "CPU headroom for checkout burst",
            "Include/Exclude": "Include",
            "Total Pricing Impact": "82.08",
        },
    )
    assert_row_fields(
        audit_by_vm["orders-db-01"],
        {
            "Original Storage Tier": "5iops-tier",
            "Chosen Storage Tier": "10iops-tier",
            "Storage Tier Override Reason": "Production write latency target",
            "Storage Cost Delta": "6.0",
        },
    )
    assert_row_fields(
        audit_by_vm["legacy-batch-01"],
        {
            "Include/Exclude": "Exclude",
            "Exclusion Reason": "Retire before migration",
        },
    )

    remediation_rows = [
        row
        for row in _csv_rows(carbon_files["remediation-backlog.csv"])
        if row["VM Key"]
    ]
    assert {row["VM Key"] for row in remediation_rows} == {
        "vm-db-001",
        "vm-legacy-001",
    }
    assert_row_fields(
        next(row for row in remediation_rows if row["VM Key"] == "vm-db-001"),
        {
            "VM Name": "unknown-vm",
            "Owner": "db-team",
            "Status": "Open",
            "Due Date": "2026-07-20",
            "Blocker Description": "Database quiesce runbook required",
        },
    )
    assert_row_fields(
        next(row for row in remediation_rows if row["VM Key"] == "vm-legacy-001"),
        {
            "Owner": "platform-team",
            "Status": "Closed",
            "Notes": "Retirement approved.",
        },
    )

    image_rows = _csv_rows(carbon_files["image-import-plan.csv"])
    image_by_source = {row["Source Image"]: row for row in image_rows}
    assert_row_fields(
        image_by_source["rhel-9-template"],
        {
            "Count of VMs": "1",
            "Owners": "app-team",
            "Target Catalog ID": "r001-orders-app-image",
            "Import Status": "Imported",
        },
    )
    assert_row_fields(
        image_by_source["windows-2019-template"],
        {
            "Count of VMs": "1",
            "Owners": "db-team",
            "Import Status": "Pending",
            "Estimated Import Time": "90m",
        },
    )
    assert_row_fields(
        image_by_source["rhel-7-template"],
        {
            "Count of VMs": "1",
            "Owners": "platform-team",
            "Import Status": "Not Required",
            "Notes": "VM excluded from migration.",
        },
    )
    assert image_by_source["TOTAL"]["Count of VMs"] == "3"

    image_tfvars = carbon_files["image-import-variables.tfvars.example"]
    assert '"orders-app-01" = "r001-orders-app-image"' in image_tfvars
    assert '"orders-db-01" = "replace-with-imported-image-id"' in image_tfvars
    assert '"legacy-batch-01" = "replace-with-imported-image-id"' in image_tfvars

    cutover_rows = _csv_rows(carbon_files["cutover-readiness.csv"])
    assert any(
        row["VM Name"] == "orders-db-01"
        and row["Blocker Category"] == "Image Import Pending"
        and row["Blocker Reason"] == "windows-2019-template import status is Pending"
        for row in cutover_rows
    )
    assert not any(
        row["VM Name"] == "orders-app-01"
        and row["Blocker Category"] == "Image Import Pending"
        for row in cutover_rows
    )
    assert any(
        row["VM Name"] == "legacy-batch-01"
        and row["Blocker Category"] == "Readiness Blocker"
        and row["Cutover Status"] == "Blocked"
        for row in cutover_rows
    )
    assert not any(
        row["VM Name"] == "legacy-batch-01"
        and row["Blocker Category"] == "Unresolved Remediation"
        for row in cutover_rows
    )

    planning_state = json.loads(carbon_files["planning-state.json"])
    decisions_by_vm = {
        row["VM Name"]: row
        for row in planning_state["vm_decisions"]
    }
    assert_row_fields(
        decisions_by_vm["orders-app-01"],
        {
            "Override Profile": "bx2-4x16",
            "Override Storage Tier": "",
            "Exclude?": False,
        },
    )
    assert_row_fields(
        decisions_by_vm["legacy-batch-01"],
        {
            "Override Profile": "",
            "Override Storage Tier": "",
            "Exclude?": True,
        },
    )
    assert {row["Wave"] for row in planning_state["wave_planning"]} == {
        "Wave 1",
        "Wave 2",
    }


def test_carbon_workshop_workbook_unknown_network_subset_matches_streamlit_handoff():
    summary = _workshop_workbook_summary()
    records = [
        next(
            row
            for row in summary["assignment_rows"]
            if row["VM Name"] == vm_name
        )
        for vm_name in ("AKWSVCIDM1-1", "BBWMFG01", "BOWAB10SP1JS02")
    ]
    image_import_status = {
        "1v / 4096M": {
            "target_catalog_id": "",
            "import_status": "Pending",
            "estimated_import_time": "30m",
            "notes": "Workshop unknown-network validation.",
        },
        "8v / 16384M": {
            "target_catalog_id": "",
            "import_status": "Pending",
            "estimated_import_time": "60m",
            "notes": "Workshop unknown-network validation.",
        },
        "8v / 32768M": {
            "target_catalog_id": "",
            "import_status": "Pending",
            "estimated_import_time": "90m",
            "notes": "Workshop unknown-network validation.",
        },
    }
    _plan, _planning_state, pricing_catalog = (
        _carbon_plan_state_and_pricing_from_records(
            records,
            assessment_quality=summary["assessment_quality"],
            image_import_status=image_import_status,
        )
    )

    streamlit_files = _streamlit_package_files(
        records,
        pricing_catalog=pricing_catalog,
        remediation_tracker={},
        image_import_status=image_import_status,
        assessment_quality=summary["assessment_quality"],
    )
    carbon_files = _carbon_package_files_from_records(
        records,
        assessment_quality=summary["assessment_quality"],
        remediation_tracker={},
        image_import_status=image_import_status,
    )

    exact_handoff_files = {
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
        "assessment-quality.json",
        "assessment-quality.csv",
        "pricing-diagnostics.json",
        "pricing-diagnostics.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
    }
    for file_name in exact_handoff_files:
        assert carbon_files[file_name] == streamlit_files[file_name], file_name
    assert _operational_planning_state(
        carbon_files["planning-state.json"]
    ) == _operational_planning_state(streamlit_files["planning-state.json"])

    vm_rows = _csv_rows(carbon_files["vm-mapping.csv"])
    assert {row["Source Network"] for row in vm_rows} == {"unknown-net"}
    assert {
        row["Network Readiness Reasons"]
        for row in vm_rows
    } == {
        "Network adapter 1 is connected but has no usable network name",
        "Network adapter 2 is connected but has no usable network name",
        "Network adapter 3 is connected but has no usable network name",
    }

    memory_rows = _csv_rows(carbon_files["memory-readiness.csv"])
    assert {row["Memory Sizing Basis"] for row in memory_rows} == {
        "missing-vmemory-preserve-configured-memory"
    }

    disk_rows = _csv_rows(carbon_files["disk-mapping.csv"])
    partition_rows = _csv_rows(carbon_files["partition-mapping.csv"])
    assert disk_rows == []
    assert partition_rows == []

    assessment_quality = json.loads(carbon_files["assessment-quality.json"])
    assert assessment_quality["overall_confidence"] == "Low"
    assert assessment_quality["optional_readiness_tabs_present"] == 0
    assert assessment_quality["optional_network_detail_tabs_present"] == 0

    image_rows = _csv_rows(carbon_files["image-import-plan.csv"])
    image_row = next(
        row for row in image_rows if row["Source Image"] == "8v / 32768M"
    )
    expected_image_fields = {
        "Import Status": "Pending",
        "Estimated Import Time": "90m",
        "Notes": "Workshop unknown-network validation.",
    }
    assert {
        field: image_row[field]
        for field in expected_image_fields
    } == expected_image_fields


def test_carbon_sample_workbook_operational_overlays_match_streamlit_handoff():
    summary = _sample_workbook_summary()
    records = [dict(row) for row in summary["assignment_rows"]]

    db_record = next(row for row in records if row["VM Name"] == "sample-db-01")
    db_record.update(
        {
            "Owner": "db-team",
            "Application": "Orders",
            "Wave": "Wave 1",
            "Cutover Group": "CG-DB",
            "Priority": "high",
            "Dependency Group": "orders-core",
            "Override Storage Tier": "5iops-tier",
            "Override Storage Tier Reason": "Archive workload after migration",
            "Override Storage Tier Monthly Per GB": 0.10,
        }
    )

    web_record = next(row for row in records if row["VM Name"] == "sample-web-01")
    web_record.update(
        {
            "Owner": "app-team",
            "Application": "Orders",
            "Wave": "Wave 2",
            "Cutover Group": "CG-Web",
            "Priority": "medium",
            "Dependency Group": "orders-web",
            "Override Profile": "bx2-4x16",
            "Override Profile Reason": "Add headroom for launch window",
            "Override Profile Hourly": 0.188,
            "Custom Image ID": "r001-orders-web-image",
        }
    )

    remediation_tracker = {
        "sample-db-01::migration": {
            "vm_key": "sample-db-01",
            "owner": "db-team",
            "status": "Open",
            "due_date": "2026-07-21",
            "notes": "Clear snapshots and update VMware Tools.",
            "blocker_type": "Migration",
            "blocker_description": "VMware Tools status requires review",
        },
        "sample-web-01::image": {
            "vm_key": "sample-web-01",
            "owner": "app-team",
            "status": "Closed",
            "due_date": "2026-07-10",
            "notes": "Ubuntu image import completed.",
            "blocker_type": "Image",
            "blocker_description": "Multiple disks detected; map data disks separately",
        },
    }
    image_import_status = {
        "4v / 16384M": {
            "target_catalog_id": "r001-sample-db-image",
            "import_status": "Pending",
            "estimated_import_time": "60m",
            "notes": "Track Windows image import before database cutover.",
        },
        "2v / 8192M": {
            "target_catalog_id": "r001-orders-web-image",
            "import_status": "Imported",
            "estimated_import_time": "35m",
            "notes": "Golden Ubuntu image ready for Wave 2.",
        },
    }
    _plan, _planning_state, pricing_catalog = (
        _carbon_plan_state_and_pricing_from_records(
            records,
            assessment_quality=summary["assessment_quality"],
            remediation_tracker=remediation_tracker,
            image_import_status=image_import_status,
        )
    )

    streamlit_files = _streamlit_package_files(
        records,
        pricing_catalog=pricing_catalog,
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
        assessment_quality=summary["assessment_quality"],
    )
    carbon_files = _carbon_package_files_from_records(
        records,
        assessment_quality=summary["assessment_quality"],
        remediation_tracker=remediation_tracker,
        image_import_status=image_import_status,
    )

    operational_files = {
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "cutover-readiness.csv",
        "vm-mapping.csv",
        "disk-mapping.csv",
        "partition-mapping.csv",
        "nic-mapping.csv",
        "memory-readiness.csv",
        "readiness-findings.csv",
    }
    for file_name in operational_files:
        assert carbon_files[file_name] == streamlit_files[file_name], file_name
    assert _operational_planning_state(
        carbon_files["planning-state.json"]
    ) == _operational_planning_state(streamlit_files["planning-state.json"])

    def assert_row_fields(row, expected):
        assert {field: row[field] for field in expected} == expected

    audit_rows = _csv_rows(carbon_files["decision-audit.csv"])
    audit_by_vm = {
        row["VM Name"]: row
        for row in audit_rows
        if row["VM Name"] and row["VM Name"] != "TOTAL"
    }
    assert_row_fields(
        audit_by_vm["sample-db-01"],
        {
            "Original Storage Tier": "10iops-tier",
            "Chosen Storage Tier": "5iops-tier",
            "Storage Tier Override Reason": "Archive workload after migration",
            "Include/Exclude": "Include",
        },
    )
    assert_row_fields(
        audit_by_vm["sample-web-01"],
        {
            "Original Profile": "bx2-2x8",
            "Chosen Profile": "bx2-4x16",
            "Profile Override Reason": "Add headroom for launch window",
            "Include/Exclude": "Include",
        },
    )

    remediation_rows = [
        row
        for row in _csv_rows(carbon_files["remediation-backlog.csv"])
        if row["VM Key"]
    ]
    assert {row["VM Key"] for row in remediation_rows} == {
        "sample-db-01",
        "sample-web-01",
    }
    assert_row_fields(
        next(row for row in remediation_rows if row["VM Key"] == "sample-db-01"),
        {
            "Owner": "db-team",
            "Status": "Open",
            "Due Date": "2026-07-21",
        },
    )

    image_rows = _csv_rows(carbon_files["image-import-plan.csv"])
    image_by_source = {row["Source Image"]: row for row in image_rows}
    assert_row_fields(
        image_by_source["2v / 8192M"],
        {
            "Count of VMs": "1",
            "Owners": "app-team",
            "Target Catalog ID": "r001-orders-web-image",
            "Import Status": "Imported",
        },
    )
    assert image_by_source["TOTAL"]["Count of VMs"] == "2"

    disk_rows = _csv_rows(carbon_files["disk-mapping.csv"])
    data_disks = [
        row
        for row in disk_rows
        if row["Target Action"] == "create-and-attach-volume"
    ]
    assert {
        (row["VM Name"], row["Disk"], row["Terraform Volume"])
        for row in data_disks
    } == {
        ("sample-db-01", "Hard disk 2", "sample_db_01_hard_disk_2_vol"),
        ("sample-web-01", "Hard disk 2", "sample_web_01_hard_disk_2_vol"),
    }

    partition_rows = _csv_rows(carbon_files["partition-mapping.csv"])
    assert {
        (row["VM Name"], row["Partition"], row["Matched To Disk"])
        for row in partition_rows
    } == {
        ("sample-db-01", "C:\\", "True"),
        ("sample-db-01", "D:\\", "True"),
        ("sample-web-01", "/", "True"),
        ("sample-web-01", "/var", "True"),
    }

    cutover_rows = _csv_rows(carbon_files["cutover-readiness.csv"])
    assert any(
        row["VM Name"] == "sample-db-01"
        and row["Wave"] == "Wave 1"
        and row["Blocker Category"] == "Image Import Pending"
        for row in cutover_rows
    )
    assert any(
        row["VM Name"] == "sample-web-01"
        and row["Wave"] == "Wave 2"
        and row["Blocker Category"] == "Readiness Review"
        for row in cutover_rows
    )

    planning_state = json.loads(carbon_files["planning-state.json"])
    wave_by_vm = {
        row["VM Name"]: row
        for row in planning_state["wave_planning"]
    }
    assert_row_fields(
        wave_by_vm["sample-db-01"],
        {
            "Wave": "Wave 1",
            "Cutover Group": "CG-DB",
            "Owner": "db-team",
            "Application": "Orders",
            "Priority": "high",
            "Dependency Group": "orders-core",
        },
    )
    assert_row_fields(
        wave_by_vm["sample-web-01"],
        {
            "Wave": "Wave 2",
            "Cutover Group": "CG-Web",
            "Owner": "app-team",
            "Application": "Orders",
            "Priority": "medium",
            "Dependency Group": "orders-web",
        },
    )


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
        remediation_tracker=SAMPLE_REMEDIATION_TRACKER,
        image_import_status=SAMPLE_IMAGE_IMPORT_STATUS,
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


def test_carbon_sample_workbook_api_zip_matches_expected_handoff_inventory():
    project_id, project, project_state = _sample_carbon_project_fixture()

    with (
        patch("prototype.api.persistence.persistence_enabled", return_value=True),
        patch(
            "prototype.api.persistence.get_project",
            return_value=project,
        ),
        patch(
            "prototype.api.persistence.get_project_state",
            return_value=project_state,
        ),
    ):
        response = TestClient(app).post(f"/api/projects/{project_id}/terraform")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        manifest_payload = json.loads(
            archive.read("migration-manifest.json").decode("utf-8")
        )
        decision_audit_rows = _csv_rows(
            archive.read("decision-audit.csv").decode("utf-8")
        )
        remediation_rows = _csv_rows(
            archive.read("remediation-backlog.csv").decode("utf-8")
        )
        image_rows = _csv_rows(
            archive.read("image-import-plan.csv").decode("utf-8")
        )
        planning_state_payload = json.loads(
            archive.read("planning-state.json").decode("utf-8")
        )
        network_plan_payload = json.loads(
            archive.read("network-plan.json").decode("utf-8")
        )

    assert STREAMLIT_HANDOFF_FILES.issubset(names)
    assert CARBON_MODULAR_TERRAFORM_FILES.issubset(names)
    assert (
        names - STREAMLIT_HANDOFF_FILES - CARBON_MODULAR_TERRAFORM_FILES
        == CARBON_CURRENT_EXTRA_FILES
    )
    assert set(manifest_payload["handoff_files"].values()).issubset(names)
    assert {
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "planning-state.json",
    }.issubset(set(manifest_payload["handoff_files"].values()))
    assert any(
        row["VM Name"] == "sample-db-01"
        and row["Original Storage Tier"] == "10iops-tier"
        for row in decision_audit_rows
    )
    assert any(
        row["VM Key"] == "sample-db-01"
        and row["Owner"] == "db-team"
        and row["Status"] == "Open"
        for row in remediation_rows
    )
    assert any(
        row["Source Image"] == "4v / 16384M"
        and row["Import Status"] == "Pending"
        and row["Target Catalog ID"] == "r001-sample-db-image"
        for row in image_rows
    )
    assert planning_state_payload["schema_version"] == "1.0"
    assert network_plan_payload["metadata"]["project_name"] == "Migration"


def test_carbon_package_preview_matches_api_zip_contents():
    project_id, project, project_state = _sample_carbon_project_fixture()

    with (
        patch("prototype.api.persistence.persistence_enabled", return_value=True),
        patch("prototype.api.persistence.get_project", return_value=project),
        patch("prototype.api.persistence.get_project_state", return_value=project_state),
    ):
        client = TestClient(app)
        preview_response = client.post(f"/api/projects/{project_id}/terraform/preview")
        zip_response = client.post(f"/api/projects/{project_id}/terraform")

    assert preview_response.status_code == 200
    assert zip_response.status_code == 200

    preview_payload = preview_response.json()
    preview_files = {
        file["path"]: file
        for file in preview_payload["files"]
    }
    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as archive:
        zip_files = {
            name: archive.read(name).decode("utf-8")
            for name in archive.namelist()
        }

    assert set(preview_files) == set(zip_files)
    assert preview_payload["project_id"] == project_id
    assert preview_payload["project_name"] == "Migration"

    for file_name in {
        "migration-manifest.json",
        "decision-audit.csv",
        "remediation-backlog.csv",
        "image-import-plan.csv",
        "network-plan.json",
    }:
        assert preview_files[file_name]["content"] == zip_files[file_name]
        assert preview_files[file_name]["size_bytes"] == len(
            zip_files[file_name].encode("utf-8")
        )

    assert preview_files["migration-manifest.json"]["category"] == "Migration handoff"
    assert preview_files["decision-audit.csv"]["category"] == "Migration handoff"
    assert preview_files["network-plan.json"]["category"] == "Carbon state"
