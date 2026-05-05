# RVTools to IBM Cloud VPC: Automated Infrastructure Mapping

## Overview
This utility automates the conversion of VMware RVTools exports into modular IBM Cloud VPC Terraform configurations. By correlating performance telemetry and networking metadata across multiple data tabs, the engine generates infrastructure-as-code (IaC) that reflects actual utilization requirements rather than static allocations.

## Core Functional Logic

### Network Schema Discovery
The tool identifies on-premises network configurations by correlating data from the vNetwork and vInfo tabs.
* **IP Range Mapping**: Extracts IPv4 gateways and addresses to define VPC Address Prefixes.
* **Subnet Generation**: Automatically configures subnets using a manual address preference, ensuring original CIDR blocks are preserved in the target VPC environment.
* **Resource Linking**: Maps individual Virtual Server Instances (VSIs) to their respective subnets based on on-premises port group assignments.

### Performance-Aware Right-Sizing
The mapping engine evaluates compute requirements by analyzing specific performance metrics to mitigate the risk of post-migration performance degradation.
* **Contention Analysis**: Monitors CPU Ready % and Co-Stop telemetry. If a workload shows signs of resource contention on-premises, the tool implements a "Safety Match" policy, maintaining the original core count and memory allocation.
* **Utilization Thresholds**: Allows for the application of variable utilization factors (30% to 70%) to align suggested IBM VPC profiles with specific performance targets.

### Resource Efficiency Auditing
The application performs an automated audit of the inventory to identify underutilized assets.
* **Identification of Low-Utilization Assets**: Workloads exhibiting <5% CPU utilization and <100 MHz overall demand are flagged for review.
* **Capacity Headroom (N+1)**: Calculates available cluster capacity by identifying the largest host speed and evaluating remaining aggregate capacity against total VM demand.

## Technical Structure
The application architecture is divided into three functional layers:
1. **Data Processing**: Utilizes Pandas for cross-tabulation and normalization of RVTools telemetry.
2. **Logic Engine**: Executes profile matching and storage tiering (3, 5, or 10 IOPS) based on workload characteristics.
3. **Template Rendering**: Outputs HCL (HashiCorp Configuration Language) in a modular format including networking, storage, and VSI modules.

## Data Requirements
Successful execution requires a standard RVTools XLSX export containing the following worksheets:
* **vInfo**: Primary inventory, power states, and network assignments.
* **vNetwork**: Networking metadata and IPv4 addressing.
* **vCPU**: Detailed performance telemetry (MHz, Ready %, Limits).
* **vHost / vCluster**: Physical infrastructure specifications and aggregate capacity.
* **vDisk**: Storage capacity and disk inventory.

## Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Launch the utility: `streamlit run app.py`
3. Upload the RVTools .xlsx file.
4. Review the generated business case and performance metrics.
5. Download the Terraform Bundle (ZIP) for deployment via IBM Cloud CLI or IBM Cloud Schematics.

---
**Author**: Michael Vincent Jones
**Version**: 1.1.0
