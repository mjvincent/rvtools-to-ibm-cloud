# Carbon UI Prototype API Documentation

## Overview

The Carbon UI Prototype API provides RESTful endpoints for managing network planning state in IBM Cloud migration projects. It serves as the backend for the Carbon UI and bridges the gap between RVTools data and Terraform generation.

**Base URL**: `http://localhost:8000` (development)
**API Version**: 1.0
**Protocol**: HTTP/HTTPS
**Content-Type**: `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Network Planning Endpoints](#network-planning-endpoints)
3. [Data Models](#data-models)
4. [Error Handling](#error-handling)
5. [Examples](#examples)

---

## Authentication

Currently, the prototype API does not require authentication. In production, implement:
- API key authentication
- OAuth 2.0 / JWT tokens
- IBM Cloud IAM integration

---

## Network Planning Endpoints

### 1. Save Network Planning State

Save or update the complete network planning state for a project.

**Endpoint**: `POST /api/projects/{project_id}/network-plan`

**Parameters**:
- `project_id` (path, required): Unique identifier for the project

**Request Body**:
```json
{
  "version": "1.0",
  "vpcs": [...],
  "subnets": [...],
  "securityGroups": [...],
  "storageProfiles": [...],
  "waves": [...],
  "networkComponents": [...],
  "vmAssignments": [...],
  "metadata": {...}
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Network plan saved successfully",
  "project_id": "project-123"
}
```

**Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "loc": ["body", "vpcs", 0, "address_prefix_mode"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/projects/project-123/network-plan \
  -H "Content-Type: application/json" \
  -d @network-plan.json
```

---

### 2. Retrieve Network Planning State

Retrieve the saved network planning state for a project.

**Endpoint**: `GET /api/projects/{project_id}/network-plan`

**Parameters**:
- `project_id` (path, required): Unique identifier for the project

**Response** (200 OK):
```json
{
  "version": "1.0",
  "vpcs": [
    {
      "id": "vpc-1",
      "name": "migration-vpc",
      "label": "Migration VPC",
      "region": "us-south",
      "address_prefix_mode": "manual",
      "address_prefixes": [...],
      "tags": {},
      "notes": "",
      "created_at": "2026-06-23T00:00:00Z",
      "updated_at": "2026-06-23T00:00:00Z"
    }
  ],
  "subnets": [...],
  "securityGroups": [...],
  "storageProfiles": [...],
  "waves": [...],
  "networkComponents": [...],
  "vmAssignments": [...],
  "metadata": {...}
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Network plan not found for project: project-123"
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/projects/project-123/network-plan
```

---

### 3. Update VM Assignments

Update VM network assignments (subnet, security group, storage, wave).

**Endpoint**: `PUT /api/projects/{project_id}/vm-assignments`

**Parameters**:
- `project_id` (path, required): Unique identifier for the project

**Request Body**:
```json
{
  "assignments": [
    {
      "vm_key": "vm-1",
      "vm_name": "web-server-1",
      "primary_subnet_id": "subnet-1",
      "primary_security_group_id": "sg-1",
      "secondary_nics": [
        {
          "id": "nic-1",
          "subnet_id": "subnet-2",
          "security_group_id": "sg-2",
          "order": 1
        }
      ],
      "storage_profile_id": "storage-1",
      "wave_id": "wave-1",
      "excluded": false
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "VM assignments updated successfully",
  "count": 1
}
```

**Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "loc": ["body", "assignments", 0, "vm_key"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Example**:
```bash
curl -X PUT http://localhost:8000/api/projects/project-123/vm-assignments \
  -H "Content-Type: application/json" \
  -d @vm-assignments.json
```

---

## Data Models

### NetworkPlanningState

Complete network planning state for a migration project.

```typescript
{
  version: string;                      // Schema version (e.g., "1.0")
  vpcs: VpcBucket[];                    // VPC definitions
  subnets: SubnetBucket[];              // Subnet definitions
  securityGroups: SecurityBucket[];     // Security group definitions
  storageProfiles: StorageBucket[];     // Storage profile definitions
  waves: WaveBucket[];                  // Migration wave definitions
  networkComponents: NetworkComponent[]; // Network components (gateways, LBs, etc.)
  vmAssignments: VmNetworkAssignment[]; // VM-to-resource assignments
  metadata: PlanningMetadata;           // Project metadata
}
```

### VpcBucket

VPC (Virtual Private Cloud) definition.

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // VPC name (e.g., "migration-vpc")
  label: string;                        // Display label
  region: string;                       // IBM Cloud region (e.g., "us-south")
  address_prefix_mode: "manual" | "auto"; // Address prefix mode
  address_prefixes: AddressPrefix[];    // CIDR blocks for the VPC
  resource_group_id?: string;           // Optional resource group
  tags: Record<string, string>;         // Key-value tags
  notes: string;                        // User notes
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

### AddressPrefix

CIDR block for a VPC zone.

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // Prefix name
  cidr: string;                         // CIDR notation (e.g., "10.240.0.0/16")
  zone: string;                         // Availability zone (e.g., "us-south-1")
  is_default: boolean;                  // Whether this is the default prefix
}
```

### SubnetBucket

Subnet definition within a VPC.

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // Subnet name
  label: string;                        // Display label
  vpc_id: string;                       // Parent VPC ID
  zone: string;                         // Availability zone
  cidr: string;                         // CIDR notation (e.g., "10.240.10.0/24")
  purpose: string;                      // Purpose/tier (e.g., "web", "app", "data")
  source_network?: string;              // Source network from RVTools
  public_gateway: boolean;              // Whether to attach public gateway
  public_gateway_id?: string;           // Public gateway ID if attached
  acl_id?: string;                      // Network ACL ID
  route_table_id?: string;              // Route table ID
  ipv4_cidr_count?: number;             // Number of IPv4 addresses
  tags: Record<string, string>;         // Key-value tags
  notes: string;                        // User notes
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

### SecurityBucket

Security group definition with rules.

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // Security group name
  label: string;                        // Display label
  vpc_id: string;                       // Parent VPC ID
  purpose: string;                      // Purpose (e.g., "web", "app", "data")
  rules: SecurityRule[];                // Security rules
  tags: Record<string, string>;         // Key-value tags
  notes: string;                        // User notes
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

### SecurityRule

Individual security rule (inbound or outbound).

```typescript
{
  id: string;                           // Unique identifier
  direction: "inbound" | "outbound";    // Traffic direction
  protocol: "tcp" | "udp" | "icmp" | "all"; // Protocol
  port_min?: number;                    // Minimum port (1-65535, TCP/UDP only)
  port_max?: number;                    // Maximum port (1-65535, TCP/UDP only)
  source?: string;                      // Source CIDR (inbound rules)
  destination?: string;                 // Destination CIDR (outbound rules)
  description: string;                  // Rule description
}
```

### StorageBucket

Storage profile definition for boot/data volumes.

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // Profile name
  label: string;                        // Display label
  tier: string;                         // Storage tier (e.g., "general-purpose")
  iops_intent: string;                  // IOPS intent (e.g., "3000")
  notes: string;                        // User notes
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

### WaveBucket

Migration wave definition for phased cutover.

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // Wave name (e.g., "Wave 1")
  owner: string;                        // Wave owner/responsible party
  target_window: string;                // Target cutover window
  priority: "high" | "medium" | "low";  // Wave priority
  notes: string;                        // User notes
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

### NetworkComponent

Network component (gateway, load balancer, VPE, etc.).

```typescript
{
  id: string;                           // Unique identifier
  name: string;                         // Component name
  label: string;                        // Display label
  type: NetworkComponentType;           // Component type
  vpc_id: string;                       // Parent VPC ID
  subnet_id?: string;                   // Subnet ID (if applicable)
  attachment: string;                   // Attachment point
  config: Record<string, any>;          // Component-specific configuration
  tags: Record<string, string>;         // Key-value tags
  notes: string;                        // User notes
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}
```

**NetworkComponentType**:
- `public_gateway` - Public gateway for internet access
- `vpn_gateway` - VPN gateway for hybrid connectivity
- `load_balancer` - Application/network load balancer
- `vpe_gateway` - Virtual Private Endpoint gateway
- `floating_ip` - Floating IP address
- `route_table` - Custom route table
- `acl` - Network Access Control List

### VmNetworkAssignment

VM assignment to network resources.

```typescript
{
  vm_key: string;                       // Unique VM identifier
  vm_name: string;                      // VM display name
  primary_subnet_id: string;            // Primary subnet assignment
  primary_security_group_id: string;    // Primary security group assignment
  secondary_nics: SecondaryNic[];       // Additional network interfaces
  storage_profile_id?: string;          // Storage profile assignment
  wave_id?: string;                     // Migration wave assignment
  excluded: boolean;                    // Whether VM is excluded from migration
  exclusion_reason?: string;            // Reason for exclusion
}
```

### SecondaryNic

Secondary network interface for multi-NIC VMs.

```typescript
{
  id: string;                           // Unique identifier
  subnet_id: string;                    // Subnet assignment
  security_group_id: string;            // Security group assignment
  order: number;                        // NIC order (1, 2, 3, ...)
  source_network?: string;              // Source network from RVTools
}
```

### PlanningMetadata

Project metadata and settings.

```typescript
{
  project_name: string;                 // Project name
  target_region: string;                // Target IBM Cloud region
  target_zone: string;                  // Target availability zone
  deployment_target: "plain_cli" | "schematics"; // Deployment method
  created_by?: string;                  // Creator username
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
  rvtools_filename?: string;            // Source RVTools filename
  rvtools_uploaded_at?: string;         // RVTools upload timestamp
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request format |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

### Common Validation Errors

**Invalid CIDR**:
```json
{
  "loc": ["body", "subnets", 0, "cidr"],
  "msg": "Invalid CIDR notation",
  "type": "value_error"
}
```

**Invalid Port Range**:
```json
{
  "loc": ["body", "security_groups", 0, "rules", 0, "port_max"],
  "msg": "port_max must be >= port_min",
  "type": "value_error"
}
```

**Missing Required Field**:
```json
{
  "loc": ["body", "vpcs", 0, "name"],
  "msg": "field required",
  "type": "value_error.missing"
}
```

---

## Examples

### Complete Network Plan Example

```json
{
  "version": "1.0",
  "vpcs": [
    {
      "id": "vpc-1",
      "name": "production-vpc",
      "label": "Production VPC",
      "region": "us-south",
      "address_prefix_mode": "manual",
      "address_prefixes": [
        {
          "id": "prefix-1",
          "name": "zone-1-prefix",
          "cidr": "10.240.0.0/16",
          "zone": "us-south-1",
          "is_default": true
        }
      ],
      "tags": {
        "environment": "production",
        "project": "migration"
      },
      "notes": "Production VPC for migrated workloads",
      "created_at": "2026-06-23T00:00:00Z",
      "updated_at": "2026-06-23T00:00:00Z"
    }
  ],
  "subnets": [
    {
      "id": "subnet-1",
      "name": "web-tier",
      "label": "Web Tier Subnet",
      "vpc_id": "vpc-1",
      "zone": "us-south-1",
      "cidr": "10.240.10.0/24",
      "purpose": "web",
      "public_gateway": true,
      "public_gateway_id": "pgw-1",
      "tags": {
        "tier": "web"
      },
      "notes": "Public-facing web tier",
      "created_at": "2026-06-23T00:00:00Z",
      "updated_at": "2026-06-23T00:00:00Z"
    },
    {
      "id": "subnet-2",
      "name": "app-tier",
      "label": "Application Tier Subnet",
      "vpc_id": "vpc-1",
      "zone": "us-south-1",
      "cidr": "10.240.20.0/24",
      "purpose": "app",
      "public_gateway": false,
      "tags": {
        "tier": "app"
      },
      "notes": "Private application tier",
      "created_at": "2026-06-23T00:00:00Z",
      "updated_at": "2026-06-23T00:00:00Z"
    }
  ],
  "securityGroups": [
    {
      "id": "sg-1",
      "name": "web-sg",
      "label": "Web Security Group",
      "vpc_id": "vpc-1",
      "purpose": "web",
      "rules": [
        {
          "id": "rule-1",
          "direction": "inbound",
          "protocol": "tcp",
          "port_min": 80,
          "port_max": 80,
          "source": "0.0.0.0/0",
          "description": "Allow HTTP from internet"
        },
        {
          "id": "rule-2",
          "direction": "inbound",
          "protocol": "tcp",
          "port_min": 443,
          "port_max": 443,
          "source": "0.0.0.0/0",
          "description": "Allow HTTPS from internet"
        },
        {
          "id": "rule-3",
          "direction": "outbound",
          "protocol": "all",
          "destination": "0.0.0.0/0",
          "description": "Allow all outbound"
        }
      ],
      "tags": {
        "tier": "web"
      },
      "notes": "Security group for web tier",
      "created_at": "2026-06-23T00:00:00Z",
      "updated_at": "2026-06-23T00:00:00Z"
    }
  ],
  "storageProfiles": [],
  "waves": [],
  "networkComponents": [],
  "vmAssignments": [
    {
      "vm_key": "vm-web-1",
      "vm_name": "web-server-1",
      "primary_subnet_id": "subnet-1",
      "primary_security_group_id": "sg-1",
      "secondary_nics": [],
      "excluded": false
    }
  ],
  "metadata": {
    "project_name": "Production Migration",
    "target_region": "us-south",
    "target_zone": "us-south-1",
    "deployment_target": "plain_cli",
    "created_at": "2026-06-23T00:00:00Z",
    "updated_at": "2026-06-23T00:00:00Z"
  }
}
```

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Rate Limiting

Currently not implemented. In production, consider:
- 100 requests per minute per IP
- 1000 requests per hour per project
- Exponential backoff for retries

---

## Versioning

API version is included in the schema version field. Future versions will use URL versioning:
- v1: `/api/v1/projects/{id}/network-plan`
- v2: `/api/v2/projects/{id}/network-plan`

---

## Support

For issues or questions:
- GitHub Issues: [rvtools-to-ibm-cloud/issues](https://github.com/user/rvtools-to-ibm-cloud/issues)
- Documentation: See `docs/` directory
- Tests: See `tests/test_prototype_api_network_planning.py`
