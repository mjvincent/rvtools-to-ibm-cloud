# Priority 2: Migration Planning Workflow

This document covers the Priority 2 migration planning features added to the rvtools-to-ibm-cloud application and the Migration Ops readiness view that ties them together:

1. **Wave Planning** — Organize VMs into migration waves with ownership and dependency tracking
2. **Decision Audit Export** — Capture all profile/storage override decisions with pricing impact
3. **Remediation Tracker** — Track readiness blockers with owner assignment and status
4. **Image Import Planning** — Group VMs by source image and coordinate import pipeline
5. **Migration Ops** — Combine wave, remediation, and image import state into cutover readiness

---

## 1. Wave Planning

### Overview

Wave planning organizes your VM migration into coordinated groups, each with specific metadata for tracking and accountability:

- **Wave** — The migration wave identifier (e.g., "Wave 1", "Wave 2")
- **Cutover Group** — A subgroup within the wave for coordinated cutover
- **Owner** — The person responsible for migrating this VM
- **Application** — The application or service name (for grouping related VMs)
- **Priority** — Migration priority level: High, Medium, or Low
- **Dependency Group** — Identifier for VMs that must migrate together

### How to Use Wave Planning

#### 1. Navigate to Wave Planning Tab

After uploading RVTools and reviewing blockers, click the **"Wave Planning"** tab in the main workbench to assign wave metadata.

#### 2. Assign Wave Metadata Individually

Use the data editor table to edit individual VMs:
- Click the cell to enter wave name, cutover group, owner, or application
- Select priority from the dropdown: High, Medium, or Low
- Enter dependency group identifier

#### 3. Bulk Assignment (Recommended for Large Estates)

For large migrations, use bulk assignment to speed up data entry:

1. **Select Multiple VMs**: Use the VM key multiselect to choose VMs with the same wave assignment
2. **Click "Assign Wave"**: Opens a form to apply wave, cutover group, owner, and application to all selected VMs
3. **Click "Assign All to Wave"**: Quick shortcut to set the same wave for all active VMs

#### 4. Conflict Detection

The Wave Planning tab automatically detects conflicts:

- ⚠️ **Application Conflict**: VMs in the same application have different cutover groups (may cause coordination issues)
- ⚠️ **Dependency Conflict**: VMs in the same dependency group have different waves (may delay mutual dependencies)

These are warnings only and don't block Terraform generation, but help identify coordination issues.

#### 5. Completeness Badge

A status badge at the top shows:
- ✅ **Complete: X/Y VMs** — All wave fields filled for X of Y active VMs
- ⚠️ **Incomplete: X/Y VMs** — X VMs still need wave assignments

### Wave Planning Data Persistence

Wave metadata is included in:
- Migration manifest (for tracking and audit)
- Decision audit CSV (for signoff)
- Image import plan (for owner coordination)
- All Terraform-generated resources (tags/metadata)

---

## 2. Decision Audit Export

### Overview

The decision audit export captures all manual override decisions (profile selection, storage tier, network mode, VM exclusion) along with their pricing impact. This enables:

- **Signoff workflow** — Leadership review of sizing decisions before Terraform generation
- **Cost reconciliation** — Post-migration comparison of estimated vs. actual costs
- **Audit trail** — Historical record of override reasons and decision makers

### How to Use Decision Audit Export

#### 1. Review Decisions Before Terraform Generation

Before building the Terraform handoff package:

1. Navigate to **"Terraform"** section in the app
2. Look for **"Decision Audit"** export button (part of handoff package)
3. Download or preview the CSV to review all override decisions

#### 2. Interpret the Decision Audit CSV

The CSV includes these columns:

| Column | Meaning |
|--------|---------|
| **VM Key** | RVTools VM identifier |
| **VM Name** | Friendly VM name |
| **Owner** | Migration owner (from Wave Planning) |
| **Application** | Application name (from Wave Planning) |
| **Wave** | Migration wave (from Wave Planning) |
| **Original Profile** | Default IBM Cloud profile suggested by catalog |
| **Chosen Profile** | Profile you selected (if different from original) |
| **Profile Override Reason** | Notes on why you changed the profile |
| **Original Storage Tier** | Default storage tier based on disk size |
| **Chosen Tier** | Storage tier you selected |
| **Storage Tier Override Reason** | Notes on why you changed storage |
| **Network Mode** | Network connectivity choice (VLAN, VPC, etc.) |
| **Include/Exclude** | Whether VM is included or excluded from migration |
| **Exclusion Reason** | If excluded, reason for exclusion |
| **vCPU Cost Delta** | Monthly cost difference vs. original profile |
| **Storage Cost Delta** | Monthly storage cost difference |
| **Total Pricing Impact** | Total monthly cost delta (vCPU + storage) |

#### 3. Example Decision Audit Row

```
vm-001,web-server-01,alice@example.com,payroll,wave-01,bx2-2x8,bx2-4x16,manual override for perf,3iops-tier,10iops-tier,latency required,vlan-100,Include,,45.00,10.50,55.50
```

This VM has:
- Profile upgraded from bx2-2x8 → bx2-4x16 (reason: manual override for perf) = **$45/month increase**
- Storage tier upgraded from 3iops → 10iops (reason: latency required) = **$10.50/month increase**
- **Total pricing impact: $55.50/month increase**

#### 4. Summary Section

The CSV includes summary rows at the end:
- **TOTAL** — Sum of all pricing impacts across included/excluded VMs
- Helps identify overall cost impact of your override decisions

### Tips for Decision Audit

- ✅ Use clear, consistent naming for waves and applications
- ✅ Document override reasons before generating Terraform (easier to remember)
- ✅ Review decision audit with stakeholders before building infrastructure
- ✅ Keep decision audit CSV for post-migration cost reconciliation

---

## 3. Remediation Tracker

### Overview

The remediation tracker helps manage readiness blockers discovered during assessment:

- **Blocker Types** — Image readiness, migration readiness, memory readiness, network readiness, preflight findings
- **Status Tracking** — Open, In Progress, Resolved, Deferred (for each blocker)
- **Owner Assignment** — Map blockers to responsible parties
- **Due Dates** — Track remediation deadlines
- **Export** — Generate backlog CSV for external tracking systems

### How to Use Remediation Tracker

#### 1. Navigate to Remediation Backlog Tab

After uploading RVTools, click the **"Remediation Backlog"** tab to see all blockers discovered during assessment.

#### 2. Understand Blocker Types

The tab shows all blockers grouped by type:

| Blocker Type | Example | Remediation |
|--------------|---------|-------------|
| **Image Readiness** | Unsupported OS version | Update guest OS or plan for image import |
| **Migration Readiness** | Mounted CD/DVD media | Remove media in VMware before migration |
| **Memory Readiness** | Insufficient memory | Right-size or resolve memory constraint |
| **Network Readiness** | Network adapter config issue | Adjust network config in Terraform or VMware |
| **Preflight** | Database state issue | Backup or quiesce database before cutover |

#### 3. Assign Owners and Status

Use the data editor to:

1. **Owner** — Read-only, pulled from Wave Planning. Make sure wave owners are assigned first.
2. **Status** — Change from Open → In Progress → Resolved (or Deferred if not applicable)
3. **Due Date** — Click date picker to set remediation deadline
4. **Notes** — Add notes on remediation (e.g., "Backup scheduled for Friday")

#### 4. Review Summary Metrics

At the top of the Remediation Backlog tab, you'll see:

- **By Status**: Open (5), In Progress (2), Resolved (1), Deferred (3)
- **By Owner**: alice@example.com (3), bob@example.com (5), unassigned (2)
- **Overdue Items**: Count of items past due date with Open or In Progress status

#### 5. Export Backlog for External Tracking

Click **"Export Remediation Backlog"** button to download a CSV with:
- All blockers, owners, status, due dates, and notes
- Summary section with counts by status and owner
- Can be imported into Jira, ServiceNow, or Excel for project tracking

### Remediation Tracker Data Persistence

Remediation tracker edits live in browser session state while the app is open. If you:
- Close the browser
- Refresh the page
- Exit the app

Export the remediation backlog CSV before leaving the session.

**To resume tracking data across sessions:**
1. Export remediation backlog CSV (contains all data)
2. Share CSV with team or store in project management system
3. Upload the same RVTools workbook in a later app session
4. Open **Import saved remediation tracker** and load the CSV
5. The app reloads status, due date, notes, and owner values by blocker ID or matching blocker details

---

## 4. Image Import Planning

### Overview

Image import planning helps coordinate the import of source VM images into IBM Cloud:

- **Image Grouping** — VMs automatically grouped by source image
- **Bulk Status Tracking** — Mark images as Not Started → In Progress → Imported → Failed
- **Target Catalog ID** — Link to imported image in IBM Cloud catalog
- **Pipeline Coordination** — Export plan for image import service/team

### How to Use Image Import Planning

#### 1. Navigate to Image Import Planning Tab

Click the **"Image Import Planning"** tab to see VMs grouped by their source images.

#### 2. Understand Image Groups

Each image group shows:

- **Source Image** — The source image name (from RVTools)
- **Count of VMs** — Number of VMs using this source image (e.g., "12 VMs")
- **Owners** — Comma-separated list of owners (from Wave Planning)
- **Target Catalog ID** — IBM Cloud catalog image ID (editable)
- **Import Status** — Current status (Not Started, In Progress, Imported, Failed)
- **Estimated Time** — Import time estimate in minutes (editable)
- **Notes** — Free text notes (editable)

#### 3. Fill in Image Import Details

For each image group:

1. **Enter Target Catalog ID**: After image is imported to IBM Cloud, enter the catalog ID (e.g., `r001-12345678`)
2. **Set Import Status**:
   - **Not Started** — Image hasn't been imported yet
   - **In Progress** — Image import currently running
   - **Imported** — Image successfully imported and ready for VSI creation
   - **Failed** — Image import failed (see notes for details)
3. **Estimate Import Time**: Rough estimate of how long import will take (impacts cutover planning)
4. **Add Notes**: Any relevant notes (e.g., "Imported from COS bucket", "Retrying after failure")

#### 4. Bulk Status Updates

For multiple images with the same status:

1. Click checkboxes to select multiple image groups
2. Click **"Bulk Update Status"** button
3. Select new status in the form
4. Apply to all selected images

#### 5. Track Import Progress

Summary section at the top shows:

- **Total Unique Images**: Count of unique source images
- **Total VMs**: Total VMs across all images
- **Import Progress**: X Imported, Y In Progress, Z Not Started, W Failed
- **Time Estimate**: Sum of all estimated import times

#### 6. Export Image Import Plan

Click **"Export Image Import Plan"** button to download CSV with:
- Source Image, Count of VMs, Owners, Target Catalog ID, Import Status, Estimated Time, Notes
- Ready for hand-off to image import team or service

### Image Import Planning Data Persistence

Like remediation tracker, image import status lives in browser session state while the app is open. To resume:
1. Export image import plan CSV
2. Share with image import team/pipeline
3. After import completes, upload RVTools again
4. Open **Import saved image import plan** and load the CSV
5. The app reloads target catalog IDs, import statuses, estimated timing, and notes

The tab preserves the existing Image Import Planning session-state keys during reruns and uses the same status data when generating the image-import CSV and Terraform handoff package inputs.

---

## 5. Migration Ops

### Overview

Migration Ops combines wave assignments, readiness blockers, remediation status, and image import status into one cutover readiness view.

Use it to answer:
- Which VMs are ready for cutover scheduling?
- Which wave or cutover group still has blockers?
- Which planning fields are missing?
- Which remediation items remain unresolved?
- Which source images are not yet `Imported`?

The detail table and `cutover-readiness.csv` export include VM, wave, cutover group, owner, application, blocker category, blocker reason, and recommended next action.

---

## Workflow Integration

### Complete Priority 2 Workflow

Here's how to use the planning features together:

1. **Upload RVTools** → App performs readiness assessment
2. **Review Blockers** → Identify any blocking issues (preflight, readiness)
3. **Assign Wave Planning** → Set wave, cutover group, owner, application for all VMs
4. **Track Remediation** → Assign blockers to owners, set due dates, track status
5. **Review Decision Audit** → Ensure profile/storage overrides make sense
6. **Track Image Imports** → Set import status and target catalog IDs
7. **Review Migration Ops** → Confirm cutover readiness by wave and cutover group
8. **Generate Terraform** → Build infrastructure with all metadata
9. **Generate Handoff Package** → ZIP includes manifest + decision audit + remediation backlog + image import plan + cutover readiness

### Data Flow

```
RVTools Upload
    ↓
Wave Planning (assign wave/owner/app/priority)
    ↓
Remediation Tracker (assign owner to blockers)
    ↓
Decision Audit (review override decisions)
    ↓
Image Import Planning (set import status)
    ↓
Migration Ops (review cutover readiness)
    ↓
Terraform Generation + Exports
    ↓
Handoff ZIP (manifest + all CSVs)
    ↓
Migration Execution
```

### Handoff Package Contents

The final ZIP download includes:

```
migration-package.zip
├── manifest.json                    (master data: VMs + wave + remediation summary + image summary)
├── terraform/
│   ├── main.tf
│   ├── networking.tf
│   ├── storage.tf
│   └── vsis.tf
├── decision-audit.csv              (profile/storage override decisions + pricing impact)
├── remediation-backlog.csv         (blockers + owner + status + due date)
├── image-import-plan.csv           (images + owners + import status + target catalog ID)
├── cutover-readiness.csv           (wave + blocker + image import readiness)
├── vm-mapping.csv
├── disk-mapping.csv
├── nic-mapping.csv
└── preflight-report.csv
```

---

## FAQ

**Q: Can I edit wave data after uploading RVTools?**
A: Yes! Use the Wave Planning tab to edit any time. Edits are included in all exports and Terraform generation.

**Q: What if a VM doesn't have a wave assignment?**
A: Wave assignments are optional but recommended for large migrations. VMs without assignments default to empty strings in exports.

**Q: Can I change remediation status multiple times?**
A: Yes! Status is editable. But remember: data is session-only, so export if you need to persist changes.

**Q: How do I coordinate with the image import team?**
A: Export the image import plan CSV and share with your image import service/team. After they complete imports, they provide target catalog IDs for you to enter back into the app.

**Q: What's the difference between Cutover Group and Dependency Group?**
A: **Cutover Group** is for VMs you want to migrate together in the same cutover window (time-based). **Dependency Group** is for VMs with application dependencies (order-based). They serve different purposes.

**Q: Can I re-import data from exported CSVs?**
A: Decision audit and image import plan are read-only exports. Remediation backlog can be manually merged back if you export, edit externally, then re-import RVTools.

---

## Support & Feedback

For issues or feature requests related to Priority 2 workflow:
- Check DEVELOPMENT_LOG.md for recent changes
- Review test snapshots in tests/snapshots/ for expected output format
- Create an issue on the repository with reproduction steps
