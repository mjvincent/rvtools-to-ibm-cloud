"""Generate a sanitized RVTools-style workbook for first-run testing."""

from pathlib import Path

import pandas as pd


OUTPUT = Path("samples/rvtools-small-complete.xlsx")


def _write_sheet(writer, name, rows):
    pd.DataFrame(rows).to_excel(writer, sheet_name=name, index=False)


def build_sample_workbook(output_path=OUTPUT):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        _write_sheet(writer, "vInfo", [
            {
                "VM": "sample-web-01",
                "Powerstate": "poweredOn",
                "CPUs": 2,
                "Memory": 8192,
                "Host": "sample-host-01",
                "Cluster": "sample-cluster-a",
                "Datacenter": "sample-dc",
                "Disks": 2,
                "Provisioned MiB": 122880,
                "CPU Usage %": 35,
                "Network #1": "sample-app-net",
                "Primary IP Address": "10.10.1.10",
                "OS according to the VMware Tools": "Ubuntu Linux (64-bit)",
                "Firmware": "bios",
            },
            {
                "VM": "sample-db-01",
                "Powerstate": "poweredOn",
                "CPUs": 4,
                "Memory": 16384,
                "Host": "sample-host-02",
                "Cluster": "sample-cluster-a",
                "Datacenter": "sample-dc",
                "Disks": 2,
                "Provisioned MiB": 327680,
                "CPU Usage %": 62,
                "Network #1": "sample-db-net",
                "Primary IP Address": "10.10.2.20",
                "OS according to the VMware Tools": "Microsoft Windows Server 2022",
                "Firmware": "efi",
            },
            {
                "VM": "sample-archive-01",
                "Powerstate": "poweredOff",
                "CPUs": 2,
                "Memory": 4096,
                "Host": "sample-host-01",
                "Cluster": "sample-cluster-a",
                "Datacenter": "sample-dc",
                "Disks": 1,
                "Provisioned MiB": 81920,
                "CPU Usage %": 2,
                "Network #1": "sample-app-net",
                "Primary IP Address": "10.10.1.30",
                "OS according to the VMware Tools": "Ubuntu Linux (64-bit)",
                "Firmware": "bios",
            },
        ])
        _write_sheet(writer, "vDisk", [
            {"VM": "sample-web-01", "Disk": "Hard disk 1", "Disk Key": "2000", "Capacity MiB": 81920, "Unit #": 0},
            {"VM": "sample-web-01", "Disk": "Hard disk 2", "Disk Key": "2001", "Capacity MiB": 40960, "Unit #": 1},
            {"VM": "sample-db-01", "Disk": "Hard disk 1", "Disk Key": "2100", "Capacity MiB": 102400, "Unit #": 0},
            {"VM": "sample-db-01", "Disk": "Hard disk 2", "Disk Key": "2101", "Capacity MiB": 225280, "Unit #": 1},
            {"VM": "sample-archive-01", "Disk": "Hard disk 1", "Disk Key": "2200", "Capacity MiB": 81920, "Unit #": 0},
        ])
        _write_sheet(writer, "vPartition", [
            {"VM": "sample-web-01", "Disk Key": "2000", "Disk": "/", "Capacity MiB": 81920, "Consumed MiB": 40960, "Free MiB": 40960, "Free % ": 50},
            {"VM": "sample-web-01", "Disk Key": "2001", "Disk": "/var", "Capacity MiB": 40960, "Consumed MiB": 20480, "Free MiB": 20480, "Free % ": 50},
            {"VM": "sample-db-01", "Disk Key": "2100", "Disk": "C:\\", "Capacity MiB": 102400, "Consumed MiB": 71680, "Free MiB": 30720, "Free % ": 30},
            {"VM": "sample-db-01", "Disk Key": "2101", "Disk": "D:\\", "Capacity MiB": 225280, "Consumed MiB": 184320, "Free MiB": 40960, "Free % ": 18},
            {"VM": "sample-archive-01", "Disk Key": "2200", "Disk": "/", "Capacity MiB": 81920, "Consumed MiB": 10240, "Free MiB": 71680, "Free % ": 88},
        ])
        _write_sheet(writer, "vCPU", [
            {"VM": "sample-web-01", "Overall": 700, "CPU ready %": 1.2, "CPU co-stop": 0.1, "Limit": 0},
            {"VM": "sample-db-01", "Overall": 2200, "CPU ready %": 6.1, "CPU co-stop": 0.2, "Limit": 0},
            {"VM": "sample-archive-01", "Overall": 40, "CPU ready %": 0.1, "CPU co-stop": 0, "Limit": 0},
        ])
        _write_sheet(writer, "vMemory", [
            {"VM": "sample-web-01", "Size MiB": 8192, "Active": 4096, "Consumed": 6144, "Ballooned": 0, "Swapped": 0, "Reservation": 0, "Limit": -1, "Hot Add": "False"},
            {"VM": "sample-db-01", "Size MiB": 16384, "Active": 14336, "Consumed": 15360, "Ballooned": 0, "Swapped": 0, "Reservation": 0, "Limit": -1, "Hot Add": "True"},
            {"VM": "sample-archive-01", "Size MiB": 4096, "Active": 1024, "Consumed": 2048, "Ballooned": 0, "Swapped": 0, "Reservation": 0, "Limit": -1, "Hot Add": "False"},
        ])
        _write_sheet(writer, "vHost", [
            {"Host": "sample-host-01", "Speed": 2400, "# Cores": 16},
            {"Host": "sample-host-02", "Speed": 2600, "# Cores": 16},
        ])
        _write_sheet(writer, "vCluster", [
            {"Cluster": "sample-cluster-a", "TotalCpu": 76800},
        ])
        _write_sheet(writer, "vNetwork", [
            {"VM": "sample-web-01", "NIC label": "Network adapter 1", "Adapter": "Vmxnet3", "Network": "sample-app-net", "Connected": True, "Starts Connected": True, "Mac Address": "00:50:56:aa:00:01", "IPv4 Address": "10.10.1.10"},
            {"VM": "sample-db-01", "NIC label": "Network adapter 1", "Adapter": "Vmxnet3", "Network": "sample-db-net", "Connected": True, "Starts Connected": True, "Mac Address": "00:50:56:aa:00:02", "IPv4 Address": "10.10.2.20"},
            {"VM": "sample-db-01", "NIC label": "Network adapter 2", "Adapter": "Vmxnet3", "Network": "sample-backup-net", "Connected": True, "Starts Connected": True, "Mac Address": "00:50:56:aa:00:03", "IPv4 Address": "10.10.3.20"},
            {"VM": "sample-archive-01", "NIC label": "Network adapter 1", "Adapter": "Vmxnet3", "Network": "sample-app-net", "Connected": True, "Starts Connected": True, "Mac Address": "00:50:56:aa:00:04", "IPv4 Address": "10.10.1.30"},
        ])
        _write_sheet(writer, "vSnapshot", [
            {"VM": "sample-db-01", "Snapshot": "pre-maintenance", "Size MiB (total)": 512},
        ])
        _write_sheet(writer, "vTools", [
            {"VM": "sample-web-01", "Tools": "toolsOk", "Tools Version": "12345", "Upgradeable": "No", "App status": "appStatusOk", "Heartbeat status": "green", "Operation Ready": "True"},
            {"VM": "sample-db-01", "Tools": "toolsOld", "Tools Version": "10000", "Upgradeable": "Yes", "App status": "appStatusOk", "Heartbeat status": "green", "Operation Ready": "True"},
            {"VM": "sample-archive-01", "Tools": "toolsOk", "Tools Version": "12345", "Upgradeable": "No", "App status": "appStatusOk", "Heartbeat status": "gray", "Operation Ready": "False"},
        ])
        _write_sheet(writer, "vCD", [
            {"VM": "sample-web-01", "Device Node": "CD/DVD drive 1", "Device Type": "client device", "Connected": False, "Starts Connected": False},
        ])
        _write_sheet(writer, "vUSB", [
            {"VM": "sample-web-01", "Device Node": "USB controller 1", "Device Type": "controller", "Connected": False},
        ])
        _write_sheet(writer, "vHealth", [
            {"Name": "sample-db-01", "Message type": "Warning", "Message": "Synthetic sample warning for owner review"},
        ])
        _write_sheet(writer, "vSwitch", [
            {"Host": "sample-host-01", "Switch": "vSwitch0", "Port Group": "sample-app-net", "VLAN": 101, "Ports": 128, "Ports Available": 64},
            {"Host": "sample-host-02", "Switch": "vSwitch0", "Port Group": "sample-db-net", "VLAN": 102, "Ports": 128, "Ports Available": 32},
        ])
        _write_sheet(writer, "dvSwitch", [
            {"Switch": "dvSwitch-backup", "Port Group": "sample-backup-net", "VLAN": 103, "Ports": 128, "Ports Available": 48},
        ])
        _write_sheet(writer, "vPort", [
            {"VM": "sample-web-01", "Network": "sample-app-net", "Port Group": "sample-app-net", "Switch": "vSwitch0", "VLAN": 101, "Status": "up"},
            {"VM": "sample-archive-01", "Network": "sample-app-net", "Port Group": "sample-app-net", "Switch": "vSwitch0", "VLAN": 101, "Status": "up"},
        ])
        _write_sheet(writer, "dvPort", [
            {"VM": "sample-db-01", "Network": "sample-backup-net", "Port Group": "sample-backup-net", "Switch": "dvSwitch-backup", "VLAN": 103, "Status": "up"},
        ])


def main():
    build_sample_workbook(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
