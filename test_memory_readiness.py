import csv
import io
import json

from logic_engine import (
    assess_memory_readiness,
    generate_memory_readiness_csv,
    generate_migration_manifest,
    generate_vm_mapping_csv,
    map_vmware_to_ibm_vpc,
)


def test_memory_ready_uses_conservative_active_sizing():
    readiness = assess_memory_readiness(
        configured_mib=16384,
        active_mib=2048,
        consumed_mib=8192,
        ballooned_mib=0,
        swapped_mib=0,
        reservation_mib=0,
        limit_mib=-1,
        hot_add=False,
    )
    assert readiness["status"] == "Review"
    assert readiness["sizing_memory_mib"] == 8192
    assert readiness["sizing_basis"] == "active-memory-with-50-percent-floor"


def test_memory_pressure_blocks_resizing():
    readiness = assess_memory_readiness(
        configured_mib=8192,
        active_mib=4096,
        consumed_mib=8192,
        ballooned_mib=0,
        swapped_mib=2048,
        reservation_mib=0,
        limit_mib=-1,
        hot_add=False,
    )
    assert readiness["status"] == "Blocked"
    assert readiness["sizing_memory_mib"] == 8192
    assert "Severe memory pressure" in readiness["reasons"]


def test_memory_limit_below_configured_blocks():
    readiness = assess_memory_readiness(
        configured_mib=16384,
        active_mib=4096,
        consumed_mib=12000,
        ballooned_mib=0,
        swapped_mib=0,
        reservation_mib=0,
        limit_mib=8192,
        hot_add=True,
    )
    assert readiness["status"] == "Blocked"
    assert readiness["sizing_memory_mib"] == 16384
    assert "Memory limit is below configured memory" in readiness["reasons"]


def test_missing_vmemory_preserves_configured_memory():
    readiness = assess_memory_readiness(
        configured_mib=16384,
        active_mib=0,
        consumed_mib=0,
        ballooned_mib=0,
        swapped_mib=0,
        reservation_mib=0,
        limit_mib=-1,
        hot_add="",
        source_available=False,
    )
    assert readiness["status"] == "Review"
    assert readiness["sizing_memory_mib"] == 16384
    assert readiness["sizing_basis"] == (
        "missing-vmemory-preserve-configured-memory"
    )


def test_memory_handoff_outputs_include_memory_fields():
    vm = {
        "VM Name": "mem01",
        "Power State": "poweredOn",
        "Guest OS": "Red Hat Enterprise Linux 9 (64-bit)",
        "Network": "App_Net",
        "Memory Readiness": "Review",
        "Memory Readiness Reasons": "Memory hot-add enabled",
        "Configured Memory MiB": 16384,
        "Active Memory MiB": 2048,
        "Consumed Memory MiB": 8192,
        "Ballooned Memory MiB": 0,
        "Swapped Memory MiB": 0,
        "Memory Reservation MiB": 0,
        "Memory Limit MiB": -1,
        "Memory Hot Add": "True",
        "Sizing Memory MiB": 8192,
        "Memory Sizing Basis": "active-memory-with-50-percent-floor",
        "IBM Profile": "bx2-2x8",
        "Storage Tier": "3iops-tier",
    }

    mapping_rows = list(csv.DictReader(io.StringIO(generate_vm_mapping_csv([vm]))))
    assert mapping_rows[0]["Memory Readiness"] == "Review"
    assert mapping_rows[0]["Sizing Memory MiB"] == "8192"

    memory_rows = list(
        csv.DictReader(io.StringIO(generate_memory_readiness_csv([vm])))
    )
    assert memory_rows[0]["Memory Sizing Basis"] == (
        "active-memory-with-50-percent-floor"
    )

    manifest = json.loads(generate_migration_manifest([vm], {
        "project_name": "test",
        "target_region": "us-south",
        "target_zone": "us-south-1",
        "vpc_name": "migration-vpc",
    }))
    handoff_files = manifest["handoff_files"]
    assert handoff_files["memory_readiness_csv"] == "memory-readiness.csv"
    memory_readiness = (
        manifest["virtual_machines"][0]["assessment"]["memory_readiness"]
    )
    assert memory_readiness["status"] == "Review"
    assert memory_readiness["sizing_memory_mib"] == 8192


def test_sizing_memory_is_not_reduced_twice():
    mapping = map_vmware_to_ibm_vpc(
        cpus=2,
        memory=8192,
        usage=40,
        region="us-south",
        threshold=40,
        storage_gb=100,
        tier="3iops-tier",
        memory_is_sizing=True,
    )
    assert mapping["profile"] == "bx2-2x8"


if __name__ == "__main__":
    test_memory_ready_uses_conservative_active_sizing()
    test_memory_pressure_blocks_resizing()
    test_memory_limit_below_configured_blocks()
    test_missing_vmemory_preserves_configured_memory()
    test_memory_handoff_outputs_include_memory_fields()
    test_sizing_memory_is_not_reduced_twice()
    print("memory readiness tests ok")
