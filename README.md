# RVTools to IBM Cloud VPC Terraform Generator

An automated assessment and migration tool designed to ingest VMware RVTools exports and generate production-ready IBM Cloud VPC Terraform code.

## 🚀 Key Features

- **Automated Right-Sizing:** Maps VMware specs to the most cost-effective IBM VPC profiles.
- **Intelligent Storage Tiering:** - `10iops-tier`: High-performance (Databases/Prod).
  - `5iops-tier`: Standard performance (High-utilization Apps).
  - `3iops-tier`: General Purpose (Standard workloads/Cost-optimized).
- **Telemetry Validation:** Detects missing performance data and flags inconsistencies.
- **Modular Terraform Output:** Generates a standard directory structure:
  - `/modules/vsi`
  - `/modules/vpc`
  - `/modules/storage`
- **Exclusion Logic:** Automatically filters out powered-off virtual machines.

## 🛠️ Usage

1. **Environment Setup:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
- **Jinja2**: Templating engine for HCL generation.
- **Pandas**: High-performance data manipulation for Excel parsing.

## Latest Updates (April 2026)

### 🛠️ Interactive Decision Engine
The tool now features a "Human-in-the-Loop" workflow:
* **Dynamic Thresholds:** Architects can select from Industry Standard (30%-70%) utilization thresholds to drive recommendations.
* **Manual Overrides:** Users can individually override recommendations for mission-critical VMs directly in the web interface.
* **Decoupled HCL:** The generation logic now produces modular Terraform code with a dedicated `.tfvars` file for environment-specific configuration.

---
*Developed as a Technical Specialist tool for IBM Cloud Automation.*
