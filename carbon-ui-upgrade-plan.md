# Carbon UI Upgrade Plan

## Overview

Upgrade the Carbon UI prototype from a mostly-mocked shell into a fully functional
IBM Cloud-style migration workbench that can replace the Streamlit app. The work
proceeds in three sequential phases: component architecture, API wiring, and
drag-and-drop assignment.

**Branch:** `feature/carbon-ui-network-planning-phase1`
**App entry point:** `prototype/carbon-ui/app/page.tsx` (1,856 lines, monolithic)
**Backend:** FastAPI + Postgres + modular Terraform renderer — fully implemented
and tested. No backend changes required for Phases 1–3.

**Current state of the Carbon UI:**
- 8 workflow tabs rendered from a single file
- API calls for health, upload, project CRUD, and Terraform generation already
  exist and use snake_case JSON bodies correctly
- Network plan save, VM assignment persistence, and drag-and-drop are mocked
- No `components/` directory exists yet
- `types/network-planning.ts` is complete but the inline types in `page.tsx`
  partially duplicate it

**Goal:** After all three phases, Carbon UI satisfies promotion Gates 1–4
(upload/parse, save/load projects, core workflows, interactive VM assignment).

---

## Resolved Design Decisions

**API field naming:** The existing `page.tsx` already sends snake_case JSON
bodies to the API. This is correct and consistent with the Python test fixtures.
All new components will continue using snake_case for API payloads and camelCase
for React state/TypeScript interfaces (matching the existing pattern).

**Type consolidation:** `page.tsx` defines local types (`VpcBucket`, `SubnetBucket`,
`AssignmentVm`, etc.) that partially duplicate `types/network-planning.ts`. Phase 1
will move the authoritative versions to `types/` and remove the inline duplicates.
The richer `VmNetworkAssignment` from `types/network-planning.ts` will replace the
simpler `AssignmentVm` inline type.

**Test environment:** `jest.config.js` already lists `components/**/*.tsx` in
`collectCoverageFrom` (coverage threshold: 70%) but uses `testEnvironment: 'node'`.
Phase 1 must update Jest to use `@testing-library/react` with `jsdom` so extracted
components can be unit tested. New component tests go in `__tests__/components/`.

---

## Phase 1 — Full Component Architecture Split

### Intent
Decompose `app/page.tsx` into a clean, maintainable component architecture.
No user-visible behaviour changes. This is the structural foundation that makes
Phases 2 and 3 maintainable.

### Expected Outcomes
- `app/page.tsx` is a thin shell (~120 lines) that composes the Carbon shell
  layout, provides context, and renders the active workflow component
- 8 workflow components in `components/workflows/`
- Shared UI primitives in `components/ui/`
- All API `fetch()` calls in `hooks/useApi.ts` with typed return types
- Shared app state in `store/AppContext.tsx` via React context
- Duplicate inline types removed from `page.tsx`; `types/` is the single source
- Jest updated to support React component tests; new unit tests for each
  extracted component at 70% coverage minimum

### Directory Structure After Phase 1

```
prototype/carbon-ui/
├── app/
│   ├── layout.tsx                          (unchanged)
│   ├── page.tsx                            (thin shell, ~120 lines)
│   └── styles.css                          (unchanged)
├── components/
│   ├── ui/
│   │   ├── MetricTile.tsx                  (estate metric card)
│   │   ├── ReadinessTag.tsx                (Blocked/Review/Ready badge)
│   │   ├── BucketCard.tsx                  (resource bucket container)
│   │   └── VmRow.tsx                       (single VM table row)
│   └── workflows/
│       ├── OverviewWorkflow.tsx            (estate summary + saved projects)
│       ├── IntakeWorkflow.tsx              (file upload + workbook summary)
│       ├── AssignmentWorkflow.tsx          (VM table + bucket assignment)
│       ├── NetworkPlanWorkflow.tsx         (VPC/subnet form + topology view)
│       ├── SecurityWorkflow.tsx            (security group buckets)
│       ├── StorageWorkflow.tsx             (storage profile buckets)
│       ├── WavesWorkflow.tsx               (wave buckets)
│       └── ExportWorkflow.tsx              (Terraform generation + download)
├── hooks/
│   └── useApi.ts                           (all fetch() calls, typed)
├── store/
│   └── AppContext.tsx                      (React context + reducer)
├── types/
│   └── network-planning.ts                 (consolidated — add missing types)
├── utils/
│   └── network-validation.ts               (unchanged)
└── __tests__/
    ├── network-planning.test.ts            (unchanged — 18 existing tests)
    ├── network-validation.test.ts          (unchanged — 30 existing tests)
    └── components/
        ├── MetricTile.test.tsx
        ├── ReadinessTag.test.tsx
        ├── BucketCard.test.tsx
        ├── VmRow.test.tsx
        ├── OverviewWorkflow.test.tsx
        ├── IntakeWorkflow.test.tsx
        └── AssignmentWorkflow.test.tsx     (core workflow, highest value)
```

### Todo List

1. **Update Jest for React component testing:**
   - Install `@testing-library/react`, `@testing-library/jest-dom`,
     `@testing-library/user-event`, and `jest-environment-jsdom`
   - Update `jest.config.js`: change `testEnvironment` to `jsdom`, add
     `setupFilesAfterFramework` for `@testing-library/jest-dom` matchers
   - Add `@types/jest` to devDependencies

2. **Consolidate types in `types/network-planning.ts`:**
   - Add the types currently defined only inline in `page.tsx`:
     `EstateSummary`, `WorkbookSummary`, `SavedProject`, `SavedProjectState`,
     `AssignmentVm` (merge with `VmNetworkAssignment`), `ResourceState`,
     `AssignmentMode`, `Workflow`
   - Remove the duplicates from `page.tsx` once components import from `types/`
   - Keep all existing types in `types/network-planning.ts` unchanged

3. **Create `store/AppContext.tsx`:**
   - Define `AppState` interface covering all 26 `useState` variables from
     `page.tsx` (grouped by concern: upload state, project state, UI state,
     resource state, assignment state)
   - Implement `AppReducer` with typed action union
   - Export `AppProvider` (wraps children) and `useAppState()` hook
   - Move `defaultResources` and `sampleRows` constants into the context module

4. **Create `hooks/useApi.ts`:**
   - Extract all `fetch()` calls from `page.tsx` into named async functions:
     `checkApiHealth`, `uploadWorkbook`, `listProjects`, `createProject`,
     `updateProject`, `deleteProject`, `loadProject`, `saveProjectState`,
     `saveNetworkPlan`, `loadNetworkPlan`, `updateVmAssignments`,
     `generateTerraform`
   - Each function reads `process.env.NEXT_PUBLIC_API_BASE_URL` (already
     rewritten by `next.config.mjs`, so relative `/api/` paths work in browser)
   - Return typed objects matching the existing API response shapes
   - Keep snake_case JSON bodies (already the correct convention)

5. **Create `components/ui/` primitives:**
   - `MetricTile.tsx` — props: `{ value: number | string; label: string; unit?: string }`
   - `ReadinessTag.tsx` — props: `{ status: 'Blocked' | 'Review' | 'Ready' | string }`
   - `BucketCard.tsx` — props: `{ title: string; subtitle?: string; items: string[]; onAdd?: () => void }`
   - `VmRow.tsx` — props: `{ vm: AssignmentVm; selected: boolean; onToggle: () => void }`

6. **Extract workflow components (one per tab):**
   - Each component receives its slice of `AppState` via `useAppState()` and
     calls `useApi` functions
   - Modals that are scoped to a single workflow move into that workflow's file
   - The shared bucket-creation modal stays in `AssignmentWorkflow.tsx` since
     it's used across subnet, security, storage, and wave creation
   - Move `renderNetworkPlan`, `renderExportReadiness`, etc. functions into the
     corresponding workflow component files

7. **Reduce `app/page.tsx` to thin shell:**
   - Keep: Carbon `Header`, `SideNav`, `Content` layout skeleton
   - Keep: workflow navigation `useState` and tab switch handler
   - Remove: all state except `activeWorkflow` (moved to `AppContext`)
   - Add: `<AppProvider>` wrapper
   - Add: `switch (activeWorkflow)` that renders the active workflow component

8. **Write unit tests for extracted components:**
   - `MetricTile.test.tsx` — renders value, label, unit; handles zero value
   - `ReadinessTag.test.tsx` — renders correct colour/label for each status
   - `BucketCard.test.tsx` — renders items list, calls `onAdd` on button click
   - `VmRow.test.tsx` — renders vm name, toggles selection on click
   - `OverviewWorkflow.test.tsx` — renders estate metrics from mock context state
   - `IntakeWorkflow.test.tsx` — renders upload area; shows error on upload fail
   - `AssignmentWorkflow.test.tsx` — renders VM list; assignment selection updates state

9. **Verify no behaviour regression:**
   - Run existing Playwright e2e smoke test (`npm run test:e2e`) against
     dev server after split
   - All 8 existing Jest tests in `network-planning.test.ts` and
     `network-validation.test.ts` must still pass

### Relevant Context
- `prototype/carbon-ui/app/page.tsx` lines 400–530: `MetricTile`, `ReadinessTag`,
  `rowsFromSummary`, `vmDecision` helper functions to extract
- `prototype/carbon-ui/app/page.tsx` lines 630–920: all API call functions
- `prototype/carbon-ui/app/page.tsx` lines 960–1850: all `render*` functions
- `prototype/carbon-ui/jest.config.js` — needs `testEnvironment: 'jsdom'`
- `prototype/carbon-ui/types/network-planning.ts` — already has `VmNetworkAssignment`,
  `NetworkPlanningState`, `PlanningMetadata` — these are the authoritative versions
- Carbon Modal pattern: `<Modal open={...} onRequestClose={...} onRequestSubmit={...}>`
- Carbon form fields: `TextInput`, `TextArea`, `Select`, `SelectItem`, `Dropdown`
- Next.js rewrites in `next.config.mjs`: `/api/*` proxied to backend, so components
  use relative `/api/` paths — no hardcoded `localhost` needed

### Status
[ ] pending

---

## Phase 2 — Wire All Tabs to Real API Calls

### Intent
Connect every workflow panel to its corresponding FastAPI endpoint so the Carbon
UI becomes a real working application. Every mocked interaction is replaced with
a live API call in a single pass.

### Expected Outcomes
- **Intake:** Upload `.xlsx` → `POST /api/workbooks/summary` → real estate metrics
  and readiness data displayed from API response
- **Overview:** Saved projects loaded from `GET /api/projects` on mount; load/
  rename/delete wired; loading a project restores all workflow state from
  `state.planning_state_json`
- **Assignment:** VM list from `workbookSummary.assignment_rows`; assignment
  changes call `PUT /api/projects/{id}/vm-assignments` immediately (not only on
  manual save)
- **Network Plan:** VPC/subnet/SG create or edit calls
  `POST /api/projects/{id}/network-plan`; tab open calls
  `GET /api/projects/{id}/network-plan` to restore state
- **Security / Storage / Waves:** Bucket changes update the network plan
  `securityGroups` / `storageProfiles` / `waves` arrays and trigger a network
  plan save
- **Export:** "Generate Terraform Package" calls
  `POST /api/projects/{id}/terraform` → streams ZIP → browser download
  with InlineLoading feedback during generation
- **Auto-save:** When an active project has unsaved state changes, a debounced
  call to `PUT /api/projects/{id}/state` persists the full planning state
- **503 banner:** If backend has no `DATABASE_URL`, a persistent Carbon
  `InlineNotification` kind="warning" explains persistence is unavailable

### Todo List

1. **Wire IntakeWorkflow.tsx:**
   - On file drop: call `useApi.uploadWorkbook(file)`
   - On success: dispatch `SET_WORKBOOK_SUMMARY` to context
   - On error: dispatch `SET_UPLOAD_ERROR`
   - Ensure `WorkbookSummary` response shape matches `POST /api/workbooks/summary`
     response (already verified in existing `handleUpload` in `page.tsx`)

2. **Wire OverviewWorkflow.tsx:**
   - Call `useApi.listProjects()` on mount and after any project mutation
   - Load project: `useApi.loadProject(id)` → restore `carbon_summary`,
     `carbon_assignment_rows`, `carbon_resources` from
     `state.planning_state_json` into context
   - Rename: `PATCH /api/projects/{id}` with `{ name, description }`
   - Delete: `DELETE /api/projects/{id}` then refresh list
   - Show Carbon `InlineLoading` during project load

3. **Wire AssignmentWorkflow.tsx:**
   - Source VM rows from context `assignmentRows` (populated after intake)
   - On assignment change (subnet, security group, storage, wave): update context
     and immediately call `useApi.updateVmAssignments(projectId, assignments)`
   - Send bare list to `PUT /api/projects/{id}/vm-assignments` matching the
     `VmNetworkAssignmentSchema` shape (snake_case, no wrapper object)
   - Debounce calls to 500ms to avoid hammering on rapid changes

4. **Wire NetworkPlanWorkflow.tsx:**
   - On tab focus: call `useApi.loadNetworkPlan(projectId)` if project is active
   - Populate VPC/subnet/SG form state from loaded network plan
   - On any resource create/edit: call `useApi.saveNetworkPlan(projectId, plan)`
   - Ensure network plan body uses snake_case top-level keys:
     `vpcs`, `subnets`, `security_groups`, `storage_profiles`, `waves`,
     `network_components`, `vm_assignments`, `metadata`
     (already correct in existing `page.tsx` implementation)

5. **Wire SecurityWorkflow.tsx, StorageWorkflow.tsx, WavesWorkflow.tsx:**
   - Security group bucket creates/edits update `resources.securityGroups` in
     context and trigger `useApi.saveNetworkPlan` with the full updated state
   - Same pattern for `storageProfiles` and `waves`

6. **Wire ExportWorkflow.tsx:**
   - "Generate Terraform Package" calls `useApi.generateTerraform(projectId)`
   - API returns `application/zip` stream → convert to `Blob` → `URL.createObjectURL`
     → programmatic `<a>` click to trigger download
   - Show Carbon `InlineLoading` during generation
   - On success: Carbon `ToastNotification` or `InlineNotification` kind="success"
   - On error: Carbon `InlineNotification` kind="error" with `error.message`

7. **Implement auto-save:**
   - In `AppContext`, track `isDirty: boolean` flag set on any state mutation
   - `useEffect` watches `isDirty`; after 2s debounce, calls
     `useApi.saveProjectState(projectId, fullState)`
   - Clear `isDirty` after successful save; show a subtle "Saved" indicator

8. **Implement 503 persistence banner:**
   - On app mount, call `useApi.checkApiHealth()`
   - If response `persistence_enabled === false`, set context flag
   - Render Carbon `InlineNotification` kind="warning" in the shell layout
     with message: "Database not connected — project saves are unavailable.
     Start the app with `make run` for full persistence."

9. **Write integration-level tests** for each wired workflow:
   - Mock `useApi` module in Jest
   - Test that IntakeWorkflow calls `uploadWorkbook` on file add
   - Test that ExportWorkflow calls `generateTerraform` on button click and
     shows loading state
   - Test that OverviewWorkflow renders project list from mock API response
   - Test that AssignmentWorkflow calls `updateVmAssignments` on assignment change

### Relevant Context
- `prototype/api/app.py` routes — all endpoint signatures confirmed
- `prototype/api/schemas.py` — `NetworkPlanningStateSchema` field aliases:
  `addressPrefixMode`/`address_prefix_mode` (both accepted via `populate_by_name=True`)
- Existing `handleUpload`, `saveProject`, `generateTerraform`, `loadProject`
  functions in `page.tsx` — these are the reference implementations to port
- `tests/test_prototype_api_network_planning.py` — shows correct request shapes
  (bare list for vm-assignments, snake_case network plan body)
- Carbon streaming download pattern: fetch → `response.blob()` → `URL.createObjectURL`
- `next.config.mjs` rewrites `/api/*` to backend so all calls use relative paths

### Status
[ ] pending

---

## Phase 3 — Drag-and-Drop VM Assignment

### Intent
Replace the current checkbox-select-then-click assignment model with a proper
drag-and-drop workbench using `@dnd-kit`. This is the highest-value UX
differentiator over the Streamlit workbench and the primary Carbon UI showcase
capability.

### Drag Model
Drag one or more VM rows from the left panel onto a **subnet** `BucketCard` in
the right panel. A **Placement Confirmation Modal** opens pre-filled with the
target subnet. The user confirms or adjusts subnet, security group, storage
profile, and wave, then clicks Confirm. The assignment persists to the API.
Multi-select drag carries all selected VMs through the same modal in one
operation. Existing assignments can be cleared via a VM row overflow menu.

### Expected Outcomes
- `@dnd-kit/core`, `@dnd-kit/sortable`, and `@dnd-kit/utilities` installed
- VM rows are draggable with a visible drag handle
- Subnet bucket cards are drop zones that highlight on hover during drag
- Dragging opens `PlacementModal` pre-filled from drop target
- Modal has dropdowns for subnet (pre-filled), security group (VPC-filtered),
  storage profile, and wave
- Confirm assigns all dragged VMs and calls `updateVmAssignments`
- Multi-select: dragging a selected VM carries the entire selected set
- VM rows show Carbon `Tag` chips for current subnet and wave assignments
- Unassign via overflow menu on each assigned VM row
- Focused unit tests for drag components and modal logic
- Playwright E2E test: drag VM to subnet → modal opens → confirm → tag appears

### Todo List

1. **Install @dnd-kit:**
   ```
   npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
   ```

2. **Create `components/dnd/DraggableVmRow.tsx`:**
   - Wrap `VmRow.tsx` with `useDraggable` from `@dnd-kit/core`
   - Drag data: `{ type: 'vm', vmKey: string, selectedVmKeys: string[] }`
   - When `isDragging`: apply Carbon-compatible opacity/transform style
   - Show `Draggable` icon (Carbon: `Draggable` from `@carbon/icons-react`)
     as handle on the left of the row

3. **Create `components/dnd/SubnetDropZone.tsx`:**
   - Wrap `BucketCard.tsx` for subnet type with `useDroppable`
   - `isOver` → apply Carbon `$layer-02` background token as highlight
   - Show "Drop VMs here" copy when bucket is empty
   - `data`: `{ subnetId: string, subnetName: string, vpcId: string }`

4. **Create `components/dnd/PlacementModal.tsx`:**
   - Carbon `ComposedModal` with `ModalHeader`, `ModalBody`, `ModalFooter`
   - Header: "Place VM(s) into network" / "Place X VMs into network" for multi
   - Body:
     - Read-only list of VM name(s) being placed (Carbon `StructuredList`)
     - `Dropdown` for subnet (pre-filled with drop target, options from context
       `resources.subnets` filtered to same VPC as drop target)
     - `Dropdown` for security group (options from `resources.securityGroups`
       filtered to same VPC as selected subnet's `vpcId`)
     - `Dropdown` for storage profile (options from `resources.storageProfiles`)
     - `Dropdown` for wave (optional, options from `resources.waves`)
   - Security group dropdown re-filters when subnet selection changes
   - Footer: "Confirm placement" (primary) and "Cancel" (secondary)
   - On confirm: build `VmNetworkAssignment[]` for each dragged VM, dispatch to
     context, call `useApi.updateVmAssignments(projectId, allAssignments)`

5. **Wire `DndContext` in `AssignmentWorkflow.tsx`:**
   - Wrap the two-column layout (VM list + bucket columns) in `<DndContext>`
   - `onDragStart`: store `activeVmKeys` in local state
   - `onDragEnd`: if `over` target is a subnet drop zone, open `PlacementModal`
     with `subnetId`, `vpcId`, and `vmKeys` pre-filled
   - `onDragCancel`: clear `activeVmKeys`
   - `<DragOverlay>`: render a `VmRow` snapshot with count badge for multi-select
     (e.g. "web-server-01 +3 more")

6. **Multi-select drag interaction:**
   - Existing checkbox selection in `AssignmentWorkflow` populates
     `selectedVmIds` in context
   - `DraggableVmRow` passes `selectedVmIds` when `vmKey` is in the selected set
   - Dragging an unselected VM: `PlacementModal` receives only that VM's key
   - After successful placement, clear `selectedVmIds`

7. **Unassign via overflow menu:**
   - Add Carbon `OverflowMenu` + `OverflowMenuItem` to each `VmRow` when a
     subnet assignment exists
   - "Remove placement" item: clear `primarySubnetId`, `primarySecurityGroupId`,
     `storageProfileId`, `waveId` for that VM in context and call
     `updateVmAssignments`

8. **Assignment status chips on VM rows:**
   - `VmRow.tsx`: when `vm.subnet` is set, render Carbon `Tag` type="blue"
     with subnet short-name (up to 20 chars, truncated with ellipsis)
   - When `vm.wave` is set, render Carbon `Tag` type="green" with wave name
   - Tags appear in the right column of the VM row

9. **Write focused tests:**
   - `PlacementModal.test.tsx`:
     - Renders correct VM name(s) in structured list
     - Subnet dropdown shows only subnets in matching VPC
     - Security group dropdown filters when subnet changes
     - Confirm button calls `updateVmAssignments` with correct shape
   - `DraggableVmRow.test.tsx`:
     - Drag data includes selected VM keys when vm is in selection
     - Drag data contains only self when vm is not selected
   - `SubnetDropZone.test.tsx`:
     - Renders BucketCard with "Drop VMs here" when empty
   - Playwright E2E addition to `carbon-smoke.spec.ts`:
     - Upload sample workbook, create subnet bucket, drag VM row onto bucket,
       confirm in modal, verify subnet tag appears on VM row

### Relevant Context
- `prototype/carbon-ui/components/workflows/AssignmentWorkflow.tsx` — created
  in Phase 1, source for drag wiring
- `prototype/carbon-ui/components/ui/BucketCard.tsx` — base for `SubnetDropZone`
- `prototype/carbon-ui/hooks/useApi.ts` — `updateVmAssignments` created in Phase 2
- `@dnd-kit/core` API: `DndContext`, `useDraggable`, `useDroppable`, `DragOverlay`,
  `DragStartEvent`, `DragEndEvent`
- Carbon `ComposedModal` vs `Modal`: use `ComposedModal` for custom footer layout
- `PUT /api/projects/{id}/vm-assignments` — bare list (not wrapped), confirmed
  correct in `tests/test_prototype_api_network_planning.py`
- `@carbon/icons-react` icon for drag handle: `Draggable` component

### Status
[ ] pending

---

## Notes for All Phases

- **Deployment:** `prototype/carbon-ui/Dockerfile` uses `node:20-alpine`. `@dnd-kit`
  has no native dependencies and builds cleanly on Node 20.
- **API paths:** `next.config.mjs` rewrites `/api/*` to the backend. All
  `useApi.ts` calls should use relative paths (`/api/projects`, not
  `http://localhost:8000/api/projects`) so the same code works in Docker and dev.
- **snake_case convention:** API request bodies stay snake_case throughout
  (already correct in current `page.tsx`). React state and TypeScript interfaces
  stay camelCase. No migration needed.
- **Documentation:** After Phase 3, update `docs/IMPLEMENTATION_STATUS.md` to
  reflect Gates 1–4 status and mark completed roadmap items.
- **Promotion gate re-evaluation:** After Phase 3, run against the 6 promotion
  gates in `docs/carbon-react-ui-strategy.md` to determine what remains before
  Carbon UI can replace Streamlit as the supported workbench.
