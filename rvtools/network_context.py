from .base import (
    as_float,
    clean_cell,
    first_present,
    normalize_match_key,
    row_matches_any,
)


def build_switch_contexts(df, switch_type, source_tab):
    contexts = {}
    if df.empty:
        return contexts

    for row in df.to_dict("records"):
        switch_name = first_present(row, [
            "Switch", "vSwitch", "dvSwitch", "Dvswitch", "DVSwitch",
            "Name", "Switch Name", "Distributed Switch"
        ])
        if not switch_name:
            continue
        ports = as_float(first_present(row, [
            "Ports", "Num Ports", "# Ports", "Number of Ports", "Port Count"
        ]), 0)
        used_ports = as_float(first_present(row, [
            "Ports Used", "Used Ports", "Port Used", "Used"
        ]), 0)
        available_ports = ""
        if ports:
            available_ports = max(0, ports - used_ports)
        contexts.setdefault(normalize_match_key(switch_name), {
            "switch_type": switch_type,
            "switch_name": switch_name,
            "source_tab": source_tab,
            "vlan": first_present(row, [
                "VLAN", "VLAN ID", "Vlan", "Vlan ID", "Segment", "Network"
            ]),
            "mtu": first_present(row, ["MTU", "Mtu"]),
            "port_count": ports,
            "used_ports": used_ports,
            "available_ports": available_ports,
        })
    return contexts


def build_port_contexts(df, source_tab, switch_lookup):
    contexts = []
    if df.empty:
        return contexts

    for row in df.to_dict("records"):
        switch_name = first_present(row, [
            "Switch", "vSwitch", "dvSwitch", "Dvswitch", "DVSwitch",
            "Switch Name", "Distributed Switch"
        ])
        switch_context = switch_lookup.get(normalize_match_key(switch_name), {})
        port_group = first_present(row, [
            "Port Group", "Portgroup", "Portgroup Name", "Network",
            "Network Name", "DVPortgroup", "DV Portgroup", "dvPortgroup",
            "Port Group Name"
        ])
        context = {
            "source_tab": source_tab,
            "vm": first_present(row, ["VM", "VM Name", "VM UUID", "VM ID"]),
            "nic_label": first_present(row, [
                "NIC label", "NIC Label", "Network Adapter", "Adapter"
            ]),
            "mac_address": first_present(row, [
                "Mac Address", "MAC Address", "MAC", "Mac"
            ]),
            "network": port_group,
            "port_group": port_group,
            "switch": switch_name,
            "switch_type": switch_context.get(
                "switch_type",
                "distributed" if source_tab == "dvPort" else "standard"
            ),
            "vlan": first_present(row, [
                "VLAN", "VLAN ID", "Vlan", "Vlan ID", "Segment"
            ], switch_context.get("vlan", "")),
            "port_key": first_present(row, [
                "Port", "Port Key", "Port ID", "Key", "Port Number"
            ]),
            "port_status": first_present(row, [
                "Status", "Port Status", "Link Status", "State"
            ]),
            "mtu": switch_context.get("mtu", ""),
            "available_ports": switch_context.get("available_ports", ""),
        }
        if context["vm"] or context["network"] or context["switch"]:
            contexts.append(context)
    return contexts


def enrich_nic_with_network_context(nic, vm_key, vm_name, port_contexts):
    candidates = []
    for context in port_contexts:
        score = 0
        if (
            row_matches_any(context, ["vm"], vm_key) or
            row_matches_any(context, ["vm"], vm_name)
        ):
            score += 4
        if row_matches_any(context, ["nic_label"], nic.get("label")):
            score += 3
        if row_matches_any(context, ["mac_address"], nic.get("mac_address")):
            score += 3
        if row_matches_any(context, ["network", "port_group"], nic.get("network")):
            score += 2
        if row_matches_any(context, ["switch"], nic.get("switch")):
            score += 1
        if score:
            candidates.append((score, context))

    if not candidates:
        nic.update({
            "switch_type": "",
            "port_group": nic.get("network", ""),
            "vlan": "",
            "port_key": "",
            "port_status": "",
            "backing_source_tab": "",
            "match_confidence": "unmatched" if port_contexts else "",
            "available_ports": "",
        })
        return nic

    max_score = max(score for score, _ in candidates)
    best = [context for score, context in candidates if score == max_score]
    context = best[0]
    confidence = "matched" if len(best) == 1 else "ambiguous"

    nic.update({
        "switch_type": context.get("switch_type", ""),
        "port_group": context.get("port_group") or nic.get("network", ""),
        "vlan": context.get("vlan", ""),
        "port_key": context.get("port_key", ""),
        "port_status": context.get("port_status", ""),
        "backing_source_tab": context.get("source_tab", ""),
        "match_confidence": confidence,
        "available_ports": context.get("available_ports", ""),
    })
    if context.get("switch") and not clean_cell(nic.get("switch")):
        nic["switch"] = context.get("switch")
    return nic

