# Development Log: Multi-Tab Contention & Network Schema Discovery

## Overview
Evolution from a single-tab compute calculator to a multi-tab correlation model and automated Landing Zone generator.

## Technical Goals
- [x] **Compute Phase**: Parse `vCPU` for performance metrics (Ready %, Co-Stop).
- [x] **Resilience Phase**: Parse `vHost` and `vCluster` for physical headroom (pCores, Total MHz).
- [x] **Network Phase**: Implement Dynamic Schema Discovery from `vNetwork` and `vNIC`.
- [x] **Logic Implementation**:
    - **Starving VM Detection**: If Ready % > 5%, override right-sizing for performance safety.
    - **Zombie VM Detection**: If Usage < 5% and Usage MHz < 100, flag for decommissioning.
    - **N+1 Cluster Resilience**: (Total Cluster MHz - Largest Host MHz) - Total Demand.
    - **VPC IP Mirroring**: Automated generation of Address Prefixes and Subnets using `manual` preference.
- [x] **Modular Architecture**: Transition to modular HCL output (Networking, Storage, VSI).

## Data Schema Correlation
- **vInfo**: Anchor (VM inventory, Powerstate, Network assignments).
- **vNetwork**: Networking metadata (VLAN IDs, IPv4 Gateways, Port Groups).
- **vCPU**: Performance telemetry (Contention, MHz demand, Limits).
- **vHost**: Infrastructure capacity (Physical Cores, Host Speed).
- **vDisk**: Storage inventory (Capacity, Aggregate VM disk demand).

## Milestones
### July 21, 2026: Carbon Guided Help Layer
- Added workflow-specific Carbon help controls that explain each step's
  purpose, completion criteria, common mistakes, and recommended next step.
- Added a separate Carbon user-guide route that can stay open while migration
  planners work through the app.
- Updated Carbon evaluation documentation and tests for the guided-help content.

### July 21, 2026: Carbon Dependency Security Maintenance
- Added scoped Carbon npm overrides for vulnerable transitive
  `brace-expansion` versions pulled through Jest tooling.
- Regenerated the Carbon lockfile and verified `npm audit` reports zero
  vulnerabilities.

### July 21, 2026: Python Dependency Security Floors
- Added explicit Python dependency floors for resolved transitive packages with
  current security fixes: GitPython, idna, Pillow, PyJWT, Tornado, and urllib3.
- Updated a Carbon handoff parity fixture date so the non-overdue remediation
  assertion remains stable as calendar time advances.
- Verified both `pip-audit` local and requirements-file audits report no known
  vulnerabilities.

### July 21, 2026: Python Warning Compatibility Cleanup
- Replaced Carbon API, network-planning model, and affected test
  `datetime.utcnow()` calls with timezone-aware UTC timestamp generation while
  preserving the existing legacy timestamp string format.
- Added the `httpx2` test dependency so FastAPI/Starlette `TestClient` no
  longer falls back to the deprecated `httpx` path.

### July 15, 2026: Carbon Manual UAT Packet
- Added a reviewer-ready Carbon manual UAT runbook covering setup, workbook
  selection, review sequence, accessibility checks, evidence capture, pass/fail
  rules, and sensitive-data guardrails.
- Linked the runbook from the Carbon checklist, results template, promotion
  cutover guide, and implementation status.

### July 15, 2026: Carbon Network Plan Accessibility/UAT Evidence
- Added focused accessibility/UAT evidence for Network Plan component editing
  and local validation findings.
- Named the Network Plan validation panel as an accessible region and gave
  component edit actions explicit target-specific labels.
- Updated the Carbon checklist, results template, implementation status, and
  promotion evidence references while keeping full human UAT sign-off open.

### July 15, 2026: Carbon Network Validation Depth
- Added structured Carbon network validation findings for missing VPC
  references, missing or invalid subnet CIDRs, component attachment warnings,
  and duplicate Terraform labels.
- Rendered a compact Network Plan validation panel so users can review local
  blockers and warnings before Export preflight and Terraform package build.
- Added focused utility and workflow tests while preserving the saved
  `network-plan.json` contract.

### July 15, 2026: Carbon Network Component Edit Depth
- Added a Network Plan diagram edit affordance for existing network components
  that opens the shared component modal with the selected component values.
- Updated the component save path so existing network components are updated in
  place instead of duplicated, preserving the saved `network-plan.json` shape.
- Added focused Carbon workflow tests for opening component edits from the
  diagram and saving edits through the shared modal.

### July 15, 2026: Carbon Streamlit Parity Roadmap
- Added a Carbon-to-Streamlit parity roadmap that turns promotion gates into
  prioritized implementation branches.
- Clarified that Carbon has moved beyond basic prototype viability but should
  not replace Streamlit until real-workbook parity, accessibility/UAT evidence,
  and production operations evidence are complete.
- Linked the roadmap from the Carbon strategy, promotion guide, Carbon README,
  and root README.

### July 15, 2026: Carbon Real-Workbook API ZIP Parity
- Added a workshop-workbook FastAPI Terraform ZIP parity test that exercises
  the larger sample through the same backend package path Carbon users invoke.
- Verified representative operational handoff evidence for overrides,
  exclusions, remediation, image import status, cutover blockers, planning
  state, and saved network-plan state.

### July 15, 2026: Carbon Failure-Path Hardening
- Added focused Export workflow unit coverage for backend preflight failures,
  save-before-preview failures, and Terraform ZIP generation failures.
- Verified Carbon surfaces backend errors, avoids stale success UI, and does
  not call later backend export steps after an earlier save failure.

### July 15, 2026: Carbon Planning-State Import Failure Coverage
- Added Export workflow coverage for malformed planning-state JSON and
  incomplete planning-state schemas.
- Verified bad imports surface user-visible errors without replacing the
  current valid exportable project state.

### July 15, 2026: Carbon Workbook Upload Failure Coverage
- Added Intake workflow coverage for workbook parser/API upload failures.
- Verified failed uploads preserve the current workbook state and successful
  retries clear stale upload errors before loading the new workbook summary.

### June 22, 2026: Registry, Persistent Compose, and Carbon Prototype
- Added a GHCR publishing path for prebuilt Docker images while preserving local Docker builds.
- Added a Docker Compose stack with Streamlit, an experimental FastAPI service, Postgres, and artifact storage volumes for persistent project evaluation.
- Added a thin FastAPI prototype that reuses the existing RVTools parser and summary logic for a real workbook upload/readiness summary endpoint.
- Added an experimental Next.js/Carbon UI prototype with an IBM Cloud-style shell, drag-and-drop upload, dashboard metrics, readiness table, and mocked deeper planning panels.
- Documented the prebuilt image, persistent Compose path, and prototype boundaries while keeping Streamlit as the supported production workbench.

### May 5, 2026: Dynamic Networking & Modular HCL
- Resolved `KeyError` issues via dynamic column discovery for non-standard RVTools exports.
- Implemented automated CIDR extraction from `vNetwork` IPv4 column.
- Developed modular Terraform bundle generator (ZIP) for tiered storage and networking.
- Finalized PEP 8 compliance across `app.py` and `logic_engine.py`.

### May 6, 2026: Business Case Enhancements
- Added Streamlit dashboard savings metric and monthly savings aggregation.
- Exposed subnet/security group mapping values in the UI.
- Included mapping fields and baseline cost data in the business-case CSV export.
- Added user override support for IBM Profile and Storage Tier in the Streamlit data editor, with values honored during Terraform generation.
- Added Terraform override controls for VPC name, address prefix strategy, custom CIDRs, and deployment target selection.
- Added conditional backend behavior for Plain CLI vs IBM Schematics deployments.


### May 11, 2026: Migration Handoff Package
- Added a generated `migration-manifest.json` file to the Terraform ZIP bundle for tool-neutral source-to-target mapping.
- Added `vm-mapping.csv` for migration team review and customer workshop planning.
- Added `image-import-variables.tfvars.example` to capture IBM Cloud VPC custom image IDs after image import.
- Added `migration-runbook.md` to guide image staging, Terraform apply, validation, and cutover activities.
- Enriched per-VM processing with source IP, guest OS, disk count, host, cluster, datacenter, and power state metadata.
- Documented the handoff package in the README, dedicated user guide, and ADR-004.

### May 11, 2026: Image Readiness Assessment
- Added advisory `Ready`, `Review`, and `Blocked` image readiness statuses for IBM Cloud VPC custom image planning.
- Added firmware, boot disk size, guest customization, and readiness reason fields to the Streamlit table.
- Added dashboard metrics for image-ready, image-review, and image-blocked VM counts.
- Extended `migration-manifest.json`, `vm-mapping.csv`, and `migration-runbook.md` with image readiness data.
- Documented the assessment in the README, migration handoff guide, image readiness guide, and ADR-005.

### May 11, 2026: Per-Disk Volume Mapping
- Added RVTools `vDisk` detail preservation for boot/data disk planning.
- Changed generated storage from one aggregate volume per VM to one IBM Cloud block volume per non-boot data disk.
- Added VSI volume attachment generation using storage module outputs passed into the VSI module.
- Added `disk-mapping.csv` to the Terraform ZIP for source disk to target volume/attachment review.
- Extended the migration manifest with source disk metadata and target data volume planning fields.
- Documented the disk mapping behavior in the README, migration handoff guide, Terraform override notes, and ADR-006.

### May 11, 2026: Multi-NIC Network Mapping
- Added RVTools `vNetwork` detail preservation for per-VM NIC planning.
- Changed VSI Terraform generation to render the first connected NIC as primary and additional connected NICs as secondary network interfaces.
- Added `nic-mapping.csv` to the Terraform ZIP for primary, secondary, and disconnected NIC review.
- Extended the migration manifest with per-NIC source network, IP, MAC, adapter, switch, and connected-state metadata.
- Documented multi-NIC behavior in the README, migration handoff guide, Terraform override notes, and ADR-007.

### May 11, 2026: Migration Readiness Expansion
- Added advisory `Ready`, `Review`, and `Blocked` migration readiness statuses using RVTools `vSnapshot`, `vTools`, `vCD`, `vUSB`, and `vHealth` data when present.
- Added dashboard metrics and table fields for migration readiness, snapshot count/size, VMware Tools status, mounted media, USB device count, and health warning count.
- Added `readiness-findings.csv` to the Terraform ZIP for row-level remediation planning.
- Extended `migration-manifest.json`, `vm-mapping.csv`, and `migration-runbook.md` with migration readiness findings.
- Documented the assessment in the README, migration handoff guide, Terraform override notes, dedicated migration readiness guide, and ADR-008.

### May 11, 2026: Memory Readiness and Sizing
- Added RVTools `vMemory` parsing for active, consumed, ballooned, swapped, reservation, limit, and hot-add telemetry.
- Added advisory `Ready`, `Review`, and `Blocked` memory readiness statuses.
- Updated IBM Cloud profile sizing to use conservative memory guidance while preserving configured memory under pressure, reservations, or limits.
- Added dashboard metrics and disabled table fields for memory readiness and sizing basis.
- Added `memory-readiness.csv` to the Terraform ZIP and extended `migration-manifest.json`, `vm-mapping.csv`, and `migration-runbook.md`.
- Documented the feature in the README, user manual, right-sizing logic, migration handoff guide, Terraform override notes, memory readiness guide, and ADR-009.

### May 12, 2026: IBM Catalog Pricing Modes
- Added `catalog_pricing.py` to separate static, cached, and live IBM Cloud profile/pricing behavior.
- Added Pricing Mode controls to the Streamlit sidebar.
- Added pricing source, confidence, last-updated timestamp, and profile hourly fields to the table, manifest, and VM mapping CSV.
- Preserved offline/static fallback behavior so demos and local assessment work do not require IBM credentials.
- Added tests for static fallback, cached pricing, and live-mode fallback without an API key.
- Documented the design in the README, user manual, right-sizing logic, pricing guide, and ADR-010.

### May 12, 2026: Normalized VM Data Model
- Expanded `models.py` into the canonical internal VM dataclass model with nested source, target, pricing, image, memory, migration, disk, NIC, and readiness finding records.
- Updated the Streamlit processing path to build `MigrationVm` objects before converting to table rows at the UI boundary.
- Preserved current CSV, manifest, Terraform ZIP, and UI table contracts through `from_record()` and `to_record()` compatibility adapters.
- Moved old pricing API and Jinja template experiments into `experiments/` so production root files and smoke tests stay focused.
- Documented the model in `docs/normalized-vm-data-model.md` and ADR-011.

### May 13, 2026: Task 1 Module Split
- Split the Streamlit application and logic engine into focused parser, assessment, sizing, Terraform renderer, handoff, and UI helper modules.
- Kept `logic_engine.py` as a compatibility facade so existing tests and callers continue to use the same public imports.
- Preserved current Streamlit columns, CSV headers, manifest structure, Terraform ZIP layout, and generated file names.
- Added ADR-012 to document the module split and no-new-dependency decision.

### May 13, 2026: Assessment Workbench UI
- Reframed the Streamlit UI around focused Overview, Readiness, VM Review, Networks, Storage, and Export tabs.
- Reduced the default VM table to decision-oriented columns while keeping advanced generated fields available for audit.
- Moved readiness guidance next to the readiness triage view and moved package controls into the Export workflow.

### May 13, 2026: Assessment Quality Report
- Added RVTools worksheet coverage and confidence reporting for required and optional assessment tabs.

### June 2, 2026: Streamlit App Helper Split
- Extracted page header rendering, sidebar settings, and remediation backlog rendering into focused `streamlit_app/` modules while keeping `app.py` as the Streamlit entrypoint.
- Added focused tests for remediation backlog row generation and edit persistence.
- Updated CI actions to Node 24-compatible action versions and retained pytest log artifacts only for failed runs.

### June 2, 2026: Wave Planning Helper Split
- Extracted Wave Planning rendering and helper logic into `streamlit_app/wave_planning.py`.
- Added focused tests for active VM filtering, bulk wave assignment, editor persistence, conflict detection, and completion counts.
- Updated README and planning/user documentation to reflect the current Wave Planning tab and focused Streamlit helper layout.

### June 2, 2026: Image Import Helper Split
- Extracted Image Import Planning rendering and bulk status handling into `streamlit_app/image_import.py`.
- Preserved existing image import session-state keys, CSV export behavior, and handoff package inputs.
- Added focused coverage for bulk image import status updates.

### June 2, 2026: Export Tab Helper Split
- Extracted Export tab package controls, preflight rendering, business case download, and Terraform bundle build/download behavior into `streamlit_app/export.py`.
- Kept `app.py` focused on upload, parsing, tab composition, and renderer delegation.
- Added focused coverage for Export tab package summary metrics.

### June 2, 2026: Network and Storage Helper Split
- Extracted Network and Storage tab rendering plus source NIC/partition planning row builders into `streamlit_app/network_storage.py`.
- Kept `ui.py` compatibility exports for existing callers while moving tab ownership into the focused Streamlit helper package.
- Added focused coverage for switch/port context rows and partition planning summaries.

### June 2, 2026: Overview and Readiness Helper Split
- Extracted estate summary, Overview tab, assessment quality, readiness triage, and readiness legend rendering into `streamlit_app/overview_readiness.py`.
- Kept `ui.py` compatibility exports for existing callers while reducing inline tab ownership in `app.py`.
- Added focused coverage for estate summary and Overview blocker metrics.

### June 2, 2026: VM Review Helper Split
- Extracted VM Review tab decision editing and advanced generated field rendering into `streamlit_app/vm_review.py`.

### June 3, 2026: Export Tab Workflow Polish
- Grouped Export tab controls into package settings, subnet CIDRs, package summary, planning downloads, preflight review, and build/download sections.
- Preserved existing business case download, planning-state controls, preflight behavior, Terraform ZIP build path, and generated package outputs.
- Updated README, user manual, and testing checklist to describe the organized Export workflow.

### June 4, 2026: Deployment Readiness
- Added Docker and Streamlit configuration for local container runs and hosted container platforms.
- Added deployment guidance for IBM Cloud Code Engine, local Docker validation, and sensitive RVTools data handling.
- Updated README, user manual, and testing checklist with deployment references and container validation steps.

### June 4, 2026: Container CI Smoke Test
- Added a GitHub Actions container smoke job that builds the Docker image, starts the Streamlit container, and checks the health endpoint.
- Added failure logging and always-on container cleanup for the CI smoke run.
- Updated the testing guide to note automated container validation.

### June 4, 2026: Deployment Documentation Hardening
- Clarified local Streamlit, local container, hosted private container, static HTML landing page, and full web app rewrite deployment options.
- Tightened IBM Cloud Code Engine notes for port selection, private visibility, and access-control expectations.
- Expanded RVTools data-security guidance for uploads, generated packages, secrets, downloads, retention, and source uploads.

### June 4, 2026: Quick Start Runbook
- Added a README Quick Start with Python, Docker, and Makefile paths for first-time users.
- Added `Makefile` shortcuts for running, testing, compiling, Docker build/run, container health checks, and Terraform validation.
- Updated the user manual, deployment guide, and testing guide with the simplified run commands.

### June 4, 2026: Upload and Export Data Handling Notices
- Added non-blocking sidebar guidance before RVTools upload to remind users that workbooks can contain sensitive infrastructure inventory.
- Added Export tab guidance before planning downloads to remind users that CSVs, planning state, and Terraform packages can contain sensitive migration data.
- Updated the user manual to mention the in-app data-handling reminders.

### June 4, 2026: First-Run Readiness Check
- Standardized first-run Streamlit launch commands on `python -m streamlit run app.py` so users do not need Streamlit on their shell path.
- Added stop-app guidance for first-time local runs.
- Rechecked the advertised Makefile and Docker quick-start commands.

### June 4, 2026: Sample Workbooks and Usability Help
- Added tracked RVTools sample workbooks under `samples/`, including a generated small complete workbook and a larger workshop workbook for realistic findings.
- Added a sample workbook generator and Makefile target for regenerating the small workbook.
- Added hover help to key sidebar, wave planning, image import, VM Review, and Export controls.
- Clarified disconnected-NIC preflight guidance so users know to correct source RVTools/vSphere data or exclude the VM.
- Updated README, user manual, testing guide, and sample folder documentation for first-run testing.

### June 4, 2026: Guided Migration Assistant
- Added a Guided Migration Assistant to the Overview tab with a first-run checklist, migration action-plan export, and conservative safe-default automation.
- Safe defaults initialize blank image import statuses to `Pending` and create open remediation tracker rows without changing profiles, subnets, image import completion, Terraform output, or package scope.
- Added an explicit optional action to queue exclusions for hard-blocked VMs through the existing VM Review quick-fix flow.
- Updated README, user manual, testing guide, and migration planning documentation.

### June 9, 2026: Planning State Persistence Polish
- Added VM decision fields to reloadable planning-state exports so exclusions, target network placement, security group, subnet, and override decisions can be restored.
- Added planning-state summary and restore summary UI for VM decisions, wave rows, remediation tracker items, image import groups, and skipped rows.
- Added a Guided Migration Assistant reminder to download planning state before closing the app.
- Updated README, user manual, testing guide, and migration handoff documentation.

### June 12, 2026: Terraform Operator Readiness
- Added a generated root `README.md` to Terraform ZIP bundles with local CLI and IBM Schematics operator guidance.
- Documented required review files, custom image ID varfile steps, manual inputs, and automation boundaries for Terraform operators.
- Added an Export tab note after successful package build so users know operator instructions are included.
- Updated README, user manual, testing guide, and migration handoff documentation.

### June 15, 2026: Streamlit Width Compatibility
- Replaced deprecated Streamlit `use_container_width` calls with the current `width` argument across the app UI.
- Preserved existing tab layout, labels, generated exports, Terraform package contents, and session-state behavior.

### June 16, 2026: Terraform Validation Resilience
- Added provider registry/download failure detection to the Terraform package validation script.
- Kept strict `--init-validate` behavior for CI while adding an explicit local `--allow-provider-download-failure` escape hatch.
- Documented VPN, proxy, DNS, and Terraform Registry troubleshooting guidance for local validation.

### June 16, 2026: Export Validation Visibility
- Added Export tab guidance that distinguishes app preflight, offline Terraform format checks, strict init validation, and local provider-download tolerance.
- Added the same validation-mode guidance to the generated Terraform operator README.
- Updated user-facing documentation without changing generated Terraform resources or ZIP layout.

### June 17, 2026: Guided Sample Workbook Mode
- Added a sidebar `Load Sample Workbook` action for first-run testing with the bundled small RVTools sample.
- Kept uploaded RVTools workbooks higher priority than the bundled sample.
- Updated testing and user documentation for the guided sample workflow.

### June 17, 2026: In-App Help And Samples Panel
- Added a sidebar `Help And Samples` panel that explains the bundled samples, recommended workflow, documentation references, and Terraform execution boundary.
- Kept the panel informational only, with no changes to parsing, planning state, Terraform generation, or handoff outputs.
- Updated first-run, testing, and sample documentation for the new onboarding panel.

### June 17, 2026: Preflight Quick Fix Guidance
- Added `Fix Category` routing to preflight findings so blockers and warnings point to source RVTools/vSphere fixes, app planning updates, exclusion, or Terraform operator review.
- Surfaced fix category summaries in the Export tab preflight review and preserved existing quick-fix behavior.
- Updated handoff and testing documentation for the clearer preflight report guidance.

### June 17, 2026: Sample Findings Walkthrough
- Added a sample findings walkthrough for the larger workshop workbook so expected warnings and blockers are distinguishable from app defects.
- Surfaced workshop practice findings in the sidebar `Help And Samples` panel.
- Updated first-run, testing, and samples documentation to reference the walkthrough.

### June 18, 2026: Planning State Session Safety
- Added Export tab session-safety guidance that explains what planning-state JSON restores and what remains session-only.
- Added an Overview reminder when the current session has planning data worth saving.
- Updated planning persistence documentation to prefer planning-state JSON for full app resume while preserving CSV exchange workflows.

### June 18, 2026: Export Bundle Contents Preview
- Added a read-only Export tab preview of major Terraform ZIP files, purposes, and primary owners before package build.
- Kept generated Terraform, ZIP layout, manifest schema, CSV headers, and session-state behavior unchanged.
- Updated user, testing, and handoff documentation for the new preview section.

### June 18, 2026: Export Build Readiness Checklist
- Added an informational Export tab checklist for readiness blockers, wave planning, image import status, planning-state/session safety, and package preflight.
- Added Ready, Review, and Blocked summary counters above the checklist for faster scanning.
- Preserved preflight as the only package build gate and left generated Terraform and handoff outputs unchanged.
- Added focused tests and documentation for the checklist behavior.

### June 3, 2026: Migration Ops Readiness
- Added the Migration Ops tab for cutover readiness by wave and cutover group.
- Added `cutover-readiness.csv` to the Terraform handoff ZIP and manifest file references.
- Updated the generated runbook and documentation to include cutover readiness review.
- Preserved the `vm_decision_editor` session key, decision column order, disabled column behavior, and preflight quick-fix application.
- Added focused coverage for VM Review decision column selection helpers.

### June 3, 2026: Planning State CSV Reload
- Added remediation backlog CSV reload support for restoring owner, status, due date, and notes in later sessions.
- Added Image Import Planning CSV reload support for restoring catalog IDs, import status, timing, and notes.
- Updated README, user manual, and Priority 2 planning docs to describe export-and-reload workflows.

### June 3, 2026: Planning State Bundle
- Added reloadable `planning-state.json` export/import support for wave planning, remediation tracker, and image import status.
- Included `planning-state.json` in the Terraform handoff ZIP and manifest file references.
- Added focused tests for planning-state JSON generation, loading, dataframe restore, and package inclusion.

### June 3, 2026: Wave Planning CSV Import/Export
- Added standalone `wave-planning.csv` download and reload controls to the Wave Planning tab.
- Added focused helper coverage for stable export columns, matching by VM key, and skipped unmatched rows.
- Updated README, user manual, and Priority 2 planning docs for standalone wave planning exchange workflows.

### June 3, 2026: RVTools Parser Helper Split
- Extracted RVTools workbook sheet loading and column cleanup into `rvtools/workbook.py`.
- Extracted disk and partition inventory building into `rvtools/storage.py`.
- Kept `rvtools_parser.py` as the public compatibility facade and exported the focused helpers from `rvtools/`.
- Added focused coverage for missing sheet handling, column normalization, storage inventory behavior, and package import compatibility.

### June 2, 2026: Assessment Quality Report Follow-Up
- Added Overview tab quality metrics and worksheet coverage detail.
- Added `assessment-quality.json` and `assessment-quality.csv` to the Terraform ZIP and migration manifest.
- Documented the advisory quality model in the README, user manual, migration handoff guide, and ADR-013.

### May 13, 2026: vPartition Storage Planning
- Added advisory RVTools `vPartition` parsing and disk-key correlation.
- Preserved matched partition details on disk records and unmatched rows at VM level for review.
- Added Storage tab partition coverage signals and `partition-mapping.csv`.
- Extended disk mapping and manifest outputs with additive partition context without changing Terraform volume sizing.
- Documented the advisory partition model in the README, user manual, storage logic, handoff guide, and ADR-014.

### May 13, 2026: Network Readiness From Switch and Port Context
- Added optional RVTools `vPort`, `dvPort`, `vSwitch`, and `dvSwitch` parsing for advisory network readiness.
- Enriched per-NIC records with switch type, port group, VLAN/segment, port key, backing source tab, and match confidence.
- Added Network readiness to the Streamlit readiness triage, Network Planning view, VM mapping CSV, NIC mapping CSV, and migration manifest.
- Preserved Terraform primary/secondary/disconnected NIC behavior; switch and port context does not alter generated resources.
- Documented the advisory network readiness model in the README, user manual, handoff guide, normalized model guide, dedicated network readiness guide, and ADR-015.
