"""Snapshot tests for decision_audit_export() output.

Tests cover:
- Basic CSV generation for a single VM with no overrides
- CSV generation when profile/storage overrides exist, verifying cost deltas
- Inclusion of wave metadata (owner/application/wave)
- Handling of excluded VMs (Include/Exclude columns)
"""
import csv
import io

from models import MigrationVm
from handoff import decision_audit_export


def parse_csv(text):
    """Parse CSV text into list of dicts."""
    return list(csv.DictReader(io.StringIO(text)))


def test_decision_audit_basic_single_vm_no_overrides(assert_matches_snapshot):
    """Test basic CSV generation for single VM with no overrides."""
    vm = MigrationVm(
        vm_key="vm-001",
        vm_name="app-01",
        ibm_profile="bx2-2x8",
        storage_tier="3iops-tier",
        total_storage_gb=100,
        owner="John Doe",
        application="Web Server",
        wave="Wave 1",
        compute_cost_monthly=50.0,
        storage_cost_monthly=10.0,
        monthly_cost=60.0,
        profile_hourly=0.114,
    )

    pricing_catalog = {
        "profiles": {
            "bx2-2x8": {
                "hourly": 0.114,
                "cpu": 2,
                "ram": 8,
            }
        },
        "storage_tiers": {
            "3iops-tier": {
                "monthly_per_gb": 0.10,
            }
        },
    }

    result = decision_audit_export([vm], pricing_catalog)
    assert_matches_snapshot("decision_audit_basic_single_vm.csv", result)


def test_decision_audit_with_profile_override(assert_matches_snapshot):
    """Test CSV generation with profile override, verifying cost deltas."""
    vm = MigrationVm(
        vm_key="vm-002",
        vm_name="app-02",
        ibm_profile="bx2-2x8",
        override_profile="bx2-4x16",
        override_profile_reason="Increased performance needed",
        storage_tier="3iops-tier",
        total_storage_gb=100,
        owner="Jane Smith",
        application="API Server",
        wave="Wave 1",
        compute_cost_monthly=50.0,
        storage_cost_monthly=10.0,
        monthly_cost=60.0,
        profile_hourly=0.114,
    )

    pricing_catalog = {
        "profiles": {
            "bx2-2x8": {
                "hourly": 0.114,
                "cpu": 2,
                "ram": 8,
            },
            "bx2-4x16": {
                "hourly": 0.227,
                "cpu": 4,
                "ram": 16,
            }
        },
        "storage_tiers": {
            "3iops-tier": {
                "monthly_per_gb": 0.10,
            }
        },
    }

    result = decision_audit_export([vm], pricing_catalog)
    assert_matches_snapshot("decision_audit_with_profile_override.csv", result)


def test_decision_audit_with_storage_override(assert_matches_snapshot):
    """Test CSV generation with storage tier override, verifying cost deltas."""
    vm = MigrationVm(
        vm_key="vm-003",
        vm_name="db-01",
        ibm_profile="bx2-2x8",
        storage_tier="3iops-tier",
        override_storage_tier="5iops-tier",
        override_storage_tier_reason="Database requires higher IOPS",
        total_storage_gb=200,
        owner="Bob Johnson",
        application="Database",
        wave="Wave 2",
        compute_cost_monthly=50.0,
        storage_cost_monthly=20.0,
        monthly_cost=70.0,
        profile_hourly=0.114,
    )

    pricing_catalog = {
        "profiles": {
            "bx2-2x8": {
                "hourly": 0.114,
                "cpu": 2,
                "ram": 8,
            }
        },
        "storage_tiers": {
            "3iops-tier": {
                "monthly_per_gb": 0.10,
            },
            "5iops-tier": {
                "monthly_per_gb": 0.15,
            }
        },
    }

    result = decision_audit_export([vm], pricing_catalog)
    assert_matches_snapshot("decision_audit_with_storage_override.csv", result)


def test_decision_audit_excluded_vm(assert_matches_snapshot):
    """Test CSV generation with excluded VM."""
    vm = MigrationVm(
        vm_key="vm-004",
        vm_name="legacy-vm",
        exclude=True,
        exclusion_reason="VM being decommissioned",
        ibm_profile="bx2-2x8",
        storage_tier="3iops-tier",
        total_storage_gb=50,
        owner="Admin",
        application="Legacy",
        wave="",
        compute_cost_monthly=50.0,
        storage_cost_monthly=5.0,
        monthly_cost=55.0,
        profile_hourly=0.114,
    )

    pricing_catalog = {
        "profiles": {
            "bx2-2x8": {
                "hourly": 0.114,
                "cpu": 2,
                "ram": 8,
            }
        },
        "storage_tiers": {
            "3iops-tier": {
                "monthly_per_gb": 0.10,
            }
        },
    }

    result = decision_audit_export([vm], pricing_catalog)
    assert_matches_snapshot("decision_audit_excluded_vm.csv", result)


def test_decision_audit_multiple_vms_mixed_overrides(assert_matches_snapshot):
    """Test CSV generation with multiple VMs, mixed overrides and inclusions."""
    vms = [
        MigrationVm(
            vm_key="vm-101",
            vm_name="web-01",
            ibm_profile="bx2-2x8",
            storage_tier="3iops-tier",
            total_storage_gb=100,
            owner="John Doe",
            application="Web Server",
            wave="Wave 1",
            compute_cost_monthly=50.0,
            storage_cost_monthly=10.0,
            monthly_cost=60.0,
            profile_hourly=0.114,
        ),
        MigrationVm(
            vm_key="vm-102",
            vm_name="api-01",
            ibm_profile="bx2-2x8",
            override_profile="bx2-4x16",
            override_profile_reason="High throughput API",
            storage_tier="3iops-tier",
            override_storage_tier="5iops-tier",
            override_storage_tier_reason="API caching layer",
            total_storage_gb=150,
            owner="Jane Smith",
            application="API Server",
            wave="Wave 1",
            compute_cost_monthly=50.0,
            storage_cost_monthly=15.0,
            monthly_cost=65.0,
            profile_hourly=0.114,
        ),
        MigrationVm(
            vm_key="vm-103",
            vm_name="db-01",
            ibm_profile="bx2-2x8",
            storage_tier="3iops-tier",
            total_storage_gb=250,
            owner="Bob Johnson",
            application="Database",
            wave="Wave 2",
            exclude=True,
            exclusion_reason="Being migrated separately",
            compute_cost_monthly=50.0,
            storage_cost_monthly=25.0,
            monthly_cost=75.0,
            profile_hourly=0.114,
        ),
    ]

    pricing_catalog = {
        "profiles": {
            "bx2-2x8": {
                "hourly": 0.114,
                "cpu": 2,
                "ram": 8,
            },
            "bx2-4x16": {
                "hourly": 0.227,
                "cpu": 4,
                "ram": 16,
            }
        },
        "storage_tiers": {
            "3iops-tier": {
                "monthly_per_gb": 0.10,
            },
            "5iops-tier": {
                "monthly_per_gb": 0.15,
            }
        },
    }

    result = decision_audit_export(vms, pricing_catalog)
    assert_matches_snapshot("decision_audit_multiple_vms_mixed.csv", result)


def test_decision_audit_empty_catalog_fallback(assert_matches_snapshot):
    """Test CSV generation with empty pricing catalog (fallback handling)."""
    vm = MigrationVm(
        vm_key="vm-005",
        vm_name="app-05",
        ibm_profile="bx2-2x8",
        storage_tier="3iops-tier",
        total_storage_gb=100,
        owner="Alice Lee",
        application="Fallback Test",
        wave="Wave 1",
        compute_cost_monthly=50.0,
        storage_cost_monthly=10.0,
        monthly_cost=60.0,
        profile_hourly=0.114,
    )

    # Empty catalog
    pricing_catalog = {}

    result = decision_audit_export([vm], pricing_catalog)
    assert_matches_snapshot("decision_audit_empty_catalog.csv", result)


def test_decision_audit_csv_structure_validation(assert_matches_snapshot):
    """Test that CSV structure matches expected headers and totals row."""
    vms = [
        MigrationVm(
            vm_key="vm-201",
            vm_name="test-vm-1",
            ibm_profile="bx2-2x8",
            storage_tier="3iops-tier",
            total_storage_gb=50,
            owner="Owner 1",
            application="App 1",
            wave="Wave 1",
            compute_cost_monthly=25.0,
            storage_cost_monthly=5.0,
            monthly_cost=30.0,
            profile_hourly=0.114,
        ),
        MigrationVm(
            vm_key="vm-202",
            vm_name="test-vm-2",
            ibm_profile="bx2-4x16",
            storage_tier="5iops-tier",
            total_storage_gb=100,
            owner="Owner 2",
            application="App 2",
            wave="Wave 2",
            compute_cost_monthly=50.0,
            storage_cost_monthly=15.0,
            monthly_cost=65.0,
            profile_hourly=0.227,
        ),
    ]

    pricing_catalog = {
        "profiles": {
            "bx2-2x8": {"hourly": 0.114},
            "bx2-4x16": {"hourly": 0.227},
        },
        "storage_tiers": {
            "3iops-tier": {"monthly_per_gb": 0.10},
            "5iops-tier": {"monthly_per_gb": 0.15},
        },
    }

    result = decision_audit_export(vms, pricing_catalog)
    
    # Validate CSV structure
    rows = parse_csv(result)
    
    # Should have 3 rows: 2 VMs + 1 TOTAL row
    assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"
    
    # First row should be first VM
    assert rows[0]["VM Key"] == "vm-201"
    assert rows[0]["VM Name"] == "test-vm-1"
    assert rows[0]["Owner"] == "Owner 1"
    assert rows[0]["Application"] == "App 1"
    assert rows[0]["Wave"] == "Wave 1"
    assert rows[0]["Include/Exclude"] == "Include"
    
    # Second row should be second VM
    assert rows[1]["VM Key"] == "vm-202"
    assert rows[1]["VM Name"] == "test-vm-2"
    
    # Third row should be TOTAL row
    assert rows[2]["VM Name"] == "TOTAL"
    
    # Verify all expected columns exist
    expected_headers = [
        "VM Key", "VM Name", "Owner", "Application", "Wave",
        "Original Profile", "Chosen Profile", "Profile Override Reason",
        "Original Storage Tier", "Chosen Storage Tier", "Storage Tier Override Reason",
        "Network Mode", "Include/Exclude", "Exclusion Reason",
        "vCPU Cost Delta", "Storage Cost Delta", "Total Pricing Impact",
    ]
    actual_headers = list(rows[0].keys())
    assert actual_headers == expected_headers, f"Headers mismatch: {actual_headers}"
    
    # Validate snapshot for full output
    assert_matches_snapshot("decision_audit_csv_structure.csv", result)
