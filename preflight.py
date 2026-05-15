import csv
import ipaddress
import io
import json
from collections import Counter
from dataclasses import dataclass

from assessments import IMAGE_MAX_GB
from models import MigrationVm, as_bool, clean_value
from sizing import STORAGE_TIERS
from terraform_renderer import _safe_resource_name


PROFILE_REGION_SUPPORT = {
    "us-south": {"bx2", "cx2", "mx2"},
    "us-east": {"bx2", "cx2", "mx2"},
    "eu-gb": {"bx2", "cx2", "mx2"},
    "jp-tok": {"bx2", "cx2", "mx2"},
}


@dataclass(frozen=True)
class PreflightFinding:
    severity: str
    category: str
    subject: str
    message: str
    remediation: str = ""
    fix_location: str = ""
    suggested_action: str = ""
    valid_options: tuple = ()
    recommended_option: str = ""
    quick_fix_type: str = ""
    field: str = ""
    current_value: str = ""
    constraint: str = ""

    def to_record(self):
        return {
            "Severity": self.severity,
            "Category": self.category,
            "Subject": self.subject,
            "Message": self.message,
            "Remediation": self.remediation,
            "Fix Location": self.fix_location,
            "Suggested Action": self.suggested_action,
            "Valid Options": ", ".join(self.valid_options),
            "Recommended Option": self.recommended_option,
            "Quick Fix Type": self.quick_fix_type,
            "Field": self.field,
            "Current Value": self.current_value,
            "Constraint": self.constraint,
        }


def _as_vm(value):
    if isinstance(value, MigrationVm):
        return value
    return MigrationVm.from_record(value)


def _normalize_vms(final_vms):
    return [_as_vm(vm) for vm in final_vms]


def _vm_name(vm):
    return clean_value(vm.get("VM Name"), "unknown-vm")


def _effective_profile(vm):
    return clean_value(vm.get("Override Profile")) or clean_value(
        vm.get("IBM Profile")
    )


def _effective_storage_tier(vm):
    return clean_value(vm.get("Override Storage Tier")) or clean_value(
        vm.get("Storage Tier")
    )


def _vm_nics(vm):
    nics = vm.source.nics or vm.nics
    normalized = []
    for nic in nics or []:
        normalized.append(nic.to_record() if hasattr(nic, "to_record") else nic)
    return normalized


def _connected_nics(vm):
    return [
        nic for nic in _vm_nics(vm)
        if as_bool(nic.get("connected", True), True)
    ]


def _network_resource_names(networks):
    names = []
    for net in networks:
        raw_name = clean_value(net.get("name"), "unknown-net")
        vlan = clean_value(net.get("vlan"))
        safe = _safe_resource_name(raw_name)
        if vlan:
            safe = f"{safe}_vlan_{vlan}"
        names.append((raw_name, safe))
    return names


def _find_cidr_issues(networks, custom_cidrs):
    findings = []
    parsed = []
    seen = {}
    for index, net in enumerate(networks):
        name = clean_value(net.get("name"), f"network-{index + 1}")
        cidr_key = clean_value(net.get("cidr_key")) or clean_value(
            net.get("name")
        )
        cidr = clean_value(
            custom_cidrs.get(cidr_key) if custom_cidrs else "",
            clean_value(net.get("cidr"), f"10.0.{index + 1}.0/24"),
        )
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            findings.append(PreflightFinding(
                "blocker",
                "cidr",
                name,
                f"Invalid CIDR '{cidr}' for network '{name}'.",
                "Enter a valid IPv4 CIDR before building the Terraform package.",
                "Export > Custom CIDRs per Subnet",
                "Replace the invalid CIDR with a valid IPv4 CIDR range.",
                current_value=cidr,
                constraint="Valid IPv4 CIDR, for example 10.0.1.0/24.",
            ))
            continue
        parsed.append((name, cidr, network))
        if str(network) in seen:
            findings.append(PreflightFinding(
                "blocker",
                "cidr",
                name,
                f"CIDR '{cidr}' duplicates network '{seen[str(network)]}'.",
                "Assign a unique CIDR to each generated subnet.",
                "Export > Custom CIDRs per Subnet",
                "Use a unique CIDR for each generated subnet.",
                current_value=cidr,
                constraint="CIDRs must be unique and non-overlapping.",
            ))
        else:
            seen[str(network)] = name

    for left_index, (left_name, left_cidr, left_net) in enumerate(parsed):
        for right_name, right_cidr, right_net in parsed[left_index + 1:]:
            if left_net.overlaps(right_net):
                findings.append(PreflightFinding(
                    "blocker",
                    "cidr",
                    f"{left_name} / {right_name}",
                    f"CIDR '{left_cidr}' overlaps '{right_cidr}'.",
                    "Use non-overlapping target CIDRs for generated subnets.",
                    "Export > Custom CIDRs per Subnet",
                    "Change one subnet CIDR so the ranges no longer overlap.",
                    current_value=f"{left_cidr}, {right_cidr}",
                    constraint="CIDRs must be unique and non-overlapping.",
                ))
    return findings


def _image_placeholder_findings(vms):
    findings = []
    for vm in vms:
        image_id = clean_value(vm.get("Custom Image ID"))
        if image_id in {"", "replace-with-imported-image-id"}:
            findings.append(PreflightFinding(
                "warning",
                "custom_image",
                _vm_name(vm),
                "Custom image ID is not resolved before package generation.",
                (
                    "Populate custom_image_ids after image import using "
                    "image-import-variables.tfvars.example."
                ),
                "Image import variables",
                "Import the VM image, then replace the placeholder image ID in the generated tfvars example.",
                quick_fix_type="image_placeholder",
                field="Custom Image ID",
                current_value=image_id,
            ))
    return findings


def _readiness_findings(vms):
    findings = []
    readiness_columns = [
        "Image Readiness", "Migration Readiness", "Memory Readiness"
    ]
    for vm in vms:
        for column in readiness_columns:
            if clean_value(vm.get(column)).lower() == "blocked":
                current_value = clean_value(vm.get(column))
                constraint = ""
                suggested_action = (
                    "Review the readiness reason, remediate the source issue, "
                    "or exclude this VM from the Terraform package."
                )
                if column == "Image Readiness":
                    boot_gb = clean_value(vm.get("Boot Disk GB"))
                    reasons = clean_value(vm.get("Readiness Reasons"))
                    current_value = (
                        f"Boot Disk GB: {boot_gb}; Reasons: {reasons}"
                    )
                    constraint = (
                        f"IBM Cloud custom image boot disk must be <= "
                        f"{IMAGE_MAX_GB} GB."
                    )
                    suggested_action = (
                        "Reduce or split the boot image before import, choose a "
                        "different migration method, or exclude this VM until "
                        "image remediation is complete."
                    )
                elif column == "Memory Readiness":
                    current_value = (
                        "Swapped MiB: "
                        f"{clean_value(vm.get('Swapped Memory MiB'), 0)}; "
                        "Ballooned MiB: "
                        f"{clean_value(vm.get('Ballooned Memory MiB'), 0)}; "
                        "Memory Limit MiB: "
                        f"{clean_value(vm.get('Memory Limit MiB'), 0)}"
                    )
                    constraint = (
                        "Resolve severe memory pressure or memory limits before "
                        "right-sizing into the Terraform package."
                    )
                findings.append(PreflightFinding(
                    "blocker",
                    "readiness",
                    _vm_name(vm),
                    f"{column} is Blocked.",
                    "Resolve blocker findings or exclude this VM from the package.",
                    f"Readiness tab > {column}",
                    suggested_action,
                    recommended_option="Exclude VM for this package if remediation cannot be completed now.",
                    quick_fix_type="exclude_vm",
                    field="Exclude?",
                    current_value=current_value,
                    constraint=constraint,
                ))
    return findings


def _mapping_findings(vms, network_names, enable_security_groups):
    findings = []
    valid_outputs = {
        f"module.networking.{safe}_id" for _, safe in network_names
    }
    valid_security_groups = {
        f"module.networking.{safe}_sg_id" for _, safe in network_names
    }
    valid_networks = {raw for raw, _ in network_names}
    valid_networks.update({safe for _, safe in network_names})

    for vm in vms:
        connected = _connected_nics(vm)
        if not connected:
            findings.append(PreflightFinding(
                "blocker",
                "network_mapping",
                _vm_name(vm),
                "VM has no connected NICs available for Terraform rendering.",
                "Connect at least one NIC in source data or exclude the VM.",
                "Networks tab",
                "Correct source NIC data, connect at least one NIC, or exclude this VM.",
                recommended_option="Exclude VM if the source NIC inventory cannot be corrected before packaging.",
                quick_fix_type="exclude_vm",
                field="Exclude?",
            ))
        for nic in connected:
            source_network = clean_value(nic.get("network"), "unknown-net")
            safe = _safe_resource_name(source_network)
            if source_network not in valid_networks and safe not in valid_networks:
                findings.append(PreflightFinding(
                    "blocker",
                    "network_mapping",
                    _vm_name(vm),
                    f"NIC network '{source_network}' has no generated subnet.",
                    "Add or correct the source network mapping before packaging.",
                    "Networks tab",
                    "Map the NIC to a discovered/generated network or correct the source network inventory.",
                    current_value=source_network,
                    constraint="NIC network must match a generated subnet.",
                ))

        subnet = clean_value(vm.get("Subnet"))
        if subnet and subnet not in valid_outputs:
            findings.append(PreflightFinding(
                "warning",
                "network_mapping",
                _vm_name(vm),
                f"VM subnet mapping '{subnet}' does not match generated outputs.",
                "Review VM Review subnet mapping before applying Terraform.",
                "VM Review tab > Subnet",
                "Update the subnet mapping to a generated networking module output.",
                current_value=subnet,
                constraint="Expected module.networking.<network>_id output.",
            ))
        if not subnet:
            findings.append(PreflightFinding(
                "warning",
                "network_mapping",
                _vm_name(vm),
                "VM subnet mapping is blank.",
                "Review target subnet mapping before applying Terraform.",
                "VM Review tab > Subnet",
                "Select or enter the generated subnet output for this VM.",
                constraint="Expected module.networking.<network>_id output.",
            ))

        security_group = clean_value(vm.get("Security Group"))
        if enable_security_groups:
            if security_group and security_group not in valid_security_groups:
                findings.append(PreflightFinding(
                    "warning",
                    "network_mapping",
                    _vm_name(vm),
                    (
                        f"Security group mapping '{security_group}' does not "
                        "match generated outputs."
                    ),
                    "Review VM Review security group mapping before applying Terraform.",
                    "VM Review tab > Security Group",
                    "Update the security group mapping to a generated networking module output.",
                    current_value=security_group,
                    constraint="Expected module.networking.<network>_sg_id output.",
                ))
            if not security_group:
                findings.append(PreflightFinding(
                    "warning",
                    "network_mapping",
                    _vm_name(vm),
                    "Security group mapping is blank.",
                    "Review target security group mapping before applying Terraform.",
                    "VM Review tab > Security Group",
                    "Select or enter the generated security group output for this VM.",
                    constraint="Expected module.networking.<network>_sg_id output.",
                ))
    return findings


def _resource_name_findings(vms, networks):
    findings = []
    vm_names = [_safe_resource_name(_vm_name(vm)) for vm in vms]
    for safe, count in Counter(vm_names).items():
        if count > 1:
            findings.append(PreflightFinding(
                "blocker",
                "terraform_names",
                safe,
                f"Multiple VMs sanitize to Terraform resource name '{safe}'.",
                "Rename or exclude duplicate VMs before package generation.",
                "VM Review tab",
                "Rename one duplicate VM in source data or exclude one of the duplicated VMs.",
                recommended_option="Exclude one duplicate VM if the source inventory cannot be corrected now.",
                constraint="Terraform resource names must be unique after sanitization.",
            ))

    network_pairs = _network_resource_names(networks)
    for safe, count in Counter(safe for _, safe in network_pairs).items():
        if count > 1:
            findings.append(PreflightFinding(
                "blocker",
                "terraform_names",
                safe,
                f"Multiple networks sanitize to Terraform resource name '{safe}'.",
                "Rename or adjust duplicated network labels before packaging.",
                "Networks tab",
                "Correct duplicated network labels in the source data before packaging.",
                constraint="Terraform resource names must be unique after sanitization.",
            ))
    return findings


def _profile_storage_findings(vms, target_region, catalog_profiles):
    findings = []
    supported_profiles = {
        clean_value(profile.get("name"))
        for profile in catalog_profiles or []
        if clean_value(profile.get("name"))
    }
    supported_families = PROFILE_REGION_SUPPORT.get(target_region)
    for vm in vms:
        profile = _effective_profile(vm)
        if not profile:
            findings.append(PreflightFinding(
                "blocker",
                "profile",
                _vm_name(vm),
                "Effective IBM profile is blank.",
                "Select a supported target profile before packaging.",
                "VM Review tab > Override Profile",
                "Choose a supported IBM profile for this VM.",
                tuple(sorted(supported_profiles)),
                next(iter(sorted(supported_profiles)), ""),
                "profile",
                "Override Profile",
                profile,
                "Effective profile cannot be blank.",
            ))
        elif supported_profiles and profile not in supported_profiles:
            findings.append(PreflightFinding(
                "warning",
                "profile",
                _vm_name(vm),
                f"Profile '{profile}' is not present in the active catalog.",
                "Validate profile availability in the selected region and zone.",
                "VM Review tab > Override Profile",
                "Choose a profile from the active catalog, or validate this override outside the app.",
                tuple(sorted(supported_profiles)),
                next(iter(sorted(supported_profiles)), ""),
                "profile" if supported_profiles else "",
                "Override Profile",
                profile,
                "Profile should exist in the active catalog when catalog data is available.",
            ))
        if supported_families:
            family = profile.split("-")[0] if profile else ""
            if family and family not in supported_families:
                findings.append(PreflightFinding(
                    "warning",
                    "profile_region",
                    _vm_name(vm),
                    (
                        f"Profile family '{family}' is not in the local support "
                        f"map for region '{target_region}'."
                    ),
                    "Confirm profile support with IBM Cloud before applying Terraform.",
                    "VM Review tab > Override Profile",
                    "Choose a profile family known for this region or confirm support with IBM Cloud.",
                    constraint=f"Known local families for {target_region}: {', '.join(sorted(supported_families))}.",
                    current_value=profile,
                ))
        elif profile:
            findings.append(PreflightFinding(
                "warning",
                "profile_region",
                _vm_name(vm),
                f"No local profile support map exists for region '{target_region}'.",
                "Confirm profile support with IBM Cloud before applying Terraform.",
                "VM Review tab > Override Profile",
                "Confirm target profile availability for the selected region and zone.",
                current_value=profile,
            ))

        tier = _effective_storage_tier(vm)
        if tier not in STORAGE_TIERS:
            findings.append(PreflightFinding(
                "blocker",
                "storage",
                _vm_name(vm),
                f"Storage tier '{tier}' is unsupported.",
                "Select one of: 3iops-tier, 5iops-tier, 10iops-tier.",
                "VM Review tab > Override Storage Tier",
                "Choose a supported IBM Cloud block storage tier.",
                tuple(STORAGE_TIERS),
                clean_value(vm.get("Storage Tier"), STORAGE_TIERS[0])
                if clean_value(vm.get("Storage Tier")) in STORAGE_TIERS
                else STORAGE_TIERS[0],
                "storage_tier",
                "Override Storage Tier",
                tier,
                "Supported values: 3iops-tier, 5iops-tier, 10iops-tier.",
            ))
    return findings


def run_package_preflight(
    final_vms,
    networks,
    target_region,
    custom_cidrs=None,
    enable_security_groups=True,
    catalog_profiles=None,
):
    vms = _normalize_vms(final_vms)
    networks = list(networks or [])
    custom_cidrs = custom_cidrs or {}
    findings = []

    if not vms:
        findings.append(PreflightFinding(
            "blocker",
            "scope",
            "package",
            "No in-scope VMs are selected for package generation.",
            "Clear at least one VM exclusion before building the Terraform package.",
            "VM Review tab > Exclude?",
            "Include at least one VM in the Terraform package.",
            quick_fix_type="include_vm",
            field="Exclude?",
            constraint="At least one VM must be in scope.",
        ))
        return findings

    network_names = _network_resource_names(networks)
    findings.extend(_readiness_findings(vms))
    findings.extend(_image_placeholder_findings(vms))
    findings.extend(_find_cidr_issues(networks, custom_cidrs))
    findings.extend(_resource_name_findings(vms, networks))
    findings.extend(_mapping_findings(vms, network_names, enable_security_groups))
    findings.extend(_profile_storage_findings(vms, target_region, catalog_profiles))
    return findings


def has_blockers(findings):
    return any(finding.severity == "blocker" for finding in findings)


def summarize_preflight(findings):
    counts = Counter(finding.severity for finding in findings)
    return {
        "blockers": counts.get("blocker", 0),
        "warnings": counts.get("warning", 0),
        "info": counts.get("info", 0),
        "total": len(findings),
    }


def generate_preflight_report_csv(findings):
    output = io.StringIO()
    fieldnames = [
        "Severity", "Category", "Subject", "Message", "Remediation",
        "Fix Location", "Suggested Action", "Valid Options",
        "Recommended Option", "Quick Fix Type", "Field", "Current Value",
        "Constraint",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for finding in findings:
        writer.writerow(finding.to_record())
    return output.getvalue()


def generate_preflight_report_json(findings):
    return json.dumps({
        "summary": summarize_preflight(findings),
        "findings": [finding.to_record() for finding in findings],
    }, indent=2, sort_keys=True)
