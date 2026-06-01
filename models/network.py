from dataclasses import dataclass

from .base import as_bool, clean_value, get_record_value


@dataclass
class NicMapping:
    label: str = ""
    adapter: str = ""
    network: str = "unknown-net"
    switch: str = ""
    connected: bool = True
    starts_connected: str = ""
    mac_address: str = ""
    type: str = ""
    ipv4: str = ""
    ipv6: str = ""
    planned: bool = True
    switch_type: str = ""
    port_group: str = ""
    vlan: str = ""
    port_key: str = ""
    port_status: str = ""
    backing_source_tab: str = ""
    match_confidence: str = ""
    available_ports: object = ""

    @classmethod
    def from_record(cls, record):
        return cls(
            label=clean_value(get_record_value(record, "label")),
            adapter=clean_value(get_record_value(record, "adapter")),
            network=clean_value(get_record_value(record, "network"), "unknown-net"),
            switch=clean_value(get_record_value(record, "switch")),
            connected=as_bool(get_record_value(record, "connected", True), True),
            starts_connected=clean_value(
                get_record_value(record, "starts_connected")
            ),
            mac_address=clean_value(get_record_value(record, "mac_address")),
            type=clean_value(get_record_value(record, "type")),
            ipv4=clean_value(get_record_value(record, "ipv4")),
            ipv6=clean_value(get_record_value(record, "ipv6")),
            planned=as_bool(get_record_value(record, "planned", True), True),
            switch_type=clean_value(get_record_value(record, "switch_type")),
            port_group=clean_value(get_record_value(record, "port_group")),
            vlan=clean_value(get_record_value(record, "vlan")),
            port_key=clean_value(get_record_value(record, "port_key")),
            port_status=clean_value(get_record_value(record, "port_status")),
            backing_source_tab=clean_value(
                get_record_value(record, "backing_source_tab")
            ),
            match_confidence=clean_value(
                get_record_value(record, "match_confidence")
            ),
            available_ports=clean_value(
                get_record_value(record, "available_ports")
            ),
        )

    def to_record(self):
        return self.__dict__.copy()
