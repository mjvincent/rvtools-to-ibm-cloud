from logic_engine import generate_nic_mapping_csv, render_terraform_templates


def sample_vm():
    return {
        "VM Name": "app-01",
        "Network": "app-net",
        "IBM Profile": "bx2-2x8",
        "Network Details": [
            {
                "label": "Network adapter 1",
                "network": "app-net",
                "connected": True,
                "ipv4": "10.0.1.10",
                "mac_address": "00:50:56:aa:bb:01",
                "switch_type": "standard",
                "port_group": "app-net",
                "vlan": "101",
                "port_key": "12",
                "backing_source_tab": "vPort",
                "match_confidence": "matched",
            },
            {
                "label": "Network adapter 2",
                "network": "db-net",
                "connected": True,
                "ipv4": "10.0.2.10",
                "mac_address": "00:50:56:aa:bb:02",
            },
            {
                "label": "Network adapter 3",
                "network": "backup-net",
                "connected": False,
                "ipv4": "",
                "mac_address": "00:50:56:aa:bb:03",
            },
        ],
    }


def test_secondary_connected_nic_generates_inline_interface():
    files = render_terraform_templates(
        [sample_vm()],
        [
            {"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"},
            {"name": "db-net", "vlan": "", "cidr": "10.0.2.0/24"},
            {"name": "backup-net", "vlan": "", "cidr": "10.0.3.0/24"},
        ],
        "us-south",
        "us-south-1",
    )
    vsi_main = files[0]

    assert "primary_network_interface" in vsi_main
    assert "network_interfaces" in vsi_main
    assert 'var.subnet_ids["app_net"]' in vsi_main
    assert 'var.subnet_ids["db_net"]' in vsi_main
    assert 'var.subnet_ids["backup_net"]' not in vsi_main


def test_nic_mapping_marks_disconnected_as_unplanned():
    csv_text = generate_nic_mapping_csv([sample_vm()])

    assert "primary" in csv_text
    assert "secondary" in csv_text
    assert "disconnected" in csv_text
    assert "backup-net" in csv_text


def test_nic_mapping_includes_switch_port_context_columns():
    csv_text = generate_nic_mapping_csv([sample_vm()])

    assert "Switch Type" in csv_text
    assert "Port Group" in csv_text
    assert "Backing Source Tab" in csv_text
    assert "matched" in csv_text
