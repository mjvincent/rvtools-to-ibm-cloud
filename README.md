# RVTools to IBM Cloud VPC Migration Engine

An automated transformation tool designed to parse VMware metadata (RVTools) and generate production-ready, modular Terraform code for IBM Cloud VPC environments.

## Key Features

- **Heuristic Right-Sizing:** Automatically analyzes peak CPU telemetry from RVTools to suggest cost-optimized IBM Cloud VSI profiles, reducing potential over-provisioning.
- **Automated Storage Mapping:** Parses `vDisk` metadata to generate corresponding `ibm_is_volume` resources with accurate capacities.
- **Modular IaC Architecture:** Outputs a best-practice Terraform structure, separating Networking, Compute, and Storage into reusable modules.
- **Enterprise Standards:** Fully linted (PEP 8) and verified via GitHub Actions CI/CD pipeline.

## Understanding the Migration Preview

The tool evaluates every Virtual Machine using the following logic:

### Visual Indicators
- **Green Check (✅):** The tool identified an optimization opportunity. Based on a peak CPU utilization of < 40%, the IBM Cloud profile has been "right-sized" to a lower vCPU count to save costs while maintaining performance.
- **Red X (❌):** No change recommended. The VM's utilization suggests it requires its full allocated resources, or the performance data was unavailable. The tool matched the IBM Profile to the original VMware specifications.

### Behind the Scenes: The Mapping Engine
1. **Extraction:** The engine pulls vCPU, RAM, and Disk capacity from the `vInfo` and `vDisk` tabs.
2. **Analysis:** It calculates the RAM-to-vCPU ratio to select the optimal IBM Profile Family:
   - **Compute (cx2):** Ratio <= 2GB per vCPU
   - **Memory (mx2):** Ratio >= 8GB per vCPU
   - **Balanced (bx2):** Everything in between.
3. **Synthesis:** It generates HCL (HashiCorp Configuration Language) by injecting these values into pre-defined Jinja2 templates, ensuring the output is syntactically correct and ready for `terraform init`.

## Technology Stack

- **Python 3.11+**: Core logic engine.
- **Streamlit**: Web interface for file processing and configuration preview.
- **Jinja2**: Templating engine for HCL generation.
- **Pandas**: High-performance data manipulation for Excel parsing.

---
*Developed as a Technical Specialist tool for IBM Cloud Automation.*
