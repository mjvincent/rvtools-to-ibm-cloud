"""
Tests for modular Terraform renderer (terraform_carbon_renderer_modular.py).

This test suite validates the new module-based Terraform generation structure
with SSH keys, backend configuration, and resource groups.
"""

import pytest
from models.network_planning import (
    NetworkPlanningState,
    VpcPlan,
    SubnetPlan,
    SecurityGroupPlan,
    SecurityRule,
    PlanningMetadata,
    AddressPrefix,
)
from terraform_carbon_renderer_modular import (
    render_modular_terraform_from_carbon_plan,
    generate_versions_tf,
    generate_provider_tf,
    generate_main_tf,
    generate_root_variables_tf,
    generate_root_outputs_tf,
    generate_terraform_tfvars_example,
    generate_networking_module_main,
    generate_vsi_module_main,
)


@pytest.fixture
def minimal_network_plan():
    """Minimal network plan with one VPC."""
    return NetworkPlanningState(
        vpcs=[
            VpcPlan(
                id="vpc-1",
                name="test-vpc",
                region="us-south",
                address_prefix_mode="auto"
            )
        ],
        metadata=PlanningMetadata(
            project_name="test-project",
            target_region="us-south",
            target_zone="us-south-1"
        )
    )


@pytest.fixture
def complete_network_plan():
    """Complete network plan with VPC, subnets, security groups."""
    return NetworkPlanningState(
        vpcs=[
            VpcPlan(
                id="vpc-1",
                name="production-vpc",
                region="us-south",
                address_prefix_mode="manual",
                address_prefixes=[
                    AddressPrefix(
                        id="prefix-1",
                        name="zone-1-prefix",
                        cidr="10.240.0.0/18",
                        zone="us-south-1",
                        is_default=True
                    )
                ]
            )
        ],
        subnets=[
            SubnetPlan(
                id="subnet-1",
                name="web-subnet",
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr="10.240.0.0/24",
                purpose="web tier"
            ),
            SubnetPlan(
                id="subnet-2",
                name="app-subnet",
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr="10.240.1.0/24",
                purpose="application tier"
            )
        ],
        security_groups=[
            SecurityGroupPlan(
                id="sg-1",
                name="web-sg",
                vpc_id="vpc-1",
                purpose="web tier security",
                rules=[
                    SecurityRule(
                        id="rule-1",
                        direction="inbound",
                        protocol="tcp",
                        port_min=443,
                        port_max=443,
                        source="0.0.0.0/0",
                        description="HTTPS from internet"
                    ),
                    SecurityRule(
                        id="rule-2",
                        direction="outbound",
                        protocol="all",
                        destination="0.0.0.0/0",
                        description="Allow all outbound"
                    )
                ]
            )
        ],
        metadata=PlanningMetadata(
            project_name="production-migration",
            target_region="us-south",
            target_zone="us-south-1",
            ssh_key_name="prod-migration-key",
            backend_type="local",
            resource_group_id="default-rg"
        )
    )


class TestVersionsFile:
    """Test versions.tf generation."""

    def test_versions_tf_structure(self):
        """Verify versions.tf has required Terraform and provider versions."""
        content = generate_versions_tf()

        assert "terraform {" in content
        assert "required_version" in content
        assert ">= 1.0" in content
        assert "required_providers" in content
        assert "IBM-Cloud/ibm" in content
        assert ">= 1.70.0" in content

    def test_versions_tf_valid_hcl(self):
        """Verify versions.tf is valid HCL syntax."""
        content = generate_versions_tf()

        # Check balanced braces
        assert content.count("{") == content.count("}")
        # Check no syntax errors
        assert "terraform {" in content
        assert content.strip().endswith("}")


class TestProviderFile:
    """Test provider.tf generation."""

    def test_provider_local_backend(self):
        """Verify local backend configuration."""
        content = generate_provider_tf("local")

        assert 'backend "local"' in content
        assert 'path = "terraform.tfstate"' in content
        assert 'provider "ibm"' in content
        assert 'region = var.region' in content

    def test_provider_s3_backend(self):
        """Verify S3 backend configuration."""
        content = generate_provider_tf("s3")

        assert 'backend "s3"' in content
        assert "# bucket" in content
        assert "# key" in content

    def test_provider_cos_backend(self):
        """Verify COS backend configuration."""
        content = generate_provider_tf("cos")

        assert 'backend "cos"' in content
        assert "# bucket" in content


class TestMainFile:
    """Test main.tf orchestration file generation."""

    def test_main_networking_only(self):
        """Verify main.tf with only networking module."""
        content = generate_main_tf(
            has_networking=True,
            has_vsi=False,
            has_storage=False
        )

        assert 'module "networking"' in content
        assert 'source = "./modules/networking"' in content
        assert 'module "vsi"' not in content
        assert 'module "storage"' not in content

    def test_main_all_modules(self):
        """Verify main.tf with all modules."""
        content = generate_main_tf(
            has_networking=True,
            has_vsi=True,
            has_storage=True,
            resource_group_id="rg-123"
        )

        assert 'module "networking"' in content
        assert 'module "vsi"' in content
        assert 'module "storage"' in content
        assert 'data "ibm_resource_group" "group"' in content
        assert 'resource_group_id = data.ibm_resource_group.group.id' in content

    def test_main_module_dependencies(self):
        """Verify VSI module receives networking outputs."""
        content = generate_main_tf(
            has_networking=True,
            has_vsi=True,
            has_storage=False
        )

        assert "vpc_id             = module.networking.vpc_id" in content
        assert "subnet_ids         = module.networking.subnet_ids" in content
        assert "security_group_ids = module.networking.security_group_ids" in content


class TestVariablesFile:
    """Test variables.tf generation."""

    def test_root_variables_basic(self):
        """Verify basic root variables."""
        content = generate_root_variables_tf(has_ssh_key=False, has_resource_group=False)

        assert 'variable "region"' in content
        assert 'variable "zone"' in content
        assert 'variable "project_name"' in content
        assert 'variable "custom_image_ids"' in content

    def test_root_variables_with_ssh_key(self):
        """Verify SSH key variable is included."""
        content = generate_root_variables_tf(has_ssh_key=True, has_resource_group=False)

        assert 'variable "ssh_public_key"' in content
        assert 'sensitive   = true' in content

    def test_root_variables_with_resource_group(self):
        """Verify resource group variable is included."""
        content = generate_root_variables_tf(has_ssh_key=False, has_resource_group=True)

        assert 'variable "resource_group_name"' in content


class TestOutputsFile:
    """Test outputs.tf generation."""

    def test_root_outputs_with_vpcs(self):
        """Verify outputs when VPCs exist."""
        content = generate_root_outputs_tf(["test-vpc"])

        assert 'output "vpc_id"' in content
        assert 'output "subnet_ids"' in content
        assert 'output "security_group_ids"' in content
        assert "module.networking" in content

    def test_root_outputs_empty(self):
        """Verify outputs when no VPCs exist."""
        content = generate_root_outputs_tf([])

        assert 'output "vpc_id"' not in content


class TestTfvarsExample:
    """Test terraform.tfvars.example generation."""

    def test_tfvars_example_basic(self):
        """Verify basic tfvars example structure."""
        content = generate_terraform_tfvars_example(
            region="us-south",
            zone="us-south-1",
            project_name="test-project"
        )

        assert 'region       = "us-south"' in content
        assert 'zone         = "us-south-1"' in content
        assert 'project_name = "test-project"' in content
        assert 'ssh_public_key' in content
        assert 'custom_image_ids' in content

    def test_tfvars_example_with_resource_group(self):
        """Verify resource group in tfvars example."""
        content = generate_terraform_tfvars_example(
            region="us-south",
            zone="us-south-1",
            project_name="test",
            resource_group_name="Default"
        )

        assert 'resource_group_name = "Default"' in content


class TestNetworkingModule:
    """Test networking module generation."""

    def test_networking_vpc_generation(self, complete_network_plan):
        """Verify VPC resource generation."""
        content = generate_networking_module_main(
            complete_network_plan.vpcs,
            complete_network_plan.subnets,
            complete_network_plan.security_groups,
            [],
            "test-project"
        )

        assert 'resource "ibm_is_vpc" "production_vpc"' in content
        assert 'name                      = "production-vpc"' in content
        assert 'address_prefix_management = "manual"' in content

    def test_networking_address_prefixes(self, complete_network_plan):
        """Verify address prefix generation for manual mode."""
        content = generate_networking_module_main(
            complete_network_plan.vpcs,
            [],
            [],
            [],
            "test-project"
        )

        assert 'resource "ibm_is_vpc_address_prefix"' in content
        assert 'cidr = "10.240.0.0/18"' in content
        assert 'zone = "us-south-1"' in content

    def test_networking_subnets(self, complete_network_plan):
        """Verify subnet resource generation."""
        content = generate_networking_module_main(
            complete_network_plan.vpcs,
            complete_network_plan.subnets,
            [],
            [],
            "test-project"
        )

        assert 'resource "ibm_is_subnet" "web_subnet"' in content
        assert 'resource "ibm_is_subnet" "app_subnet"' in content
        assert 'ipv4_cidr_block = "10.240.0.0/24"' in content
        assert 'ipv4_cidr_block = "10.240.1.0/24"' in content

    def test_networking_security_groups(self, complete_network_plan):
        """Verify security group resource generation."""
        content = generate_networking_module_main(
            complete_network_plan.vpcs,
            [],
            complete_network_plan.security_groups,
            [],
            "test-project"
        )

        assert 'resource "ibm_is_security_group" "web_sg"' in content
        assert 'name           = "web-sg"' in content

    def test_networking_security_rules(self, complete_network_plan):
        """Verify security group rule generation."""
        content = generate_networking_module_main(
            complete_network_plan.vpcs,
            [],
            complete_network_plan.security_groups,
            [],
            "test-project"
        )

        assert 'resource "ibm_is_security_group_rule"' in content
        assert 'direction = "inbound"' in content
        assert 'direction = "outbound"' in content
        assert 'port_min = 443' in content
        assert 'port_max = 443' in content
        assert 'remote    = "0.0.0.0/0"' in content


class TestVSIModule:
    """Test VSI module generation."""

    def test_vsi_ssh_key_generation(self):
        """Verify SSH key resource is generated."""
        content = generate_vsi_module_main([], [], [], "migration-key")

        assert 'resource "ibm_is_ssh_key"' in content
        assert 'name           = var.ssh_key_name' in content
        assert 'public_key     = var.ssh_public_key' in content

    def test_vsi_ssh_key_default_name(self):
        """Verify default SSH key name."""
        content = generate_vsi_module_main([], [], [], None)

        assert 'resource "ibm_is_ssh_key" "migration_key"' in content

class TestVSIGeneration:
    """Test VSI instance generation with VM assignments."""

    def test_vsi_generation_with_single_vm(self):
        """Test generating a single VSI instance."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-001",
            vm_name="web-server-01",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            cpu_count=4,
            memory_gb=16,
            ibm_profile="cx2-4x8",
            boot_disk_gb=100,
            guest_os="Ubuntu 22.04"
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert 'resource "ibm_is_instance" "web_server_01"' in content
        assert 'name           = "web-server-01"' in content
        assert 'profile        = "cx2-4x8"' in content
        assert 'subnet          = var.subnet_ids["app-subnet"]' in content
        assert 'security_groups = [var.security_group_ids["app-sg"]]' in content
        assert 'size     = 100' in content
        assert 'data.ibm_is_image.ubuntu_22_04.id' in content

    def test_vsi_generation_with_override_profile(self):
        """Test VSI with override profile and reasoning."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="db-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.1.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="db-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-002",
            vm_name="db-server-01",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            cpu_count=8,
            memory_gb=32,
            ibm_profile="mx2-8x64",
            override_profile="mx2-16x128",
            override_profile_reason="Database requires extra memory for caching",
            boot_disk_gb=250
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert 'profile        = "mx2-16x128"' in content
        assert 'Database requires extra memory for caching' in content

    def test_vsi_generation_with_custom_image(self):
        """Test VSI with custom image ID."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-003",
            vm_name="custom-app-01",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            cpu_count=2,
            memory_gb=4,
            custom_image_id="r006-custom-image-123",
            boot_disk_gb=100
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert 'var.custom_image_ids["custom-app-01"]' in content

    def test_vsi_generation_with_secondary_nics(self):
        """Test VSI with secondary network interfaces."""
        from models.network_planning import VmNetworkAssignment, SecondaryNicAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet1 = SubnetPlan(
            id="subnet-1",
            name="frontend-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        subnet2 = SubnetPlan(
            id="subnet-2",
            name="backend-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.1.0/24"
        )
        sg1 = SecurityGroupPlan(id="sg-1", name="frontend-sg", vpc_id="vpc-1")
        sg2 = SecurityGroupPlan(id="sg-2", name="backend-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-004",
            vm_name="multi-nic-server",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            secondary_nics=[
                SecondaryNicAssignment(
                    id="nic-1",
                    subnet_id="subnet-2",
                    security_group_id="sg-2",
                    order=1
                )
            ],
            cpu_count=4,
            memory_gb=8
        )

        content = generate_vsi_module_main([vm], [subnet1, subnet2], [sg1, sg2], "test-key")

        assert 'resource "ibm_is_instance_network_interface" "multi_nic_server_nic_1"' in content
        assert 'instance        = ibm_is_instance.multi_nic_server.id' in content
        assert 'subnet          = var.subnet_ids["backend-subnet"]' in content

    def test_vsi_generation_with_wave_tagging(self):
        """Test VSI with migration wave tagging."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-005",
            vm_name="wave1-app",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            wave_id="wave-1",
            cpu_count=2,
            memory_gb=4
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert '"wave:wave-1"' in content

    def test_vsi_generation_excluded_vm(self):
        """Test that excluded VMs are commented out."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-006",
            vm_name="excluded-server",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            excluded=True,
            exclusion_reason="Decommissioned before migration"
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert '# VM excluded-server excluded: Decommissioned before migration' in content
        assert 'resource "ibm_is_instance" "excluded_server"' not in content

    def test_vsi_generation_windows_image_selection(self):
        """Test automatic Windows image selection."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-007",
            vm_name="windows-server",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            guest_os="Windows Server 2022",
            cpu_count=4,
            memory_gb=16
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert 'data.ibm_is_image.windows_2022.id' in content

    def test_vsi_generation_rhel_image_selection(self):
        """Test automatic RHEL image selection."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-008",
            vm_name="rhel-server",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1",
            guest_os="Red Hat Enterprise Linux 9",
            cpu_count=2,
            memory_gb=8
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert 'data.ibm_is_image.rhel_9.id' in content

    def test_vsi_generation_profile_fallback(self):
        """Test profile fallback when no specs provided."""
        from models.network_planning import VmNetworkAssignment

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24"
        )
        sg = SecurityGroupPlan(id="sg-1", name="app-sg", vpc_id="vpc-1")

        vm = VmNetworkAssignment(
            vm_key="vm-009",
            vm_name="default-server",
            primary_subnet_id="subnet-1",
            primary_security_group_id="sg-1"
        )

        content = generate_vsi_module_main([vm], [subnet], [sg], "test-key")

        assert 'profile        = "cx2-2x4"' in content

    def test_vsi_stock_image_data_sources(self):
        """Test that stock image data sources are included."""
        from models.network_planning import VmNetworkAssignment

        content = generate_vsi_module_main([], [], [], "test-key")

        assert 'data "ibm_is_image" "ubuntu_22_04"' in content
        assert 'data "ibm_is_image" "rhel_9"' in content
        assert 'data "ibm_is_image" "windows_2022"' in content



class TestModularRendering:
    """Test complete modular Terraform rendering."""

    def test_minimal_plan_structure(self, minimal_network_plan):
        """Verify minimal plan generates all required files."""
        files = render_modular_terraform_from_carbon_plan(minimal_network_plan)

        # Root files
        assert "versions.tf" in files
        assert "provider.tf" in files
        assert "main.tf" in files
        assert "variables.tf" in files
        assert "outputs.tf" in files
        assert "terraform.tfvars.example" in files

        # Module files
        assert "modules/networking/main.tf" in files
        assert "modules/networking/variables.tf" in files
        assert "modules/networking/outputs.tf" in files
        assert "modules/vsi/main.tf" in files
        assert "modules/vsi/variables.tf" in files
        assert "modules/vsi/outputs.tf" in files
        assert "modules/storage/main.tf" in files
        assert "modules/storage/variables.tf" in files
        assert "modules/storage/outputs.tf" in files

    def test_complete_plan_content(self, complete_network_plan):
        """Verify complete plan generates correct content."""
        files = render_modular_terraform_from_carbon_plan(complete_network_plan)

        # Check main.tf orchestration
        assert 'module "networking"' in files["main.tf"]
        assert 'data "ibm_resource_group"' in files["main.tf"]

        # Check networking module
        assert "production-vpc" in files["modules/networking/main.tf"]
        assert "web-subnet" in files["modules/networking/main.tf"]
        assert "web-sg" in files["modules/networking/main.tf"]

        # Check SSH key in VSI module
        assert "prod-migration-key" not in files["modules/vsi/main.tf"]  # Uses variable
        assert "ssh_key_name" in files["modules/vsi/variables.tf"]

    def test_backend_configuration(self, minimal_network_plan):
        """Verify backend type is respected."""
        minimal_network_plan.metadata.backend_type = "s3"
        files = render_modular_terraform_from_carbon_plan(minimal_network_plan)

        assert 'backend "s3"' in files["provider.tf"]

    def test_project_name_override(self, minimal_network_plan):
        """Verify project name can be overridden."""
        files = render_modular_terraform_from_carbon_plan(
            minimal_network_plan,
            project_name="custom-project"
        )

        assert 'project_name = "custom-project"' in files["terraform.tfvars.example"]

    def test_file_count(self, complete_network_plan):
        """Verify correct number of files are generated."""
        files = render_modular_terraform_from_carbon_plan(complete_network_plan)

        # 6 root files + 9 module files = 15 total
        assert len(files) == 15


class TestResourceNaming:
    """Test resource name sanitization."""

    def test_vpc_with_special_chars(self):
        """Verify VPC names with special characters are sanitized."""
        plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(
                    id="vpc-1",
                    name="My VPC (Production)",
                    region="us-south"
                )
            ],
            metadata=PlanningMetadata()
        )

        files = render_modular_terraform_from_carbon_plan(plan)

        # Resource name should be sanitized
        assert 'resource "ibm_is_vpc" "my_vpc_production"' in files["modules/networking/main.tf"]
        # Display name should be preserved
        assert 'name                      = "My VPC (Production)"' in files["modules/networking/main.tf"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_network_plan(self):
        """Verify empty plan generates valid structure."""
        plan = NetworkPlanningState(metadata=PlanningMetadata())
        files = render_modular_terraform_from_carbon_plan(plan)

        # Should still generate all files
        assert len(files) == 15

        # Main.tf should not have networking module
        assert 'module "networking"' not in files["main.tf"]

    def test_vpc_without_subnets(self):
        """Verify VPC without subnets is valid."""
        plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
            ],
            metadata=PlanningMetadata()
        )

        files = render_modular_terraform_from_carbon_plan(plan)

        assert 'resource "ibm_is_vpc"' in files["modules/networking/main.tf"]
        assert 'resource "ibm_is_subnet"' not in files["modules/networking/main.tf"]

    def test_security_group_without_rules(self):
        """Verify security group without rules is valid."""
        plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(id="vpc-1", name="test-vpc", region="us-south")
            ],
            security_groups=[
                SecurityGroupPlan(
                    id="sg-1",
                    name="empty-sg",
                    vpc_id="vpc-1",
                    rules=[]
                )
            ],
            metadata=PlanningMetadata()
        )

        files = render_modular_terraform_from_carbon_plan(plan)

        assert 'resource "ibm_is_security_group" "empty_sg"' in files["modules/networking/main.tf"]
        # Should not have any rules
        assert files["modules/networking/main.tf"].count('resource "ibm_is_security_group_rule"') == 0




# =============================================================================
# Phase 3: Network Component Generation Tests
# =============================================================================

class TestNetworkComponentGeneration:
    """Test advanced network component generation."""

    def test_public_gateway_generation(self):
        """Test public gateway resource generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(
            id="vpc-1",
            name="test-vpc",
            region="us-south",
            address_prefix_mode="auto"
        )

        pgw = NetworkComponentPlan(
            id="pgw-1",
            name="test-public-gateway",
            type="public_gateway",
            vpc_id="vpc-1",
            config={
                "vpc_id": "vpc-1",
                "zone": "us-south-1"
            }
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[pgw],
            project_name="test-project"
        )

        assert 'resource "ibm_is_public_gateway" "test_public_gateway"' in result
        assert 'name           = "test-public-gateway"' in result
        assert 'vpc            = ibm_is_vpc.test_vpc.id' in result
        assert 'zone           = "us-south-1"' in result
        assert 'component:public-gateway' in result

    def test_floating_ip_generation(self):
        """Test floating IP resource generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        fip = NetworkComponentPlan(
            id="fip-1",
            name="test-floating-ip",
            type="floating_ip",
            vpc_id="vpc-1",
            config={
                "zone": "us-south-2",
                "target_type": "vsi"
            }
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[fip],
            project_name="test-project"
        )

        assert 'resource "ibm_is_floating_ip" "test_floating_ip"' in result
        assert 'name           = "test-floating-ip"' in result
        assert 'zone           = "us-south-2"' in result
        assert 'component:floating-ip' in result
        assert '# Target: vsi' in result

    def test_load_balancer_generation(self):
        """Test load balancer resource generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        subnet1 = SubnetPlan(
            id="subnet-1",
            name="lb-subnet-1",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.0.1.0/24"
        )

        subnet2 = SubnetPlan(
            id="subnet-2",
            name="lb-subnet-2",
            vpc_id="vpc-1",
            zone="us-south-2",
            cidr="10.0.2.0/24"
        )

        lb = NetworkComponentPlan(
            id="lb-1",
            name="test-load-balancer",
            type="load_balancer",
            vpc_id="vpc-1",
            config={
                "type": "public",
                "subnets": ["lb-subnet-1", "lb-subnet-2"]
            }
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[subnet1, subnet2],
            security_groups=[],
            network_components=[lb],
            project_name="test-project"
        )

        assert 'resource "ibm_is_lb" "test_load_balancer"' in result
        assert 'name           = "test-load-balancer"' in result
        assert 'type           = "public"' in result
        assert 'var.subnet_ids["lb-subnet-1"]' in result
        assert 'var.subnet_ids["lb-subnet-2"]' in result
        assert 'component:load-balancer' in result

    def test_vpn_gateway_placeholder(self):
        """Test VPN gateway placeholder generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        vpn = NetworkComponentPlan(
            id="vpn-1",
            name="test-vpn-gateway",
            type="vpn_gateway",
            vpc_id="vpc-1",
            config={"vpc_id": "vpc-1"}
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[vpn],
            project_name="test-project"
        )

        assert '# VPN Gateway: test-vpn-gateway' in result
        assert '# resource "ibm_is_vpn_gateway" "test_vpn_gateway"' in result
        assert '#   vpc            = ibm_is_vpc.test_vpc.id' in result
        assert 'component:vpn-gateway' in result

    def test_vpe_gateway_placeholder(self):
        """Test VPE gateway placeholder generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        vpe = NetworkComponentPlan(
            id="vpe-1",
            name="test-vpe-gateway",
            type="vpe_gateway",
            vpc_id="vpc-1",
            config={
                "vpc_id": "vpc-1",
                "service_name": "cloud-object-storage"
            }
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[vpe],
            project_name="test-project"
        )

        assert '# VPE Gateway: test-vpe-gateway' in result
        assert '# resource "ibm_is_virtual_endpoint_gateway" "test_vpe_gateway"' in result
        assert '#   vpc            = ibm_is_vpc.test_vpc.id' in result
        assert 'service:cloud-object-storage' in result

    def test_route_table_placeholder(self):
        """Test route table placeholder generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        rt = NetworkComponentPlan(
            id="rt-1",
            name="test-route-table",
            type="route_table",
            vpc_id="vpc-1",
            config={"vpc_id": "vpc-1"}
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[rt],
            project_name="test-project"
        )

        assert '# Route Table: test-route-table' in result
        assert '# resource "ibm_is_vpc_routing_table" "test_route_table"' in result
        assert '#   vpc  = ibm_is_vpc.test_vpc.id' in result

    def test_network_acl_placeholder(self):
        """Test network ACL placeholder generation"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        acl = NetworkComponentPlan(
            id="acl-1",
            name="test-network-acl",
            type="acl",
            vpc_id="vpc-1",
            config={"vpc_id": "vpc-1"}
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[acl],
            project_name="test-project"
        )

        assert '# Network ACL: test-network-acl' in result
        assert '# resource "ibm_is_network_acl" "test_network_acl"' in result
        assert '#   vpc  = ibm_is_vpc.test_vpc.id' in result

    def test_multiple_network_components(self):
        """Test generation of multiple network component types together"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        components = [
            NetworkComponentPlan(
                id="pgw-1",
                name="public-gateway-1",
                type="public_gateway",
                vpc_id="vpc-1",
                config={"vpc_id": "vpc-1", "zone": "us-south-1"}
            ),
            NetworkComponentPlan(
                id="fip-1",
                name="floating-ip-1",
                type="floating_ip",
                vpc_id="vpc-1",
                config={"zone": "us-south-1"}
            ),
            NetworkComponentPlan(
                id="lb-1",
                name="load-balancer-1",
                type="load_balancer",
                vpc_id="vpc-1",
                config={"type": "private", "subnets": []}
            ),
        ]

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=components,
            project_name="test-project"
        )

        # Verify all components are present
        assert 'resource "ibm_is_public_gateway" "public_gateway_1"' in result
        assert 'resource "ibm_is_floating_ip" "floating_ip_1"' in result
        assert 'resource "ibm_is_lb" "load_balancer_1"' in result
        assert 'type           = "private"' in result

    def test_network_components_with_missing_vpc_id(self):
        """Test network components gracefully handle missing vpc_id"""
        from models.network_planning import NetworkComponentPlan

        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        pgw = NetworkComponentPlan(
            id="pgw-1",
            name="test-gateway",
            type="public_gateway",
            vpc_id="vpc-1",
            config={"zone": "us-south-1"}  # No vpc_id in config
        )

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[pgw],
            project_name="test-project"
        )

        # Should default to first VPC
        assert 'vpc            = ibm_is_vpc.test_vpc.id' in result

    def test_empty_network_components(self):
        """Test that empty network components list doesn't break generation"""
        vpc = VpcPlan(id="vpc-1", name="test-vpc", region="us-south", address_prefix_mode="auto")

        result = generate_networking_module_main(
            vpcs=[vpc],
            subnets=[],
            security_groups=[],
            network_components=[],
            project_name="test-project"
        )

        # Should not have network components section
        assert '# Network Components' not in result
        # But should still have VPC
        assert 'resource "ibm_is_vpc" "test_vpc"' in result


# Made with Bob
# Made with Bob
