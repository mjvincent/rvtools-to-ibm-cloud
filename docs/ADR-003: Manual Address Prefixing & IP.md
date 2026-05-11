# ADR-003: Manual Address Prefixing & IP Parity

## Status
**Accepted / Implemented** (May 2026)

## Context
Standard VPC deployments utilize "Default Address Prefixes," which often result in IP ranges that overlap with existing on-premises sites or fail to match established customer IPAM standards. For enterprise migrations, maintaining IP persistence is often a prerequisite for application connectivity and security governance.

## Decision
The engine now exposes an address prefix strategy option in the Streamlit UI. The default behavior remains `address_preference = "manual"` to preserve source CIDR mappings, but users may optionally select an `auto` strategy for provider-managed prefix allocation.

The tool utilizes a **Network Schema Discovery** process to extract IPv4 metadata from the `vNetwork` and `vNIC` tabs, programmatically generating `ibm_is_vpc_address_prefix` resources that mirror the source environment when manual mode is selected.

## Consequences
* **Positive**: Ensures 1:1 network parity between VMware Port Groups and IBM VPC Subnets; simplifies hybrid connectivity (Direct Link/Transit Gateway) by preventing CIDR overlaps.
* **Positive**: Supports primary and secondary NIC mapping by discovering all source networks represented in `vNetwork`.
* **Positive**: Automated discovery removes the human error associated with manual IP entry during the Landing Zone build.
* **Negative**: High dependency on the quality of the RVTools `vNetwork` data; if IP metadata is missing, the tool must revert to a deterministic fallback schema (10.x.x.x) to ensure the Terraform remains functional.
