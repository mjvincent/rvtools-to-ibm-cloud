🧠 RVTools to IBM Cloud VPC: Right-Sizing & Resilience Logic
1. The "Why" Behind the Logic

Standard migration tools often look only at Allocation (how much RAM/CPU is assigned). This tool focuses on Utilization and Contention (how the VM actually performs). Our goal is to ensure Day 1 stability in IBM Cloud VPC by identifying "stressed" workloads that cannot afford to be right-sized.
2. Performance Safety Overrides: Understanding Contention

Before the tool suggests a smaller (cheaper) profile, it checks the source VM for signs of resource contention. We specifically track two "red flag" metrics: CPU Ready and CPU Co-Stop.
A. CPU Ready (%RDY) — "The Waiting Room"

    Definition: CPU Ready measures the time a Virtual Machine is ready to run, but is forced to wait because the physical CPU resources are busy serving other workloads.

    The Threshold: > 5.0%.

    The Logic: If a VM spends more than 5% of its time waiting in the "queue" on-premises, it is already resource-constrained. Right-sizing this VM during migration would likely lead to an immediate performance outage in the cloud.

B. CPU Co-Stop (%CSTP) — "The Sync Delay"

    Definition: This metric applies specifically to VMs with multiple virtual CPUs (vCPUs). It measures the time the vCPUs spend waiting to be synchronized so they can execute instructions at the same time on the physical cores.

    The Threshold: > 3.0%.

    The Logic: High Co-Stop indicates that a VM is "tripping over itself" because it has too many vCPUs for the underlying hardware to coordinate efficiently. This is a sign of architectural inefficiency that must be matched exactly (Safety Match) to ensure the workload doesn't degrade further during the transition to VPC.

3. Decision Pillar 2: The N+1 Resilience Math (Availability Parity)

While IBM handles physical hardware failover in VPC, this tool calculates Logical N+1 to ensure the target architecture matches the client's existing Service Level Agreements (SLAs).
The Calculation

We account for a "Worst Case Scenario" (the loss of the largest logical failure point):

    Total Cluster Capacity (MHz).

    Minus the capacity of the Largest Host in the source cluster.

    Compare the remaining capacity against the Current Total Demand.

Why this matters: For Dedicated Hosts, this ensures that if one host is down for maintenance, the remaining hosts have the headroom to support the evacuated VSIs.
4. Decision Pillar 3: Zombie VM Detection

To optimize cloud spend, the engine identifies "Ghost" workloads consuming resources without providing value.

    Criteria: Power State: Powered On | CPU Utilization: < 5% | Total Demand: < 100 MHz.

    The Action: These VMs are flagged for decommissioning, preventing unnecessary migration costs.

5. Decision Pillar 4: Storage Performance & IOPS Tiering

The engine utilizes a "Keyword + Performance" hybrid logic to assign the correct storage profile, ensuring enterprise-grade disk throughput for critical applications.
A. Intent-Based Keyword Triggers

Detection of these keywords in the VM Name or Environment automatically triggers a 10 IOPS/GB (Production Tier) default:

    Environment Tags: prod, production, crit.

    Workload Indicators: sql, db, oracle, sap, hana.

B. Performance-Based Triggers

    Disk Latency: If source telemetry shows sustained disk latency > 15ms, the engine upgrades the volume to 10 IOPS/GB regardless of the naming convention.

    Contention Alignment: Any VM flagged for a Safety Match (due to high CPU Ready or Co-Stop) defaults to 10 IOPS/GB to ensure the entire infrastructure stack has maximum performance headroom.

Michael Jones | Senior Cloud Architect | Master Certified Technical Specialist
