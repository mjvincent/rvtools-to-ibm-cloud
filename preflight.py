import csv
import ipaddress
import io
import json
from collections import Counter
from dataclasses import dataclass

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

    def to_record(self):
        return {
            "Severity": self.severity,
            "Category": self.category,
            "Subject": self.subject,
            "Message": self.message,
            "Remediation": self.remediation,
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
                findings.append(PreflightFinding(
                    "blocker",
                    "readiness",
                    _vm_name(vm),
                    f"{column} is Blocked.",
                    "Resolve blocker findings or exclude this VM from the package.",
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
                ))

        subnet = clean_value(vm.get("Subnet"))
        if subnet and subnet not in valid_outputs:
            findings.append(PreflightFinding(
                "warning",
                "network_mapping",
                _vm_name(vm),
                f"VM subnet mapping '{subnet}' does not match generated outputs.",
                "Review VM Review subnet mapping before applying Terraform.",
            ))
        if not subnet:
            findings.append(PreflightFinding(
                "warning",
                "network_mapping",
                _vm_name(vm),
                "VM subnet mapping is blank.",
                "Review target subnet mapping before applying Terraform.",
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
                ))
            if not security_group:
                findings.append(PreflightFinding(
                    "warning",
                    "network_mapping",
                    _vm_name(vm),
                    "Security group mapping is blank.",
                    "Review target security group mapping before applying Terraform.",
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
            ))
        elif supported_profiles and profile not in supported_profiles:
            findings.append(PreflightFinding(
                "warning",
                "profile",
                _vm_name(vm),
                f"Profile '{profile}' is not present in the active catalog.",
                "Validate profile availability in the selected region and zone.",
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
                ))
        elif profile:
            findings.append(PreflightFinding(
                "warning",
                "profile_region",
                _vm_name(vm),
                f"No local profile support map exists for region '{target_region}'.",
                "Confirm profile support with IBM Cloud before applying Terraform.",
            ))

        tier = _effective_storage_tier(vm)
        if tier not in STORAGE_TIERS:
            findings.append(PreflightFinding(
                "blocker",
                "storage",
                _vm_name(vm),
                f"Storage tier '{tier}' is unsupported.",
                "Select one of: 3iops-tier, 5iops-tier, 10iops-tier.",
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
    fieldnames = ["Severity", "Category", "Subject", "Message", "Remediation"]
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
