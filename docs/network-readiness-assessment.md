# Network Readiness Assessment

## Purpose
The network readiness assessment helps migration teams validate source NIC, switch, port group, VLAN/segment, and port evidence before moving VMware workloads to IBM Cloud Virtual Servers for VPC.

The assessment is advisory. It does not change generated Terraform resources, block ZIP generation, suppress network interfaces, or alter subnet and security group references.

## Status Values
### `Ready`
Connected NICs have usable source network metadata. When optional network-detail tabs are present, the NICs also have matched switch or port evidence with no detected blockers.

### `Review`
The VM has source network findings that should be validated before migration waves are finalized. Examples include unknown networks, disconnected NICs retained for review, missing switch/port backing, ambiguous duplicate matches, or missing VLAN/segment evidence.

### `Blocked`
The VM has explicit source-side network evidence that should be remediated before migration. Examples include a connected NIC backed by a blocked, disabled, down, error, or invalid source port, or a switch backing that reports no available ports.

## RVTools Inputs
* `vNetwork`: Primary NIC inventory, source network, IP, MAC, adapter, switch, and connection state.
* `vPort`: Standard switch port and port group context.
* `dvPort`: Distributed switch port and distributed port group context.
* `vSwitch`: Standard switch backing, VLAN, MTU, and port-capacity context.
* `dvSwitch`: Distributed switch backing, VLAN/segment, MTU, and port-capacity context.
* `vInfo`: Fallback network metadata when detailed NIC rows are unavailable.

## Dashboard Fields
* `Network Readiness`: `Ready`, `Review`, or `Blocked`.
* `Network Readiness Reasons`: Human-readable explanation of network findings.
* `Network Details`: Per-NIC metadata preserved for the Network Planning view and handoff package.

## Handoff Files
* `migration-manifest.json` includes a `network_readiness` object per VM and enriched source NIC records when switch/port evidence is available.
* `vm-mapping.csv` includes VM-level network readiness summary columns.
* `nic-mapping.csv` includes switch type, port group, VLAN/segment, port key, port status, backing source tab, match confidence, and network readiness columns.
* `assessment-quality.json` and `assessment-quality.csv` report optional network-detail tab coverage.

## Limitations
RVTools network data is inventory metadata. It cannot validate IBM Cloud subnet design, prove IP availability, inspect firewall policy, confirm routing, or guarantee application connectivity after cutover.

`Ready` means no source network findings were detected from the available tabs. It does not guarantee that the target VPC, security groups, DNS, load balancers, or hybrid connectivity are production-ready.
