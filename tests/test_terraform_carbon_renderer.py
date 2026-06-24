"""
Tests for terraform_carbon_renderer.py - Carbon UI Terraform generation.

Tests the conversion of Carbon network planning state into production-ready
Terraform HCL files.
"""

import pytest
from models.network_planning import (
    NetworkPlanningState,
    VpcPlan,
    SubnetPlan,
    SecurityGroupPlan,
    SecurityRule,
    NetworkComponentPlan,
    VmNetworkAssignment,
    PlanningMetadata,
)
from terraform_carbon_renderer import (
    render_networking_from_carbon_plan,
    render_vpc_from_carbon,
    render_subnet_from_carbon,
    render_security_group_from_carbon,
    render_network_component_from_carbon,
    _safe_resource_name,
    _ibm_name,
    _hcl_string,
)


class TestHelperFunctions:
    """Test HCL helper functions."""

    def test_hcl_string_basic(self):
        assert _hcl_string("test") == '"test"'
        assert _hcl_string("test-name") == '"test-name"'

    def test_hcl_string_with_quotes(self):
        assert _hcl_string('test"quote') == '"test\\"quote"'

    def test_hcl_string_none(self):
        assert _hcl_string(None) == '""'
        assert _hcl_string(None, "default") == '"default"'

    def test_safe_resource_name_basic(self):
        assert _safe_resource_name("my-vpc") == "my_vpc"
        assert _safe_resource_name("My VPC 123") == "my_vpc_123"

    def test_safe_resource_name_special_chars(self):
        assert _safe_resource_name("vpc@#$%name") == "vpc_name"
        assert _safe_resource_name("___test___") == "test"

    def test_safe_resource_name_starts_with_digit(self):
        assert _safe_resource_name("123-vpc") == "r_123_vpc"

    def test_safe_resource_name_empty(self):
        assert _safe_resource_name("") == "unknown"
        assert _safe_resource_name("@#$%") == "unknown"

    def test_ibm_name_basic(self):
        assert _ibm_name("my_vpc") == "my-vpc"
        assert _ibm_name("My VPC 123") == "my-vpc-123"

    def test_ibm_name_multiple_hyphens(self):
        assert _ibm_name("test---name") == "test-name"
        assert _ibm_name("---test---") == "test"


class TestVpcGeneration:
    """Test VPC Terraform generation."""

    def test_render_vpc_basic(self):
        vpc = VpcPlan(
            id="vpc-1",
            name="production-vpc",
            region="us-south",
        )
        hcl = render_vpc_from_carbon(vpc, "test-project")

        assert "resource \"ibm_is_vpc\" \"production_vpc\"" in hcl
        assert "name = \"production-vpc\"" in hcl
        assert "tags = [\"project:test-project\"]" in hcl

    def test_render_vpc_with_resource_group(self):
        vpc = VpcPlan(
            id="vpc-1",
            name="test-vpc",
            region="us-south",
            resource_group_id="rg-123",
        )
        hcl = render_vpc_from_carbon(vpc, "test-project")

        assert "resource_group = \"rg-123\"" in hcl

    def test_render_vpc_with_custom_tags(self):
        vpc = VpcPlan(
            id="vpc-1",
            name="test-vpc",
            region="us-south",
            tags={"env": "prod", "team": "platform"},
        )
        hcl = render_vpc_from_carbon(vpc, "test-project")

        assert "env:prod" in hcl
        assert "team:platform" in hcl


class TestSubnetGeneration:
    """Test subnet Terraform generation."""

    def test_render_subnet_basic(self):
        subnet = SubnetPlan(
            id="subnet-1",
            name="web-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.0.0/24",
        )
        hcl = render_subnet_from_carbon(subnet, "production_vpc", "test-project")

        assert "resource \"ibm_is_subnet\" \"web_subnet\"" in hcl
        assert "name = \"web-subnet\"" in hcl
        assert "vpc = ibm_is_vpc.production_vpc.id" in hcl
        assert "zone = \"us-south-1\"" in hcl
        assert "ipv4_cidr_block = \"10.240.0.0/24\"" in hcl

    def test_render_subnet_with_public_gateway(self):
        subnet = SubnetPlan(
            id="subnet-1",
            name="app-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.1.0/24",
            public_gateway=True,
        )
        hcl = render_subnet_from_carbon(subnet, "production_vpc", "test-project")

        assert "public_gateway" in hcl

    def test_render_subnet_with_purpose(self):
        subnet = SubnetPlan(
            id="subnet-1",
            name="db-subnet",
            vpc_id="vpc-1",
            zone="us-south-1",
            cidr="10.240.2.0/24",
            purpose="database",
        )
        hcl = render_subnet_from_carbon(subnet, "production_vpc", "test-project")

        assert "purpose:database" in hcl or "database" in hcl


class TestSecurityGroupGeneration:
    """Test security group Terraform generation."""

    def test_render_security_group_basic(self):
        sg = SecurityGroupPlan(
            id="sg-1",
            name="web-sg",
            vpc_id="vpc-1",
        )
        hcl = render_security_group_from_carbon(sg, "production_vpc", "test-project")

        assert "resource \"ibm_is_security_group\" \"web_sg\"" in hcl
        assert "name = \"web-sg\"" in hcl
        assert "vpc = ibm_is_vpc.production_vpc.id" in hcl

    def test_render_security_group_with_rules(self):
        sg = SecurityGroupPlan(
            id="sg-1",
            name="app-sg",
            vpc_id="vpc-1",
            rules=[
                SecurityRule(
                    id="rule-1",
                    direction="inbound",
                    protocol="tcp",
                    port_min=443,
                    port_max=443,
                    source="0.0.0.0/0",
                    description="HTTPS from anywhere",
                ),
                SecurityRule(
                    id="rule-2",
                    direction="outbound",
                    protocol="all",
                    destination="0.0.0.0/0",
                    description="Allow all outbound",
                ),
            ],
        )
        hcl = render_security_group_from_carbon(sg, "production_vpc", "test-project")

        assert "resource \"ibm_is_security_group_rule\"" in hcl
        assert "direction = \"inbound\"" in hcl
        assert "tcp" in hcl
        assert "443" in hcl
        assert "HTTPS from anywhere" in hcl

    def test_render_security_group_icmp_rule(self):
        sg = SecurityGroupPlan(
            id="sg-1",
            name="test-sg",
            vpc_id="vpc-1",
            rules=[
                SecurityRule(
                    id="rule-1",
                    direction="inbound",
                    protocol="icmp",
                    source="10.0.0.0/8",
                    description="ICMP from private network",
                ),
            ],
        )
        hcl = render_security_group_from_carbon(sg, "production_vpc", "test-project")

        assert "icmp" in hcl
        assert "10.0.0.0/8" in hcl


class TestNetworkComponentGeneration:
    """Test network component Terraform generation."""

    def test_render_public_gateway(self):
        component = NetworkComponentPlan(
            id="pgw-1",
            name="prod-pgw",
            vpc_id="vpc-1",
            type="public_gateway",
            config={"zone": "us-south-1"},
        )
        hcl = render_network_component_from_carbon(component, "production_vpc", "test-project")

        assert "# Public Gateway: prod-pgw" in hcl or "public_gateway" in hcl.lower()

    def test_render_load_balancer(self):
        component = NetworkComponentPlan(
            id="lb-1",
            name="app-lb",
            vpc_id="vpc-1",
            type="load_balancer",
            config={"subnets": ["subnet-1", "subnet-2"]},
        )
        hcl = render_network_component_from_carbon(component, "production_vpc", "test-project")

        assert "# Load Balancer: app-lb" in hcl or "load_balancer" in hcl.lower()

    def test_render_vpn_gateway(self):
        component = NetworkComponentPlan(
            id="vpn-1",
            name="site-vpn",
            vpc_id="vpc-1",
            type="vpn_gateway",
            config={"subnet": "subnet-1"},
        )
        hcl = render_network_component_from_carbon(component, "production_vpc", "test-project")

        assert "# VPN Gateway: site-vpn" in hcl or "vpn" in hcl.lower()


class TestFullNetworkPlanGeneration:
    """Test complete network plan Terraform generation."""

    def test_render_minimal_network_plan(self):
        """Test minimal valid network plan."""
        network_plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(
                    id="vpc-1",
                    name="test-vpc",
                    region="us-south",
                ),
            ],
            subnets=[
                SubnetPlan(
                    id="subnet-1",
                    name="test-subnet",
                    vpc_id="vpc-1",
                    zone="us-south-1",
                    cidr="10.240.0.0/24",
                ),
            ],
            security_groups=[
                SecurityGroupPlan(
                    id="sg-1",
                    name="test-sg",
                    vpc_id="vpc-1",
                ),
            ],
        )

        terraform_files = render_networking_from_carbon_plan(
            network_plan,
            project_name="test-project"
        )

        assert "providers.tf" in terraform_files
        assert "vpc.tf" in terraform_files
        assert "subnets.tf" in terraform_files
        assert "security_groups.tf" in terraform_files
        assert "variables.tf" in terraform_files
        assert "outputs.tf" in terraform_files

    def test_render_complete_network_plan(self):
        """Test complete network plan with all components."""
        network_plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(
                    id="vpc-1",
                    name="production-vpc",
                    region="us-south",
                    tags={"env": "prod"},
                ),
            ],
            subnets=[
                SubnetPlan(
                    id="subnet-1",
                    name="web-subnet",
                    vpc_id="vpc-1",
                    zone="us-south-1",
                    cidr="10.240.0.0/24",
                    purpose="web",
                ),
                SubnetPlan(
                    id="subnet-2",
                    name="app-subnet",
                    vpc_id="vpc-1",
                    zone="us-south-1",
                    cidr="10.240.1.0/24",
                    purpose="app",
                ),
            ],
            security_groups=[
                SecurityGroupPlan(
                    id="sg-1",
                    name="web-sg",
                    vpc_id="vpc-1",
                    rules=[
                        SecurityRule(
                            id="rule-1",
                            direction="inbound",
                            protocol="tcp",
                            port_min=443,
                            port_max=443,
                            source="0.0.0.0/0",
                        ),
                    ],
                ),
            ],
            network_components=[
                NetworkComponentPlan(
                    id="pgw-1",
                    name="prod-pgw",
                    vpc_id="vpc-1",
                    type="public_gateway",
                    config={"zone": "us-south-1"},
                ),
            ],
            vm_assignments=[
                VmNetworkAssignment(
                    vm_key="vm-1",
                    vm_name="web-01",
                    primary_subnet_id="subnet-1",
                    primary_security_group_id="sg-1",
                ),
            ],
            metadata=PlanningMetadata(
                project_name="test-project",
                target_region="us-south",
                target_zone="us-south-1",
            ),
        )

        terraform_files = render_networking_from_carbon_plan(
            network_plan,
            project_name="test-project"
        )

        # Verify all files generated
        assert len(terraform_files) >= 6

        # Verify VPC content
        assert "production-vpc" in terraform_files["vpc.tf"]

        # Verify subnet content
        assert "web-subnet" in terraform_files["subnets.tf"]
        assert "app-subnet" in terraform_files["subnets.tf"]

        # Verify security group content
        assert "web-sg" in terraform_files["security_groups.tf"]
        assert "443" in terraform_files["security_groups.tf"]

        # Verify network components
        assert "network_components.tf" in terraform_files
        assert "prod-pgw" in terraform_files["network_components.tf"]

        # Verify VSI content
        assert "vsi.tf" in terraform_files
        assert "web-01" in terraform_files["vsi.tf"]

    def test_render_multi_vpc_network_plan(self):
        """Test network plan with multiple VPCs."""
        network_plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(id="vpc-1", name="prod-vpc", region="us-south"),
                VpcPlan(id="vpc-2", name="dev-vpc", region="us-south"),
            ],
            subnets=[
                SubnetPlan(
                    id="subnet-1",
                    name="prod-subnet",
                    vpc_id="vpc-1",
                    zone="us-south-1",
                    cidr="10.240.0.0/24",
                ),
                SubnetPlan(
                    id="subnet-2",
                    name="dev-subnet",
                    vpc_id="vpc-2",
                    zone="us-south-1",
                    cidr="10.241.0.0/24",
                ),
            ],
            security_groups=[
                SecurityGroupPlan(id="sg-1", name="prod-sg", vpc_id="vpc-1"),
                SecurityGroupPlan(id="sg-2", name="dev-sg", vpc_id="vpc-2"),
            ],
        )

        terraform_files = render_networking_from_carbon_plan(
            network_plan,
            project_name="multi-vpc-project"
        )

        # Verify both VPCs
        assert "prod-vpc" in terraform_files["vpc.tf"]
        assert "dev-vpc" in terraform_files["vpc.tf"]

        # Verify outputs for both VPCs
        assert "prod_vpc_id" in terraform_files["outputs.tf"]
        assert "dev_vpc_id" in terraform_files["outputs.tf"]

    def test_render_network_plan_with_metadata(self):
        """Test that metadata is used when provided."""
        network_plan = NetworkPlanningState(
            vpcs=[VpcPlan(id="vpc-1", name="test-vpc", region="us-south")],
            subnets=[
                SubnetPlan(
                    id="subnet-1",
                    name="test-subnet",
                    vpc_id="vpc-1",
                    zone="us-south-1",
                    cidr="10.240.0.0/24",
                ),
            ],
            security_groups=[
                SecurityGroupPlan(id="sg-1", name="test-sg", vpc_id="vpc-1"),
            ],
            metadata=PlanningMetadata(
                project_name="metadata-project",
                target_region="us-east",
                target_zone="us-east-1",
            ),
        )

        terraform_files = render_networking_from_carbon_plan(network_plan)

        # Project name from metadata should be used in tags
        assert "metadata-project" in terraform_files["vpc.tf"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_network_plan(self):
        """Test handling of empty network plan."""
        network_plan = NetworkPlanningState()

        terraform_files = render_networking_from_carbon_plan(
            network_plan,
            project_name="empty-project"
        )

        # Should still generate base files
        assert "providers.tf" in terraform_files
        assert "variables.tf" in terraform_files

    def test_vpc_without_subnets(self):
        """Test VPC with no subnets."""
        network_plan = NetworkPlanningState(
            vpcs=[VpcPlan(id="vpc-1", name="lonely-vpc", region="us-south")],
        )

        terraform_files = render_networking_from_carbon_plan(
            network_plan,
            project_name="test-project"
        )

        assert "lonely-vpc" in terraform_files["vpc.tf"]
        # Subnets file should still be generated but empty
        assert "subnets.tf" in terraform_files

    def test_special_characters_in_names(self):
        """Test handling of special characters in resource names."""
        network_plan = NetworkPlanningState(
            vpcs=[
                VpcPlan(
                    id="vpc-1",
                    name="My VPC (Production) #1",
                    region="us-south",
                ),
            ],
            subnets=[
                SubnetPlan(
                    id="subnet-1",
                    name="Web Subnet @ Zone-1",
                    vpc_id="vpc-1",
                    zone="us-south-1",
                    cidr="10.240.0.0/24",
                ),
            ],
            security_groups=[
                SecurityGroupPlan(
                    id="sg-1",
                    name="SG: Web & App",
                    vpc_id="vpc-1",
                ),
            ],
        )

        terraform_files = render_networking_from_carbon_plan(
            network_plan,
            project_name="test-project"
        )

        # Names should be sanitized for Terraform resource names
        vpc_tf = terraform_files["vpc.tf"]
        assert "resource \"ibm_is_vpc\"" in vpc_tf
        # But original names should be preserved in name attributes
        assert "My VPC (Production) #1" in vpc_tf or "my-vpc-production-1" in vpc_tf


# Made with Bob
