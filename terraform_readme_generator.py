"""
Generate comprehensive README files for Terraform packages.

This module creates detailed README documentation for both flat and modular
Terraform structures generated from Carbon UI network planning.
"""


def generate_modular_terraform_readme(
    project_name: str,
    target_region: str,
    target_zone: str,
    vpc_count: int,
    subnet_count: int,
    vm_count: int,
    has_ssh_key: bool = True,
    backend_type: str = "local",
) -> str:
    """
    Generate comprehensive README for modular Terraform package.

    Args:
        project_name: Name of the migration project
        target_region: IBM Cloud region
        target_zone: IBM Cloud availability zone
        vpc_count: Number of VPCs in the plan
        subnet_count: Number of subnets in the plan
        vm_count: Number of VMs to be migrated
        has_ssh_key: Whether SSH key is configured
        backend_type: Terraform backend type (local/s3/cos)

    Returns:
        Markdown-formatted README content
    """
    return f"""# Terraform Package: {project_name}

Generated from Carbon UI network planning workbench using modular structure.

## Package Structure

This package uses IBM Cloud best practices with a modular structure:

```
terraform-package/
├── versions.tf              # Terraform and provider version constraints
├── provider.tf              # IBM Cloud provider and backend configuration
├── main.tf                  # Module orchestration
├── variables.tf             # Root-level input variables
├── outputs.tf               # Aggregated outputs from modules
├── terraform.tfvars.example # Configuration template
├── network-plan.json        # Original Carbon planning state (reference)
└── modules/
    ├── networking/          # VPCs, subnets, security groups
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── vsi/                 # SSH keys, virtual server instances
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── storage/             # Block storage volumes
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Configuration

- **Region**: {target_region}
- **Zone**: {target_zone}
- **VPCs**: {vpc_count}
- **Subnets**: {subnet_count}
- **VMs**: {vm_count}
- **Backend**: {backend_type}

## Prerequisites

1. **Terraform** >= 1.0
2. **IBM Cloud CLI** with VPC plugin
3. **IBM Cloud API key** with VPC permissions
4. **SSH key pair** for VM access (REQUIRED)
5. **Custom images** imported to IBM Cloud (if using custom images)

## Quick Start

### 1. Configure Variables

Copy the example file and edit with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars
```

**IMPORTANT:** You MUST provide an SSH public key in `terraform.tfvars`:

```hcl
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQD... your-email@example.com"
```

Generate a new SSH key if needed:

```bash
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
cat ~/.ssh/id_rsa.pub  # Copy this value
```

### 2. Initialize Terraform

```bash
terraform init
```

This downloads the IBM Cloud provider and initializes modules.

### 3. Validate Configuration

```bash
terraform validate
terraform fmt -check
```

### 4. Plan Deployment

```bash
terraform plan
```

Review the plan output carefully. Terraform will show:
- Resources to be created
- Module dependencies
- Estimated costs (if available)

### 5. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm deployment.

### 6. Verify Deployment

```bash
terraform show
terraform output
```

## Module Architecture

### Networking Module (`modules/networking/`)

Creates the network foundation:
- **VPCs** with manual or auto address prefix management
- **Subnets** across availability zones
- **Security Groups** with inbound/outbound rules
- **Address Prefixes** (if manual mode)

### VSI Module (`modules/vsi/`)

Manages compute resources:
- **SSH Keys** for secure VM access (CRITICAL)
- **Virtual Server Instances** (when VM assignments are configured)
- **Network Interfaces** (primary and secondary NICs)

### Storage Module (`modules/storage/`)

Handles persistent storage:
- **Block Storage Volumes** for data disks
- **Volume Attachments** to VSIs

## Customization

### Backend Configuration

The default backend is `{backend_type}`. For team collaboration, edit `provider.tf`:

**S3 Backend:**
```hcl
terraform {{
  backend "s3" {{
    bucket = "my-terraform-state"
    key    = "carbon-migration/terraform.tfstate"
    region = "us-east-1"
  }}
}}
```

**IBM Cloud Object Storage:**
```hcl
terraform {{
  backend "cos" {{
    bucket = "my-terraform-state"
    key    = "carbon-migration/terraform.tfstate"
    region = "us-south"
  }}
}}
```

### Resource Groups

Specify a resource group in `terraform.tfvars`:

```hcl
resource_group_name = "production"
```

### Custom Images

After importing images to IBM Cloud, update `terraform.tfvars`:

```hcl
custom_image_ids = {{
  "vm-web-01" = "r006-12345678-1234-1234-1234-123456789abc"
  "vm-app-01" = "r006-87654321-4321-4321-4321-cba987654321"
}}
```

## Troubleshooting

### Authentication Issues

Set your IBM Cloud API key:

```bash
export IC_API_KEY="your-api-key"
```

Or use IBM Cloud CLI:

```bash
ibmcloud login --apikey @~/ibmcloud-api-key.txt
```

### SSH Key Required

If you see "ssh_public_key variable is required", ensure you've set it in `terraform.tfvars`.

⚠️ **VMs cannot be accessed without an SSH key!**

### Resource Quota

Verify sufficient quota:
- VPCs (default: 10 per region)
- Subnets (default: 15 per VPC)
- Security Groups (default: 25 per VPC)
- VSIs (varies by account)

Check: IBM Cloud Console → VPC Infrastructure → Overview

### Module Errors

If modules fail to initialize:

```bash
terraform get -update
terraform init -upgrade
```

## State Management

- **Local**: State stored in `terraform.tfstate` (default)
- **Remote**: Configure backend in `provider.tf` for team collaboration
- **Schematics**: Use IBM Cloud Schematics for managed Terraform

## Next Steps

1. **Import Custom Images**: Use IBM Cloud Console or CLI
2. **Configure VM Assignments**: Update network plan in Carbon UI
3. **Add Network Components**: Public gateways, load balancers, etc.
4. **Set Up Monitoring**: IBM Cloud Monitoring and Log Analysis
5. **Configure Backup**: Snapshots and backup policies

## Support

For issues or questions:
- Review the Carbon UI documentation
- Check IBM Cloud Terraform provider docs
- Contact your migration team lead

---

**Generated by Carbon UI Migration Workbench**
**Terraform Version**: >= 1.0
**IBM Cloud Provider**: >= 1.70.0
"""


# Made with Bob
