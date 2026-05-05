# IBM Cloud VPC Infrastructure Mapping: Performance and Resilience Logic

## 1. Design Methodology
The transition from on-premises VMware environments to IBM Cloud VPC requires an assessment model that prioritizes workload stability over simple resource allocation. This mapping engine utilizes a multi-factor analysis of utilization, contention, and networking metadata to ensure that destination profiles maintain performance parity.

## 2. Performance-Based Safety Overrides
The engine evaluates source telemetry for indicators of resource contention. If a workload exhibits performance constraints on-premises, a "Safety Match" policy is enforced, preventing aggressive right-sizing and maintaining the original resource allocation to ensure stability post-migration.

### A. CPU Ready (%RDY): Contention Thresholds
* **Definition**: CPU Ready represents the latency incurred when a virtual machine is ready to execute instructions but must wait for available physical CPU cycles.
* **Threshold**: > 5.0%.
* **Logic**: Sustained CPU Ready metrics above 5% indicate that the workload is already resource-starved. Right-sizing these instances during migration would likely induce performance degradation. Consequently, these workloads are matched to the nearest IBM Cloud VPC profile that meets or exceeds original allocations.

### B. CPU Co-Stop (%CSTP): Multi-Core Synchronization
* **Definition**: For multi-vCPU instances, Co-Stop measures the synchronization delay between virtual processors as they wait for simultaneous access to physical cores.
* **Threshold**: > 3.0%.
* **Logic**: Elevated Co-Stop values indicate architectural inefficiencies relative to the underlying host capacity. To mitigate risk, these workloads are flagged for exact resource matching, ensuring the transition to the VPC hypervisor does not exacerbate execution delays.

## 3. Network Schema Discovery and Address Preservation
To support complex migrations without requiring extensive IP re-addressing, the engine automates the discovery of on-premises networking schemas.
* **Subnet Mirroring**: By extracting IPv4 metadata from the `vNetwork` and `vNIC` worksheets, the tool identifies existing CIDR blocks.
* **Address Preference Configuration**: The engine programmatically sets VPC address preferences to `manual`. This enables the injection of specific customer address prefixes, allowing IBM Cloud Subnets to mirror the original on-premises IP architecture.

## 4. Availability and Resilience Modeling (N+1)
The logic engine calculates logical N+1 resilience to ensure the target IBM Cloud architecture aligns with enterprise availability requirements.
* **Resilience Calculation**: The model identifies the largest single point of failure (maximum host speed) and subtracts it from the aggregate cluster capacity.
* **Headroom Assessment**: Total current demand is compared against the remaining effective capacity. This ensures that the migration proposal accounts for sufficient headroom to sustain workload performance during host-level maintenance or failure events.

## 5. Storage Throughput and IOPS Tiering
Storage profiles are assigned using a hybrid logic model that accounts for both workload intent and observed performance requirements.
* **Intent-Based Assignment**: Detection of specific strings (e.g., SQL, DB, SAP, PROD) in metadata triggers a default assignment to the 10 IOPS/GB tier.
* **Utilization-Based Escalation**: Instances identified as high-utilization or those flagged for a Performance Safety Match are automatically escalated to higher-tier storage profiles to ensure maximum throughput headroom.

## 6. Underutilized Asset Identification
The engine audits the inventory to identify assets that may not require migration, thereby optimizing the destination footprint.
* **Identification Criteria**: Instances with a "Powered On" state but exhibiting <5% CPU utilization and <100 MHz overall demand are categorized as underutilized.
* **Recommendation**: These assets are flagged for review and potential decommissioning prior to migration to minimize unnecessary recurring costs.

---
**Author**: Michael Vincent Jones
**Role**: Technical Specialist, IBM Automation
