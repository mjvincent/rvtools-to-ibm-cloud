"""
Tests for network planning models and schemas.
"""

import pytest
from models.network_planning import (
    NetworkPlanningState,
    VpcPlan,
    SubnetPlan,
    SecurityGroupPlan,
    SecurityRule,
    AddressPrefix,
    to_dict,
    from_dict,
)


def test_vpc_plan_creation():
    """Test creating a VPC plan."""
    vpc = VpcPlan(
        id="vpc-1",
        name="test-vpc",
        region="us-south",
        address_prefix_mode="manual",
    )

    assert vpc.id == "vpc-1"
    assert vpc.name == "test-vpc"
    assert vpc.address_prefix_mode == "manual"
    assert vpc.region == "us-south"


def test_vpc_plan_invalid_mode():
    """Test that invalid address prefix mode raises error."""
    with pytest.raises(ValueError, match="address_prefix_mode must be"):
        VpcPlan(
            id="vpc-1",
            name="test-vpc",
            region="us-south",
            address_prefix_mode="invalid",
        )


def test_vpc_plan_with_address_prefixes():
    """Test VPC plan with address prefixes."""
    vpc = VpcPlan(
        id="vpc-1",
        name="test-vpc",
        region="us-south",
        address_prefix_mode="manual",
        address_prefixes=[
            AddressPrefix(
                id="prefix-1",
                name="zone-1-prefix",
                cidr="10.240.0.0/16",
                zone="us-south-1",
                is_default=True,
            )
        ],
    )

    assert len(vpc.address_prefixes) == 1
    assert vpc.address_prefixes[0].cidr == "10.240.0.0/16"
    assert vpc.address_prefixes[0].is_default is True


def test_subnet_plan_creation():
    """Test creating a subnet plan."""
    subnet = SubnetPlan(
        id="subnet-1",
        name="test-subnet",
        vpc_id="vpc-1",
        zone="us-south-1",
        cidr="10.240.10.0/24",
        purpose="web-tier",
    )

    assert subnet.id == "subnet-1"
    assert subnet.name == "test-subnet"
    assert subnet.vpc_id == "vpc-1"
    assert subnet.cidr == "10.240.10.0/24"
    assert subnet.purpose == "web-tier"


def test_security_rule_creation():
    """Test creating a security rule."""
    rule = SecurityRule(
        id="rule-1",
        direction="inbound",
        protocol="tcp",
        port_min=80,
        port_max=80,
        source="0.0.0.0/0",
        description="Allow HTTP",
    )

    assert rule.direction == "inbound"
    assert rule.protocol == "tcp"
    assert rule.port_min == 80
    assert rule.port_max == 80
    assert rule.source == "0.0.0.0/0"


def test_security_rule_invalid_direction():
    """Test that invalid direction raises error."""
    with pytest.raises(ValueError, match="direction must be"):
        SecurityRule(
            id="rule-1",
            direction="invalid",
            protocol="tcp",
        )


def test_security_rule_invalid_protocol():
    """Test that invalid protocol raises error."""
    with pytest.raises(ValueError, match="protocol must be"):
        SecurityRule(
            id="rule-1",
            direction="inbound",
            protocol="invalid",
        )


def test_security_group_plan_creation():
    """Test creating a security group plan."""
    sg = SecurityGroupPlan(
        id="sg-1",
        name="test-sg",
        vpc_id="vpc-1",
        purpose="web-tier",
        rules=[
            SecurityRule(
                id="rule-1",
                direction="inbound",
                protocol="tcp",
                port_min=443,
                port_max=443,
                source="0.0.0.0/0",
                description="Allow HTTPS",
            )
        ],
    )

    assert sg.id == "sg-1"
    assert sg.name == "test-sg"
    assert sg.vpc_id == "vpc-1"
    assert len(sg.rules) == 1
    assert sg.rules[0].port_min == 443


def test_network_planning_state_creation():
    """Test creating a network planning state."""
    state = NetworkPlanningState(
        vpcs=[
            VpcPlan(
                id="vpc-1",
                name="test-vpc",
                region="us-south",
            )
        ],
        subnets=[
            SubnetPlan(
                id="subnet-1",
                name="test-subnet",
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr="10.240.10.0/24",
            )
        ],
    )

    assert len(state.vpcs) == 1
    assert len(state.subnets) == 1
    assert state.vpcs[0].name == "test-vpc"
    assert state.subnets[0].cidr == "10.240.10.0/24"
    assert state.version == "1.0"


def test_network_planning_state_serialization():
    """Test converting network planning state to/from dict."""
    state = NetworkPlanningState(
        vpcs=[
            VpcPlan(
                id="vpc-1",
                name="test-vpc",
                region="us-south",
            )
        ],
    )

    # Convert to dict
    state_dict = to_dict(state)
    assert isinstance(state_dict, dict)
    assert len(state_dict["vpcs"]) == 1
    assert state_dict["vpcs"][0]["name"] == "test-vpc"
    assert state_dict["version"] == "1.0"

    # Convert back to NetworkPlanningState
    restored_state = from_dict(state_dict)
    assert isinstance(restored_state, NetworkPlanningState)
    assert len(restored_state.vpcs) == 1
    assert restored_state.vpcs[0].name == "test-vpc"


def test_network_planning_state_from_dict_with_nested_objects():
    """Test creating NetworkPlanningState from dict with nested objects."""
    data = {
        "version": "1.0",
        "vpcs": [
            {
                "id": "vpc-1",
                "name": "test-vpc",
                "region": "us-south",
                "address_prefix_mode": "manual",
                "address_prefixes": [
                    {
                        "id": "prefix-1",
                        "name": "zone-1-prefix",
                        "cidr": "10.240.0.0/16",
                        "zone": "us-south-1",
                        "is_default": True,
                    }
                ],
                "tags": {},
                "notes": "",
                "created_at": "2026-06-23T00:00:00",
                "updated_at": "2026-06-23T00:00:00",
            }
        ],
        "subnets": [],
        "security_groups": [],
        "storage_profiles": [],
        "waves": [],
        "network_components": [],
        "vm_assignments": [],
        "metadata": {
            "project_name": "test",
            "target_region": "us-south",
            "target_zone": "us-south-1",
            "deployment_target": "plain_cli",
            "created_at": "2026-06-23T00:00:00",
            "updated_at": "2026-06-23T00:00:00",
        },
    }

    state = from_dict(data)
    assert isinstance(state, NetworkPlanningState)
    assert len(state.vpcs) == 1
    assert isinstance(state.vpcs[0], VpcPlan)
    assert len(state.vpcs[0].address_prefixes) == 1
    assert isinstance(state.vpcs[0].address_prefixes[0], AddressPrefix)
    assert state.vpcs[0].address_prefixes[0].cidr == "10.240.0.0/16"


def test_network_planning_state_empty():
    """Test creating an empty network planning state."""
    state = NetworkPlanningState()

    assert state.version == "1.0"
    assert len(state.vpcs) == 0
    assert len(state.subnets) == 0
    assert len(state.security_groups) == 0
    assert state.metadata.target_region == "us-south"
    assert state.metadata.deployment_target == "plain_cli"


def test_network_planning_state_round_trip():
    """Test full round-trip serialization."""
    # Create a complex state
    original = NetworkPlanningState(
        vpcs=[
            VpcPlan(
                id="vpc-1",
                name="test-vpc",
                region="us-south",
                address_prefix_mode="manual",
                address_prefixes=[
                    AddressPrefix(
                        id="prefix-1",
                        name="zone-1-prefix",
                        cidr="10.240.0.0/16",
                        zone="us-south-1",
                        is_default=True,
                    )
                ],
            )
        ],
        subnets=[
            SubnetPlan(
                id="subnet-1",
                name="test-subnet",
                vpc_id="vpc-1",
                zone="us-south-1",
                cidr="10.240.10.0/24",
                purpose="web-tier",
                public_gateway=True,
            )
        ],
        security_groups=[
            SecurityGroupPlan(
                id="sg-1",
                name="test-sg",
                vpc_id="vpc-1",
                rules=[
                    SecurityRule(
                        id="rule-1",
                        direction="inbound",
                        protocol="tcp",
                        port_min=443,
                        port_max=443,
                        source="0.0.0.0/0",
                        description="Allow HTTPS",
                    )
                ],
            )
        ],
    )

    # Convert to dict and back
    state_dict = to_dict(original)
    restored = from_dict(state_dict)

    # Verify all data is preserved
    assert restored.version == original.version
    assert len(restored.vpcs) == len(original.vpcs)
    assert restored.vpcs[0].name == original.vpcs[0].name
    assert len(restored.vpcs[0].address_prefixes) == 1
    assert restored.vpcs[0].address_prefixes[0].cidr == "10.240.0.0/16"
    assert len(restored.subnets) == 1
    assert restored.subnets[0].public_gateway is True
    assert len(restored.security_groups) == 1
    assert len(restored.security_groups[0].rules) == 1
    assert restored.security_groups[0].rules[0].port_min == 443

# Made with Bob
