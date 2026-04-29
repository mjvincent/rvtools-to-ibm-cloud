# IBM Cloud Migration Utility 
🚀 **From Raw RVTools to Ready-to-Deploy Terraform in Seconds.**

This utility is a professional-grade migration tool designed to ingest VMware configuration data (RVTools) and output a fully right-sized, cost-optimized IBM Cloud VPC infrastructure plan. It implements **Strategy B (The Economic Optimizer)** to ensure workloads are not just moved, but transformed for maximum efficiency.

## 🚀 Key Features

* **Automated Right-Sizing:** Maps VMware telemetry to the most cost-effective IBM VPC profiles (`cx2`, `bx2`, `mx2`) based on architect-selected utilization thresholds.
* **Intelligent Storage Tiering:** * `10iops-tier`: High-performance (Triggered by DB/SAP/SQL keywords).
    * `5iops-tier`: Standard performance (Triggered by high CPU utilization >70%).
    * `3iops-tier`: General Purpose (Standard workloads/Cost-optimized).
* **Full Solution Costing:** Provides a transparent monthly spend estimate, breaking down **Compute (VSI)** vs. **Block Storage** costs for each workload.
* **Modular Terraform Output:** Generates a standard, deployment-ready directory structure delivered as a single `.zip` bundle:
    * `/modules/vsi`
    * `/modules/vpc`
    * `/modules/storage`
    * `main.tf`, `variables.tf`, & `terraform.tfvars`
* **Executive Business Case:** Automatically calculates savings against an industry-standard **$30/vCPU On-Prem TCO** baseline.

## 🛠️ Usage & Installation

1. **Environment Setup:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
