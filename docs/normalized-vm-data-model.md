# Normalized VM Data Model

## Purpose
The normalized VM data model is the internal contract between RVTools parsing,
RVTools parsing, readiness assessment, cost/profile recommendation,
Terraform rendering, Streamlit display, and migration handoff generation.

Earlier app code passed Streamlit table dictionaries through most layers. The
current model keeps those dictionaries only at compatibility boundaries:
Streamlit `DataFrame` rows, generated CSV headers, existing manifest fields, and
tests that intentionally exercise legacy inputs.

## Canonical Records
`models.py` defines the canonical dataclasses:

- `MigrationVm`: top-level workload record.
- `SourceMetadata`: source VM identity, placement, disks, and NICs.
- `TargetRecommendation`: IBM profile, storage tier, subnet, security group,
  cost, and override context.
- `PricingMetadata`: pricing source, confidence, timestamp, and hourly profile
  rate.
- `ImageReadiness`: image planning status and supporting metadata.
- `MemoryReadiness`: memory pressure, constraints, and sizing recommendation.
- `MigrationReadiness`: operational migration status and detailed findings.
- `DiskMapping`, `PartitionMapping`, `NicMapping`, and `ReadinessFinding`:
  repeated nested details.

`MigrationVm` still exposes legacy top-level attributes for compatibility with
the current UI and existing tests. During initialization it refreshes the nested
records so application code can use typed fields while exports preserve the
established wire format.

## Compatibility Boundaries
`MigrationVm.from_record()` accepts existing table-style dictionaries with
headers such as `VM Name`, `IBM Profile`, `Disk Details`, and `Readiness
Findings`.

`MigrationVm.to_record()` returns the same table-style shape used by the
Streamlit data editor and current CSV/manifest generators. This prevents a data
model refactor from changing user-visible ZIP contents or UI columns.

Partition details are additive. Matched partitions are nested under their
source disk, while unmatched `vPartition` rows are preserved at the VM source
level for review.

`logic_engine.py` remains a compatibility facade for existing imports. The
focused implementation modules accept either `MigrationVm` instances or legacy
dictionaries where public rendering and handoff functions historically allowed
that shape. Inputs are normalized at the function boundary before rendering
Terraform or handoff outputs.

## Development Guidance
New parser or assessment code should construct or update `MigrationVm` and its
nested records directly. `rvtools_parser.py` owns workbook correlation,
`assessments.py` owns readiness policy, `sizing.py` owns profile/cost
recommendation, `terraform_renderer.py` owns HCL output, and `handoff.py` owns
manifest/CSV/runbook exports. Call `to_record()` only when handing data to
Streamlit or legacy export code.

New output adapters should accept `MigrationVm` objects and avoid depending on
Streamlit-specific column names except where a public CSV, manifest, or UI
contract already requires them.
