# Carbon UI Integration Summary

## Quick Reference Guide

This document provides a concise summary of the Carbon UI integration plan. For detailed technical specifications, see [`carbon-ui-integration-plan.md`](./carbon-ui-integration-plan.md).

---

## 🎯 Integration Goals

1. **Wire Carbon network planning to Terraform generation**
2. **Implement true drag-and-drop VM assignment**
3. **Achieve feature parity with Streamlit**
4. **Enable Carbon UI as production-ready alternative**

---

## 🏗️ Architecture Overview

### Current State
- **Streamlit**: Production app with full Terraform generation
- **Carbon UI**: Prototype with real upload, persistence, network planning,
  Terraform ZIP export, and drag-and-drop assignment
- **FastAPI**: Shared backend for parsing, state management, Carbon network
  planning, VM assignment persistence, and Terraform generation
- **Gap**: Carbon still lacks several Streamlit-only planning workflows

### Target State
- **Carbon UI** → **FastAPI** → **Enhanced Terraform Renderer** → **Terraform ZIP**
- Network planning schema bridges UI state and Terraform generation
- Native drag-and-drop augments checkbox assignment
- Full handoff package with manifest, CSVs, runbook

---

## 🔑 Key Integration Points

### 1. Network Planning Schema

**Create stable schema for Terraform-ready network planning:**

```typescript
// Carbon UI (TypeScript)
type NetworkPlanningState = {
  vpcs: VpcBucket[];
  subnets: SubnetBucket[];
  securityGroups: SecurityBucket[];
  networkComponents: NetworkComponent[];
  vmAssignments: VmNetworkAssignment[];
};
```

```python
# Backend (Python)
@dataclass
class NetworkPlanningState:
    vpcs: List[VpcPlan]
    subnets: List[SubnetPlan]
    security_groups: List[SecurityGroupPlan]
    network_components: List[NetworkComponentPlan]
    vm_assignments: List[VmNetworkAssignment]
```

### 2. API Endpoints

**Implemented FastAPI endpoints:**

- `POST /api/projects/{id}/network-plan` - Save network planning state
- `GET /api/projects/{id}/network-plan` - Retrieve network planning state
- `POST /api/projects/{id}/terraform` - Generate and stream Terraform ZIP from Carbon state
- `PUT /api/projects/{id}/vm-assignments` - Update VM assignments from drag-and-drop

Still planned:
- Preflight/validation endpoint dedicated to Carbon UI feedback
- Artifact download endpoint for saved Terraform packages, if Carbon starts
  storing generated ZIPs server-side

### 3. Enhanced Terraform Renderer

**New rendering functions in `terraform_renderer.py`:**

```python
def render_networking_from_carbon_plan(
    network_plan: NetworkPlanningState,
    project_name: str,
    ssh_source_cidr: str,
) -> str:
    """Generate Terraform networking from Carbon UI planning state."""
    # VPC with manual address prefixes
    # Subnets with user-defined CIDRs
    # Security groups with custom rules
    # Public gateways, VPN gateways, load balancers (placeholders)
    # Route tables, ACLs, VPE gateways (placeholders)

def render_vsi_from_carbon_assignments(
    processed_vms: List[MigrationVm],
    network_plan: NetworkPlanningState,
    project_name: str,
) -> str:
    """Generate Terraform VSI from Carbon UI VM assignments."""
    # VSI resources with Carbon-assigned subnets
    # Primary + secondary NICs from assignments
    # Security group attachments
    # Volume attachments (unchanged)
```

**Backward compatibility maintained:**
```python
def render_networking_templates(
    unique_nets,
    vpc_name="my-vpc",
    carbon_network_plan=None,  # NEW: Optional Carbon state
):
    if carbon_network_plan:
        return render_networking_from_carbon_plan(carbon_network_plan, ...)
    else:
        return _render_networking_legacy(unique_nets, ...)  # Streamlit path
```

### 4. Drag-and-Drop Architecture

**Drag-and-drop uses native browser drag/drop components:**

```typescript
// prototype/carbon-ui/components/dnd/
DraggableVmRow
SubnetDropZone
PlacementModal
```

**Features:**
- Drag single or multiple VMs
- Drop onto target buckets (subnet, security group, storage, wave)
- Visual feedback during drag (drop zone highlighting)
- Validation (prevent invalid drops)
- Persist assignments via API

---

## 📋 Feature Parity Checklist

### Core Functionality
- [x] Upload and parse RVTools workbooks
- [x] Display estate summary and readiness
- [x] Save and load projects
- [x] Assign VMs to subnets/security/storage/waves
- [x] Generate Terraform packages
- [x] Download Terraform ZIP

### Priority 2 Features
- [x] Wave Planning initial workflow (wave, cutover group, owner, priority, dependency)
- [x] Remediation Tracker initial workflow (blocker status, owner, due dates)
- [x] Image Import Planning initial workflow (image grouping, import status)
- [x] Migration Ops initial workflow (cutover readiness view)
- [x] Decision Audit initial workflow (override tracking)
- [x] Decision Audit pricing impact columns in Carbon ZIP
- [ ] Complete handoff parity for remaining package files

### Network Planning
- [ ] VPC creation with address prefixes
- [ ] Subnet creation with custom CIDRs
- [ ] Security group creation with custom rules
- [ ] Public gateway support
- [ ] Network component placeholders (VPN, LB, VPE, floating IP, route tables, ACLs)
- [ ] Network diagram with clickable/editable nodes
- [x] Terraform generation from network plan

### Handoff Package
- [ ] Migration manifest JSON
- [ ] All CSV exports (vm-mapping, nic-mapping, disk-mapping, etc.)
- [ ] Migration runbook
- [x] Preflight validation endpoint, Export UI feedback, and workflow routing
- [x] Planning state JSON export/import in Carbon Export workflow
- [ ] Terraform ZIP packaging

---

## 🗓️ Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4) ✅
**Goal**: Establish network planning schema and API endpoints

**Tasks:**
- Define NetworkPlanningState schema (TypeScript + Python)
- Create Pydantic validation schemas
- Implement FastAPI endpoints for network plan CRUD
- Add network plan persistence to Postgres
- Write API tests

**Deliverables:**
- `models/network_planning.py`
- `prototype/api/schemas.py`
- Updated `prototype/api/app.py`

### Phase 2: Terraform Integration (Weeks 5-8) ✅
**Goal**: Wire Carbon network plans to Terraform generation

**Tasks:**
- Implement `render_networking_from_carbon_plan()`
- Implement `render_vsi_from_carbon_assignments()`
- Add network component placeholder renderers
- Create backward compatibility layer
- Implement Terraform generation API endpoint
- Add ZIP packaging logic

**Deliverables:**
- Enhanced `terraform_renderer.py`
- Terraform generation API endpoint
- Test coverage

### Phase 3: Drag-and-Drop UI (Weeks 9-12) ✅
**Goal**: Replace checkbox assignment with drag-and-drop

**Tasks:**
- Create native draggable VM rows
- Create droppable bucket zones
- Implement multi-select drag
- Add visual feedback
- Implement assignment persistence
- Write Playwright tests

**Deliverables:**
- `prototype/carbon-ui/components/dnd/DraggableVmRow.tsx`
- `prototype/carbon-ui/components/dnd/SubnetDropZone.tsx`
- `prototype/carbon-ui/components/dnd/PlacementModal.tsx`
- E2E tests covering multi-select DnD and autosave reload

### Phase 4: Priority 2 Features (Weeks 13-20)
**Goal**: Achieve feature parity with Streamlit Priority 2 features

**Tasks:**
- Wave Planning (Weeks 13-14)
- Remediation Tracker (Weeks 15-16)
- Image Import Planning (Weeks 17-18)
- Migration Ops (Weeks 19-20)

**Deliverables:**
- Complete Priority 2 feature set
- API endpoints for all features
- CSV export/import

### Phase 5: Handoff Package (Weeks 21-24)
**Goal**: Generate complete Terraform handoff packages

**Tasks:**
- Migration manifest generation
- All CSV exports
- Migration runbook
- Preflight validation endpoint, Export UI feedback, and workflow routing
- Decision audit export
- Planning state JSON export/import
- ZIP packaging

**Deliverables:**
- Complete Terraform ZIP with handoff files
- Download UI

### Phase 6: Polish & Promotion (Weeks 25-28)
**Goal**: Prepare Carbon UI for production promotion

**Tasks:**
- Clickable/editable diagram nodes
- Detail side panels
- Validation/preflight for network components
- Terraform preview in UI
- Performance optimization
- Accessibility audit
- Complete test suite
- Documentation
- User acceptance testing

**Deliverables:**
- Production-ready Carbon UI
- Promotion decision (Go/No-Go)

---

## 🚪 Promotion Gates

Carbon UI must meet these gates before replacing Streamlit:

### Gate 1: Core Functionality ✅/❌
- [ ] Upload and parse RVTools workbooks
- [ ] Display estate summary and readiness
- [ ] Save and load projects from Postgres
- [ ] Assign VMs to subnets/security/storage/waves
- [ ] Generate Terraform packages
- [ ] Download Terraform ZIP with handoff files

### Gate 2: Feature Parity ✅/❌
- [ ] All Streamlit tabs replicated
- [ ] Wave planning with conflict detection
- [ ] Remediation tracker
- [ ] Image import planning
- [ ] Migration Ops
- [ ] Decision audit
- [x] Planning state JSON export/import
- [ ] All CSV exports match Streamlit

### Gate 3: Network Planning ✅/❌
- [ ] VPC creation with address prefixes
- [ ] Subnet creation with custom CIDRs
- [ ] Security group creation with custom rules
- [ ] Public gateway support
- [ ] Network component placeholders
- [ ] Network diagram with clickable nodes
- [ ] Terraform generation from network plan

### Gate 4: User Experience ✅/❌
- [ ] Drag-and-drop VM assignment
- [ ] Multi-select operations
- [ ] Visual feedback and validation
- [ ] Performance (large workbooks >500 VMs)
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Mobile/tablet responsiveness

### Gate 5: Quality & Testing ✅/❌
- [ ] Unit test coverage >80%
- [ ] E2E test coverage for critical paths
- [ ] API integration tests
- [ ] Terraform generation tests
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Documentation complete

### Gate 6: Production Readiness ✅/❌
- [ ] Docker/Postgres runtime works without manual setup
- [ ] Error handling and logging
- [ ] Monitoring and observability
- [ ] Backup and recovery procedures
- [ ] User training materials
- [ ] Migration guide (Streamlit → Carbon)

---

## 🔧 Technical Decisions

### Decision 1: Shared Backend Logic
**Rationale**: Avoid code duplication, maintain single source of truth for parsing/sizing/Terraform logic

**Implementation**: FastAPI acts as bridge between Carbon UI and Python engine

### Decision 2: Network Planning Schema
**Rationale**: Need stable, Terraform-ready schema that bridges UI planning and HCL generation

**Implementation**: TypeScript schema in Carbon UI, Python dataclass in backend, Pydantic validation in API

### Decision 3: Backward Compatibility
**Rationale**: Streamlit must continue working while Carbon matures

**Implementation**: Enhanced Terraform renderer accepts optional `carbon_network_plan` parameter, falls back to legacy path if not provided

### Decision 4: Drag-and-Drop Library
**Rationale**: Need robust, accessible, well-maintained drag-and-drop solution

**Implementation**: Use `@dnd-kit` (modern, accessible, TypeScript-first, active maintenance)

### Decision 5: Incremental Promotion
**Rationale**: Reduce risk by validating each phase before proceeding

**Implementation**: 6-phase roadmap with clear gates, Go/No-Go decision at end

---

## 📚 Related Documentation

- **[Carbon UI Integration Plan](./carbon-ui-integration-plan.md)** - Detailed technical specifications
- **[Carbon React UI Strategy](./carbon-react-ui-strategy.md)** - Strategic direction and promotion gates
- **[Priority 2 Migration Planning](./PRIORITY2_MIGRATION_PLANNING.md)** - Feature requirements
- **[ADR-003: Manual Address Prefixing](./ADR-003:%20Manual%20Address%20Prefixing%20&%20IP.md)** - Network schema decisions
- **[Normalized VM Data Model](./normalized-vm-data-model.md)** - Internal data structures

---

## 🚀 Next Steps

### Immediate Actions (Week 1)
1. Review and approve this integration plan
2. Create GitHub project board with roadmap tasks
3. Set up feature branch: `feature/carbon-terraform-integration`
4. Define NetworkPlanningState schema (TypeScript + Python)
5. Create initial API endpoint stubs

### Short-term Goals (Weeks 2-4)
1. Complete Phase 1: Foundation
2. Implement network plan CRUD endpoints
3. Add Postgres persistence
4. Write API tests
5. Update Carbon UI to save/load network plans

### Medium-term Goals (Weeks 5-12)
1. Complete Phase 2: Terraform Integration
2. Complete Phase 3: Drag-and-Drop UI
3. Validate Terraform generation from Carbon state
4. User testing of drag-and-drop workflow

### Long-term Goals (Weeks 13-28)
1. Complete Phase 4: Priority 2 Features
2. Complete Phase 5: Handoff Package
3. Complete Phase 6: Polish & Promotion
4. Promotion decision and production cutover

---

## ❓ Open Questions

1. **Network Component Scope**: Which network components should be fully implemented vs. placeholders in Phase 2?
   - Recommendation: VPC, subnets, security groups, public gateways fully implemented; VPN, LB, VPE, ACLs as placeholders

2. **Drag-and-Drop UX**: Should we support drag-from-bucket-to-bucket reassignment, or only drag-from-unassigned-to-bucket?
   - Recommendation: Support both for flexibility

3. **Terraform Preview**: Should Carbon UI show Terraform preview before download, or only after download?
   - Recommendation: Show preview in UI for validation, similar to Streamlit's package contents preview

4. **Migration Path**: How do we migrate existing Streamlit users to Carbon UI?
   - Recommendation: Run both in parallel, provide migration guide, deprecate Streamlit after 3-6 months of Carbon stability

5. **Performance Target**: What's the acceptable performance for large workbooks (e.g., 1000+ VMs)?
   - Recommendation: <3s for initial load, <1s for drag-and-drop operations, <10s for Terraform generation

---

## 📞 Contact & Feedback

For questions or feedback on this integration plan:
- Review the detailed technical plan in `carbon-ui-integration-plan.md`
- Check existing ADRs for architectural decisions
- Create GitHub issues for specific implementation questions
- Use feature branch PRs for incremental reviews

---

**Document Version**: 1.1
**Last Updated**: 2026-06-26
**Status**: Phases 1-3 implemented and verified; Phase 4 parity planning next
**Next Review**: Promotion gate review
