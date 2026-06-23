# Carbon UI Integration Architecture Diagrams

This document provides visual representations of the Carbon UI integration architecture, data flows, and component interactions.

---

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        A[Carbon UI<br/>Next.js + React + IBM Carbon]
        B[Streamlit App<br/>Production Workbench]
    end

    subgraph "API Layer"
        C[FastAPI<br/>prototype/api/]
    end

    subgraph "Business Logic Layer"
        D[RVTools Parser<br/>rvtools_parser.py]
        E[Assessments<br/>assessments.py]
        F[Sizing<br/>sizing.py]
        G[Terraform Renderer<br/>terraform_renderer.py]
        H[Handoff Package<br/>handoff/]
    end

    subgraph "Data Layer"
        I[(Postgres<br/>Projects & State)]
        J[Docker Volumes<br/>Artifacts]
    end

    A -->|REST API| C
    B -->|Direct Import| D
    C -->|Shared Logic| D
    C -->|Shared Logic| E
    C -->|Shared Logic| F
    C -->|Shared Logic| G
    C -->|Shared Logic| H
    C -->|Persist| I
    C -->|Store| J
    G -->|Generate| J

    style A fill:#0f62fe,color:#fff
    style B fill:#24a148,color:#fff
    style C fill:#8a3ffc,color:#fff
    style I fill:#fa4d56,color:#fff
```

---

## 2. Network Planning Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CarbonUI as Carbon UI
    participant API as FastAPI
    participant Parser as RVTools Parser
    participant Renderer as Terraform Renderer
    participant DB as Postgres
    participant Storage as Docker Volume

    User->>CarbonUI: Upload RVTools workbook
    CarbonUI->>API: POST /api/workbook/upload
    API->>Parser: parse_rvtools_workbook()
    Parser-->>API: ParsedWorkbook (unique_nets, VMs)
    API->>API: create_initial_network_plan()
    API-->>CarbonUI: WorkbookSummary + NetworkPlan

    User->>CarbonUI: Create VPC/Subnet buckets
    User->>CarbonUI: Assign VMs to subnets
    CarbonUI->>API: POST /api/projects/{id}/network-plan
    API->>DB: Save planning_state_json
    DB-->>API: Success
    API-->>CarbonUI: Saved

    User->>CarbonUI: Generate Terraform
    CarbonUI->>API: POST /api/projects/{id}/terraform/generate
    API->>DB: Load planning_state_json
    DB-->>API: NetworkPlanningState
    API->>Renderer: render_networking_from_carbon_plan()
    API->>Renderer: render_vsi_from_carbon_assignments()
    Renderer-->>API: Terraform HCL
    API->>API: Build handoff package ZIP
    API->>Storage: Store artifact
    Storage-->>API: artifact_id
    API-->>CarbonUI: Download URL

    User->>CarbonUI: Download Terraform ZIP
    CarbonUI->>API: GET /api/projects/{id}/terraform/download
    API->>Storage: Retrieve artifact
    Storage-->>API: ZIP file
    API-->>CarbonUI: Terraform package
    CarbonUI-->>User: Download complete
```

---

## 3. Network Planning Schema Relationships

```mermaid
erDiagram
    NetworkPlanningState ||--o{ VpcBucket : contains
    NetworkPlanningState ||--o{ SubnetBucket : contains
    NetworkPlanningState ||--o{ SecurityBucket : contains
    NetworkPlanningState ||--o{ NetworkComponent : contains
    NetworkPlanningState ||--o{ VmNetworkAssignment : contains
    NetworkPlanningState ||--|| PlanningMetadata : has

    VpcBucket ||--o{ AddressPrefix : has
    VpcBucket ||--o{ SubnetBucket : contains
    VpcBucket ||--o{ SecurityBucket : contains
    VpcBucket ||--o{ NetworkComponent : contains

    SubnetBucket }o--|| VpcBucket : belongs_to
    SubnetBucket ||--o{ VmNetworkAssignment : assigned_to
    SubnetBucket }o--o| NetworkComponent : has_public_gateway
    SubnetBucket }o--o| NetworkComponent : has_acl
    SubnetBucket }o--o| NetworkComponent : has_route_table

    SecurityBucket }o--|| VpcBucket : belongs_to
    SecurityBucket ||--o{ SecurityRule : contains
    SecurityBucket ||--o{ VmNetworkAssignment : assigned_to

    VmNetworkAssignment }o--|| SubnetBucket : primary_subnet
    VmNetworkAssignment }o--|| SecurityBucket : primary_security_group
    VmNetworkAssignment ||--o{ SecondaryNic : has

    SecondaryNic }o--|| SubnetBucket : subnet
    SecondaryNic }o--|| SecurityBucket : security_group

    NetworkComponent }o--|| VpcBucket : belongs_to
    NetworkComponent }o--o| SubnetBucket : attached_to
```

---

## 4. Drag-and-Drop Assignment Flow

```mermaid
stateDiagram-v2
    [*] --> Unassigned: VM loaded from RVTools

    Unassigned --> Dragging: User starts drag
    Dragging --> Unassigned: User cancels drag
    Dragging --> ValidatingDrop: User drops on bucket

    ValidatingDrop --> Assigned: Valid drop
    ValidatingDrop --> Dragging: Invalid drop (show error)

    Assigned --> Dragging: User drags to reassign
    Assigned --> [*]: VM excluded from migration

    note right of ValidatingDrop
        Validation checks:
        - Bucket exists
        - Bucket type matches mode
        - No conflicts
        - Subnet in same VPC
    end note

    note right of Assigned
        Assignment persisted:
        - Primary subnet
        - Primary security group
        - Secondary NICs (if any)
        - Storage profile
        - Wave
    end note
```

---

## 5. Terraform Generation Pipeline

```mermaid
flowchart TD
    A[Carbon Network Plan] --> B{Validate Plan}
    B -->|Invalid| C[Return Validation Errors]
    B -->|Valid| D[Load VM Assignments]

    D --> E[Generate VPC Resources]
    D --> F[Generate Subnet Resources]
    D --> G[Generate Security Group Resources]
    D --> H[Generate Network Components]
    D --> I[Generate VSI Resources]
    D --> J[Generate Storage Resources]

    E --> K[Networking Module]
    F --> K
    G --> K
    H --> K

    I --> L[VSI Module]
    J --> M[Storage Module]

    K --> N[Root main.tf]
    L --> N
    M --> N

    N --> O[Generate Handoff Files]
    O --> P[Migration Manifest]
    O --> Q[CSV Exports]
    O --> R[Runbook]
    O --> S[Preflight Report]

    P --> T[Package ZIP]
    Q --> T
    R --> T
    S --> T
    N --> T

    T --> U[Store Artifact]
    U --> V[Return Download URL]

    style A fill:#0f62fe,color:#fff
    style T fill:#24a148,color:#fff
    style V fill:#8a3ffc,color:#fff
```

---

## 6. Component Interaction: VM Assignment

```mermaid
sequenceDiagram
    participant User
    participant DragDrop as DragDropAssignment
    participant State as React State
    participant API as FastAPI
    participant DB as Postgres

    User->>DragDrop: Start dragging VM
    DragDrop->>State: setActiveId(vmId)
    DragDrop->>DragDrop: Show drag overlay

    User->>DragDrop: Drop VM on subnet bucket
    DragDrop->>DragDrop: Validate drop target

    alt Valid Drop
        DragDrop->>State: Update VM assignment
        State->>API: PUT /api/projects/{id}/vm-assignments
        API->>DB: Update planning_state_json
        DB-->>API: Success
        API-->>State: Assignment saved
        State->>DragDrop: Re-render with new assignment
        DragDrop->>User: Show success feedback
    else Invalid Drop
        DragDrop->>User: Show error message
        DragDrop->>State: Revert to previous state
    end

    DragDrop->>State: setActiveId(null)
    DragDrop->>DragDrop: Hide drag overlay
```

---

## 7. Feature Parity Progress Tracking

```mermaid
gantt
    title Carbon UI Feature Parity Roadmap
    dateFormat YYYY-MM-DD
    section Phase 1: Foundation
    Network Schema Definition    :done, p1a, 2026-06-24, 1w
    API Endpoints               :done, p1b, after p1a, 1w
    Postgres Persistence        :active, p1c, after p1b, 1w
    API Tests                   :p1d, after p1c, 1w

    section Phase 2: Terraform
    Enhanced Renderer           :p2a, after p1d, 2w
    Network Component Placeholders :p2b, after p2a, 1w
    Terraform Generation API    :p2c, after p2b, 1w

    section Phase 3: Drag-Drop
    Install @dnd-kit            :p3a, after p2c, 1w
    Draggable Components        :p3b, after p3a, 1w
    Multi-select Support        :p3c, after p3b, 1w
    E2E Tests                   :p3d, after p3c, 1w

    section Phase 4: Priority 2
    Wave Planning               :p4a, after p3d, 2w
    Remediation Tracker         :p4b, after p4a, 2w
    Image Import Planning       :p4c, after p4b, 2w
    Migration Ops               :p4d, after p4c, 2w

    section Phase 5: Handoff
    Manifest Generation         :p5a, after p4d, 1w
    CSV Exports                 :p5b, after p5a, 1w
    Preflight Validation        :p5c, after p5b, 1w
    ZIP Packaging               :p5d, after p5c, 1w

    section Phase 6: Polish
    Clickable Diagram Nodes     :p6a, after p5d, 1w
    Performance Optimization    :p6b, after p6a, 1w
    Accessibility Audit         :p6c, after p6b, 1w
    Production Readiness        :p6d, after p6c, 1w
```

---

## 8. Promotion Gates Decision Tree

```mermaid
flowchart TD
    Start[Carbon UI Ready?] --> G1{Gate 1:<br/>Core Functionality}

    G1 -->|Pass| G2{Gate 2:<br/>Feature Parity}
    G1 -->|Fail| Fix1[Fix Core Issues]
    Fix1 --> G1

    G2 -->|Pass| G3{Gate 3:<br/>Network Planning}
    G2 -->|Fail| Fix2[Implement Missing Features]
    Fix2 --> G2

    G3 -->|Pass| G4{Gate 4:<br/>User Experience}
    G3 -->|Fail| Fix3[Complete Network Components]
    Fix3 --> G3

    G4 -->|Pass| G5{Gate 5:<br/>Quality & Testing}
    G4 -->|Fail| Fix4[Improve UX]
    Fix4 --> G4

    G5 -->|Pass| G6{Gate 6:<br/>Production Readiness}
    G5 -->|Fail| Fix5[Add Tests & Coverage]
    Fix5 --> G5

    G6 -->|Pass| Decision{Promotion<br/>Decision}
    G6 -->|Fail| Fix6[Production Hardening]
    Fix6 --> G6

    Decision -->|Go| Promote[Promote Carbon to Production]
    Decision -->|No-Go| Defer[Defer Promotion]

    Promote --> Monitor[Monitor & Iterate]
    Defer --> Reassess[Reassess in 3 Months]
    Reassess --> Start

    style Start fill:#0f62fe,color:#fff
    style Decision fill:#8a3ffc,color:#fff
    style Promote fill:#24a148,color:#fff
    style Defer fill:#fa4d56,color:#fff
```

---

## 9. Data Model: Network Planning State

```mermaid
classDiagram
    class NetworkPlanningState {
        +string version
        +VpcBucket[] vpcs
        +SubnetBucket[] subnets
        +SecurityBucket[] securityGroups
        +StorageBucket[] storageProfiles
        +WaveBucket[] waves
        +NetworkComponent[] networkComponents
        +VmNetworkAssignment[] vmAssignments
        +PlanningMetadata metadata
    }

    class VpcBucket {
        +string id
        +string name
        +string region
        +string addressPrefixMode
        +AddressPrefix[] addressPrefixes
        +Dict tags
        +string notes
    }

    class SubnetBucket {
        +string id
        +string name
        +string vpcId
        +string zone
        +string cidr
        +string purpose
        +boolean publicGateway
        +Dict tags
    }

    class SecurityBucket {
        +string id
        +string name
        +string vpcId
        +SecurityRule[] rules
        +Dict tags
    }

    class VmNetworkAssignment {
        +string vmKey
        +string primarySubnetId
        +string primarySecurityGroupId
        +SecondaryNic[] secondaryNics
        +string storageProfileId
        +string waveId
        +boolean excluded
    }

    class SecondaryNic {
        +string id
        +string subnetId
        +string securityGroupId
        +int order
    }

    NetworkPlanningState "1" --> "*" VpcBucket
    NetworkPlanningState "1" --> "*" SubnetBucket
    NetworkPlanningState "1" --> "*" SecurityBucket
    NetworkPlanningState "1" --> "*" VmNetworkAssignment
    VpcBucket "1" --> "*" SubnetBucket
    VpcBucket "1" --> "*" SecurityBucket
    SubnetBucket "1" --> "*" VmNetworkAssignment
    SecurityBucket "1" --> "*" VmNetworkAssignment
    VmNetworkAssignment "1" --> "*" SecondaryNic
```

---

## 10. Backward Compatibility Strategy

```mermaid
flowchart LR
    A[Terraform Renderer Call] --> B{carbon_network_plan<br/>provided?}

    B -->|Yes| C[Carbon UI Path]
    B -->|No| D[Streamlit Path]

    C --> E[render_networking_from_carbon_plan]
    C --> F[render_vsi_from_carbon_assignments]

    D --> G[render_networking_legacy]
    D --> H[render_vsi_templates]

    E --> I[VPC + Subnets + Security Groups<br/>+ Network Components]
    F --> J[VSI with Carbon Assignments]

    G --> K[VPC + Subnets + Security Groups<br/>from unique_nets]
    H --> L[VSI with RVTools NICs]

    I --> M[Terraform Modules]
    J --> M
    K --> M
    L --> M

    M --> N[Terraform ZIP Package]

    style C fill:#0f62fe,color:#fff
    style D fill:#24a148,color:#fff
    style M fill:#8a3ffc,color:#fff
```

---

## 11. API Endpoint Map

```mermaid
graph LR
    subgraph "Network Planning"
        A1[POST /api/projects/:id/network-plan]
        A2[GET /api/projects/:id/network-plan]
        A3[PUT /api/projects/:id/vm-assignments]
    end

    subgraph "Terraform Generation"
        B1[POST /api/projects/:id/terraform/generate]
        B2[GET /api/projects/:id/terraform/download/:artifact_id]
        B3[POST /api/projects/:id/terraform/validate]
    end

    subgraph "Project Management"
        C1[POST /api/projects]
        C2[GET /api/projects/:id]
        C3[PUT /api/projects/:id]
        C4[DELETE /api/projects/:id]
    end

    subgraph "Workbook Processing"
        D1[POST /api/workbook/upload]
        D2[GET /api/workbook/summary]
    end

    A1 --> DB[(Postgres)]
    A2 --> DB
    A3 --> DB
    B1 --> DB
    B1 --> Storage[Docker Volume]
    B2 --> Storage
    C1 --> DB
    C2 --> DB
    C3 --> DB
    C4 --> DB
    D1 --> Parser[RVTools Parser]
    D2 --> Parser

    style DB fill:#fa4d56,color:#fff
    style Storage fill:#8a3ffc,color:#fff
    style Parser fill:#24a148,color:#fff
```

---

## 12. Testing Strategy Pyramid

```mermaid
graph TB
    subgraph "Testing Pyramid"
        A[E2E Tests<br/>Playwright]
        B[Integration Tests<br/>API + DB]
        C[Unit Tests<br/>Components + Utils]
    end

    A --> B
    B --> C

    subgraph "E2E Coverage"
        E1[Upload Workbook]
        E2[Create Network Plan]
        E3[Assign VMs]
        E4[Generate Terraform]
        E5[Download Package]
    end

    subgraph "Integration Coverage"
        I1[API Endpoints]
        I2[Postgres Persistence]
        I3[Terraform Generation]
        I4[Handoff Package]
    end

    subgraph "Unit Coverage"
        U1[Network Validation]
        U2[CIDR Calculations]
        U3[Schema Conversion]
        U4[Drag-Drop Logic]
    end

    A -.-> E1
    A -.-> E2
    A -.-> E3
    A -.-> E4
    A -.-> E5

    B -.-> I1
    B -.-> I2
    B -.-> I3
    B -.-> I4

    C -.-> U1
    C -.-> U2
    C -.-> U3
    C -.-> U4

    style A fill:#fa4d56,color:#fff
    style B fill:#8a3ffc,color:#fff
    style C fill:#24a148,color:#fff
```

---

**Document Version**: 1.0
**Last Updated**: 2026-06-23
**Status**: Planning Phase
