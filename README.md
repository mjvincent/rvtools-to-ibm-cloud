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

## Business Case and Mapping Output
The dashboard now includes a potential savings metric and exports an enriched business case CSV with per-VM data including:
* Baseline cost estimate
* Estimated monthly savings
* Subnet mapping for Terraform
* Security group mapping for Terraform (if enabled)
* User override fields for Profile and Storage Tier to influence generated Terraform

## Streamlit Override Controls
The Streamlit dashboard exposes editable override fields for `Override Profile` and `Override Storage Tier`. When set, these user-specified values are honored by the Terraform generator, allowing human-directed tuning of VSI sizing without changing the underlying migration logic.

### Example
If the auto-generated profile is `bx2-2x8` but you want the instance to use `cx2-2x4`, set `Override Profile` to `cx2-2x4` for that row before clicking **Build Terraform Project**. The generated VSI resource will then use the override profile.

If you want a lower-cost disk tier than the default recommendation, change `Override Storage Tier` from `5iops-tier` to `3iops-tier` for that row; the generated volume resource will then use the override tier.

### Override Columns
The Streamlit data table uses the following override columns:
* `Override Profile` — choose an alternate IBM Cloud VSI profile
* `Override Storage Tier` — choose an alternate storage IOPS tier
* `Subnet` — displays the generated subnet mapping for the selected network
* `Security Group` — displays the generated security group mapping when enabled

![Streamlit override controls example](docs/images/streamlit_override_example.png)

> Best practice: only set override values when you have validated that the target IBM Cloud profile and tier are supported for the workload and its storage requirements.

## Terraform Output Structure
The exported ZIP bundle now produces a modular Terraform layout:
* `main.tf`, `variables.tf`, `outputs.tf` at the root
* `modules/networking/main.tf`, `variables.tf`, `outputs.tf`
* `modules/storage/main.tf`, `variables.tf`, `outputs.tf`
* `modules/vsi/main.tf`, `variables.tf`, `outputs.tf`

![Terraform module layout example](docs/images/terraform_output_layout.png)

## Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Launch the utility: `streamlit run app.py`
3. Upload the RVTools .xlsx file.
4. Review the generated business case, savings metrics, and network/security mappings.
5. Download the Terraform Bundle (ZIP) for deployment via IBM Cloud CLI or IBM Cloud Schematics.

## Release Notes
- Added a potential savings metric to the Streamlit dashboard.
- Added per-VM baseline and savings values in the exported business case CSV.
- Added subnet and security group mapping fields to the business case export to support Terraform wiring.

---
**Author**: Michael Vincent Jones
**Version**: 1.1.0
