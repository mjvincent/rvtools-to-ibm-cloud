# RVTools to IBM Cloud VPC: Performance-Aware Migration

## Overview
This tool automates the transformation of VMware RVTools exports into production-ready IBM Cloud VPC Terraform code. By correlating telemetry across multiple data silos, the engine ensures destination profiles are right-sized for actual performance demand, not just allocated specifications.

## Core Features

### Performance-Driven Right-Sizing
Unlike standard calculators, this tool detects **CPU Ready %** and **Co-Stop** spikes. If a workload is resource-constrained on-premises, the engine implements a "Safety Match" override, maintaining the original specifications to prevent Day 1 performance degradation in the cloud.

### Infrastructure Resilience (N+1)
The tool calculates cluster-wide headroom by identifying the largest failure point (Host Speed) and comparing total demand against the remaining effective capacity. This ensures that the migration proposal maintains enterprise-grade uptime.

### Zombie VM Identification
Workloads that are powered on but show <5% utilization and <100 MHz overall demand are flagged. This allows migration teams to avoid migrating "ghost" assets, significantly reducing waste in the target environment.

## Technical Stack
* **Python**: Data processing and logic engine.
* **Pandas**: Cross-tab data correlation and transformation.
* **Streamlit**: Interactive assessment dashboard.
* **Terraform**: Automated HCL generation for IBM Cloud.

## Data Schema Requirements
To provide high-fidelity results, the following RVTools tabs are required:
* `vInfo`: Baseline configuration.
* `vCPU`: Performance telemetry (Overall MHz, Limit).
* `vHost`: Physical host specifications.
* `vCluster`: Aggregate capacity.
* `vDisk`: Storage inventory.

## Usage
1. Export a full RVTools workbook.
2. Upload the `.xlsx` file to the dashboard.
3. Review the N+1 Headroom and Density ratios.
4. Export the Business Case (CSV) or download the complete Terraform Bundle (ZIP).
