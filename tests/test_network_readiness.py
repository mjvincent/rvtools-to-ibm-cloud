import io

import pandas as pd

from logic_engine import assess_network_readiness, render_terraform_templates
from rvtools_parser import parse_rvtools_workbook


def _sheet(rows):
    return pd.DataFrame(rows)


def _workbook(extra_sheets=None, connected=True):
    sheets = {
        "vInfo": _sheet([{
            "VM": "app-01",
            "Powerstate": "poweredOn",
            "CPUs": 2,
            "Memory": 8192,
            "Host": "host-01",
            "CPU Usage %": 25,
            "Network #1": "app-net",
            "Primary IP Address": "10.0.1.10",
            "Disks": 1,
            "Provisioned MiB": 81920,
            "OS according to the VMware Tools": "Ubuntu Linux (64-bit)",
            "Firmware": "efi",
        }]),
        "vDisk": _sheet([{
            "VM": "app-01",
            "Disk": "Hard disk 1",
            "Disk Key": "2000",
            "Capacity MiB": 81920,
        }]),
        "vCPU": _sheet([{
            "VM": "app-01",
            "CPU ready %": 0,
            "CPU co-stop": 0,
            "Overall": 400,
            "Limit": 0,
        }]),
        "vMemory": _sheet([{
            "VM": "app-01",
            "Size MiB": 8192,
            "Active": 4096,
            "Consumed": 6144,
            "Ballooned": 0,
            "Swapped": 0,
            "Reservation": 0,
            "Limit": -1,
            "Hot Add": "False",
        }]),
        "vHost": _sheet([{
            "Host": "host-01",
            "Speed": 2400,
            "# Cores": 16,
        }]),
        "vCluster": _sheet([{
            "Cluster": "cluster-01",
            "TotalCpu": 38400,
        }]),
        "vNetwork": _sheet([{
            "VM": "app-01",
            "NIC label": "Network adapter 1",
            "Network": "app-net",
            "Switch": "vSwitch0",
            "Connected": connected,
            "Starts Connected": connected,
            "Mac Address": "00:50:56:aa:bb:01",
            "Adapter": "VMXNET3",
        }]),
    }
    sheets.update(extra_sheets or {})

    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output


def _parse(extra_sheets=None, connected=True):
    return parse_rvtools_workbook(
        _workbook(extra_sheets, connected=connected),
        "us-south",
        70,
        True,
    )


def test_standard_switch_context_enriches_nic_and_ready_status():
    parsed = _parse({
        "vSwitch": _sheet([{
            "Switch": "vSwitch0",
            "Ports": 128,
            "Ports Used": 64,
            "VLAN ID": "101",
        }]),
        "vPort": _sheet([{
            "VM": "app-01",
            "NIC label": "Network adapter 1",
            "Network": "app-net",
            "Switch": "vSwitch0",
            "Port Key": "12",
            "VLAN ID": "101",
            "Status": "up",
        }]),
    })
    record = parsed.processed_vms[0].to_record()
    nic = record["Network Details"][0]

    assert record["Network Readiness"] == "Ready"
    assert nic["switch_type"] == "standard"
    assert nic["backing_source_tab"] == "vPort"
    assert nic["match_confidence"] == "matched"
    assert nic["vlan"] == "101"


def test_distributed_switch_context_enriches_nic_and_ready_status():
    parsed = _parse({
        "dvSwitch": _sheet([{
            "dvSwitch": "dvs-prod",
            "Ports": 256,
            "Ports Used": 32,
            "VLAN ID": "220",
        }]),
        "dvPort": _sheet([{
            "VM": "app-01",
            "NIC label": "Network adapter 1",
            "Network": "app-net",
            "dvSwitch": "dvs-prod",
            "Port Key": "77",
            "VLAN ID": "220",
            "Status": "up",
        }]),
    })
    record = parsed.processed_vms[0].to_record()
    nic = record["Network Details"][0]

    assert record["Network Readiness"] == "Ready"
    assert nic["switch_type"] == "distributed"
    assert nic["backing_source_tab"] == "dvPort"
    assert nic["port_key"] == "77"


def test_missing_optional_network_detail_tabs_preserve_ready_behavior():
    parsed = _parse()
    record = parsed.processed_vms[0].to_record()

    assert record["Network Readiness"] == "Ready"
    assert record["Network Details"][0]["match_confidence"] == ""


def test_ambiguous_port_matches_are_review_not_guessed():
    parsed = _parse({
        "vPort": _sheet([
            {
                "VM": "app-01",
                "NIC label": "Network adapter 1",
                "Network": "app-net",
                "Switch": "vSwitch0",
                "Port Key": "12",
                "VLAN ID": "101",
            },
            {
                "VM": "app-01",
                "NIC label": "Network adapter 1",
                "Network": "app-net",
                "Switch": "vSwitch0",
                "Port Key": "13",
                "VLAN ID": "101",
            },
        ]),
    })
    record = parsed.processed_vms[0].to_record()

    assert record["Network Readiness"] == "Review"
    assert record["Network Details"][0]["match_confidence"] == "ambiguous"
    assert "matched multiple switch/port rows" in record["Network Readiness Reasons"]


def test_blocked_port_status_is_advisory_and_does_not_change_terraform():
    readiness = assess_network_readiness([{
        "label": "Network adapter 1",
        "network": "app-net",
        "connected": True,
        "planned": True,
        "backing_source_tab": "vPort",
        "match_confidence": "matched",
        "switch_type": "standard",
        "vlan": "101",
        "port_status": "blocked",
    }], network_detail_available=True)
    files = render_terraform_templates(
        [{
            "VM Name": "app-01",
            "Network": "app-net",
            "IBM Profile": "bx2-2x8",
            "Network Details": [{
                "label": "Network adapter 1",
                "network": "app-net",
                "connected": True,
            }],
        }],
        [{"name": "app-net", "vlan": "", "cidr": "10.0.1.0/24"}],
        "us-south",
        "us-south-1",
    )

    assert readiness["status"] == "Blocked"
    assert 'var.subnet_ids["app_net"]' in files[0]
