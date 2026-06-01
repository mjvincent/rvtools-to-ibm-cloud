from models import MigrationVm


def build_final_vms(source_df, processed_vms, disk_details, nic_details):
    final_vm_records = [
        v for v in source_df.to_dict("records")
        if not v.get("Exclude?")
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
            [],
        )
        vm["Network Details"] = nic_details.get(vm.get("VM Key"), [])
        vm["Readiness Findings"] = next(
            (
                source.get("Readiness Findings", [])
                for source in processed_vms
                if source.get("VM Key") == vm.get("VM Key")
            ),
            [],
        )
        final_vms.append(MigrationVm.from_record(vm))
    return final_vms

