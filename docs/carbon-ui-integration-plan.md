# Carbon UI Integration Plan: Architecture Overview & Network Component Wiring

## Executive Summary

This document provides a comprehensive architecture overview and integration plan for the Carbon UI prototype, focusing on wiring network components into Terraform generation and achieving feature parity with the production Streamlit application.

**Status**: Planning Phase
**Target**: Carbon UI promotion to production-ready status
**Timeline**: Phased approach with incremental milestones (28 weeks)

---

## 1. Current Architecture Analysis

### 1.1 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Production: Streamlit (app.py + streamlit_app/)            │
│  - Full-featured workbench                                   │
│  - Upload, planning, persistence, Terraform generation       │
│  - Wave planning, remediation, image import                  │
│                                                              │
│  Prototype: Carbon UI (prototype/carbon-ui/)                 │
│  - Next.js + React + IBM Carbon Design System                │
│  - Workflow navigation, upload, VM assignment                │
│  - Resource buckets, network diagram (visualization only)    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     API/SERVICE LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Prototype (prototype/api/)                          │
│  - Workbook parsing via shared Python engine                 │
│  - Summary/readiness/assignment data endpoints               │
│  - Project state persistence to Postgres                     │
│  - Shared logic: rvtools_parser, assessments, sizing         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      DATA/LOGIC LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Core Python Modules:                                        │
│  - rvtools_parser.py + rvtools/ (workbook parsing)           │
│  - assessments.py (readiness evaluation)                     │
│  - sizing.py (profile matching)                              │
│  - terraform_renderer.py (HCL generation)                    │
│  - models/ (MigrationVm, network, storage, readiness)        │
│  - handoff/ (manifest, CSV exports, runbooks)                │
│                                                              │
│  Persistence:                                                │
│  - Postgres (project metadata, planning state JSON)          │
│  - Docker volumes (artifacts, workbooks)                     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Architectural Decisions

**Decision 1: Shared Backend Logic**
- Carbon UI does NOT fork or duplicate Python logic
- All parsing, readiness, sizing, and Terraform generation remains in shared modules
- FastAPI acts as the bridge between Carbon UI and Python engine

**Decision 2: Streamlit Remains Production**
- Streamlit is the supported application until Carbon meets promotion gates
- Carbon lives under `prototype/` to signal experimental status
- No long-lived forks; use feature branches and pull requests

**Decision 3: Postgres for Persistence**
- Project metadata and planning state stored in Postgres
- Both Streamlit and Carbon can save/load projects
- Planning state JSON is the interchange format

---

## 2. Current State Assessment

### 2.1 What Carbon UI Has Today

✅ **Implemented:**
- IBM Carbon Design System shell with workflow navigation
- Drag-and-drop RVTools workbook upload
- Estate summary dashboard (VMs, cost, savings, blockers)
- Readiness table with status indicators
- VM assignment workbench with checkbox/select controls
- Resource bucket creation (VPC, subnet, security, storage, wave)
- Network diagram visualization (mocked/planning model only)
- Project save/load through FastAPI/Postgres
- Playwright e2e smoke tests

### 2.2 What Carbon UI Lacks (vs. Streamlit)

❌ **Missing Critical Features:**
- **Terraform Generation**: No connection to `terraform_renderer.py`
- **Network Component Wiring**: Diagram is visualization-only, not Terraform-ready
- **True Drag-and-Drop**: Current assignment uses checkboxes, not drag-and-drop
- **Wave Planning**: No wave/cutover/owner/priority/dependency tracking
- **Remediation Tracker**: No blocker management with status/owner/due dates
- **Image Import Planning**: No image grouping or import status tracking
- **Migration Ops**: No cutover readiness view
- **Decision Audit**: No override tracking with pricing impact
- **Handoff Package**: No ZIP generation with manifest/CSVs/runbook
- **Preflight Validation**: No safety checks before package build
- **Planning State Restore**: Limited to Carbon-specific state, not full Streamlit parity

---

## 3. Network Component Integration Architecture

### 3.1 Current Network Model Gap

**Streamlit/Terraform Flow:**
```
RVTools vNetwork → parse_rvtools_workbook() → unique_nets[]
→ render_networking_templates() → VPC + Address Prefixes + Subnets + Security Groups
```

**Carbon UI Flow (Current):**
```
RVTools upload → FastAPI summary → Carbon state → Resource buckets (UI only)
→ Network diagram (visualization) → ❌ NO TERRAFORM OUTPUT
```

**The Gap:**
- Carbon creates VPC/subnet/security buckets in UI state
- These buckets are NOT wired to `terraform_renderer.py`
- Network diagram is a planning visualization, not a Terraform schema

### 3.2 Proposed Network Planning Schema

See detailed schema definitions in sections 3.2.1 and 3.2.2 below.

---

*This document continues with detailed technical specifications for network planning schemas, API endpoints, Terraform renderer enhancements, drag-and-drop architecture, feature parity roadmap, and promotion gates.*

*For the complete integration plan, see the following sections in this document.*
