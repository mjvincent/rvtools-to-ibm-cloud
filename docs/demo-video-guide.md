# Demo Video Guide

## Purpose

Create a 5 minute workshop-style demo that shows how the RVTools to IBM Cloud VPC tool turns an RVTools workbook into a Terraform handoff package with readiness, planning, and operator guidance.

The demo should emphasize that the app generates IBM Cloud VPC Terraform and migration handoff files. It does not execute Terraform, import images, move workloads, or perform cutover.

Audience: IBM internal reviewers, GitHub repo visitors, and customer demo audiences.

Voice approach: AI voice workflow using Michael Vincent Jones' voice with explicit permission from Michael Vincent Jones for this demo.

## Recommended Demo Setup

- Use `samples/rvtools-small-complete.xlsx` for the first polished demo.
- Optional second recording: use `samples/SizingWorkshop-RVTools.xlsx` to show realistic blocker handling.
- Run the app locally:

```bash
python -m streamlit run app.py
```

- Browser size: 1440 x 900 or larger.
- Zoom: 100%.
- Hide bookmarks and unrelated desktop notifications.
- Suggested recorder: QuickTime, Loom, OBS, or Screen Studio.
- Target length: 5 minutes.
- Tone: workshop-style, practical, and technical enough for architects and migration teams.

## Storyboard

| Time | Screen | Narration Goal |
| --- | --- | --- |
| 0:00-0:20 | README or app header | Introduce the problem: RVTools data needs to become reviewable IBM Cloud VPC Terraform. |
| 0:20-0:45 | Launch app and upload sample workbook | Show that a user can start with a sample file and immediately get an assessment workbench. |
| 0:45-1:20 | Overview and Guided Migration Assistant | Show estate summary, checklist, and safe planning defaults. |
| 1:20-1:55 | Readiness and Remediation Backlog | Show how blockers and review items are surfaced before packaging. |
| 1:55-2:30 | VM Review, Wave Planning, Image Import Planning | Show human decisions: exclusions, overrides, ownership, waves, and image tracking. |
| 2:30-3:00 | Migration Ops | Show cutover readiness by wave and cutover group. |
| 3:00-3:50 | Export tab | Show planning state, preflight, package build, and download. |
| 3:50-4:30 | ZIP contents | Show Terraform files, handoff CSVs, planning state, image variables, runbook, and root README. |
| 4:30-5:00 | Close | Reinforce scope: Terraform generation and migration handoff, not workload movement. |

## Voiceover Script

### Intro

This is the RVTools to IBM Cloud VPC migration planning tool. It takes a standard VMware RVTools workbook and turns it into a structured IBM Cloud VPC Terraform package, along with the handoff files that migration teams need before image import, Terraform plan, and cutover.

The goal is not to magically move workloads. The goal is to turn source inventory into reviewable infrastructure-as-code, readiness signals, and a clean operator package.

### Upload And Assessment

I will start with the included small sample workbook, `rvtools-small-complete.xlsx`. After upload, the app parses the RVTools tabs and builds an assessment workbench.

The Overview gives an estate summary, readiness counts, assessment quality, and the Guided Migration Assistant. This checklist helps a first-time user understand the sequence: review blockers, track remediation, complete wave planning, update image import status, review Migration Ops, and then build the Terraform bundle.

The assistant can apply safe defaults, such as setting blank image import statuses to Pending and creating open remediation tracker rows. It does not mark images imported, change profiles or subnets, build Terraform, or perform migration.

### Readiness And Decisions

The Readiness tab groups image, migration, memory, and network findings so teams can deal with blocked items before packaging.

The Remediation Backlog turns those findings into trackable work items with status, owner, due date, and notes.

In VM Review, the user can decide what stays in scope and adjust target decisions, such as profile overrides, storage tier overrides, network placement, subnet, and security group mapping. These decisions are preserved in planning state so the work can be paused and resumed.

### Planning Views

Wave Planning lets migration teams assign wave, cutover group, owner, application, priority, and dependency group.

Image Import Planning groups active VMs by source image and tracks the import lifecycle, including target catalog IDs after images are imported into IBM Cloud.

Migration Ops ties the planning pieces together. It shows which workloads are ready, which require review, and which remain blocked because of missing planning fields, unresolved remediation, or pending image import.

### Export And Package

The Export tab is where the Terraform handoff is built. Package settings include the VPC name, deployment target, address prefix strategy, subnet CIDRs, and optional SSH source CIDR.

The app runs package preflight before building. If there are blockers, the build stops and tells the user what to fix or exclude.

Once the package is ready, the app downloads a ZIP containing the Terraform project, mapping CSVs, readiness exports, planning state, preflight reports, image import variables, a migration runbook, and a root README for the Terraform operator.

### ZIP And Operator Handoff

Inside the ZIP, the Terraform files are organized into root files and modules for networking, storage, and virtual server instances.

The handoff files help teams review VM mappings, NIC mappings, disk mappings, readiness findings, pricing diagnostics, remediation, image import status, and cutover readiness.

The root README gives the Terraform operator the next steps: review preflight, replace image ID placeholders, validate the package, run Terraform plan, and confirm all manual inputs such as IBM Cloud credentials, quota, profiles, network design, and custom image IDs.

### Close

That is the purpose of this tool: convert RVTools exports into an IBM Cloud VPC Terraform package with enough planning context that architects, migration teams, and Terraform operators can move forward with confidence.

The tool does not replace application validation or migration execution, but it gives the team a practical, auditable starting point for the IBM Cloud VPC migration workflow.

## Screen Recording Checklist

1. Start the app with `python -m streamlit run app.py`.
2. Upload `samples/rvtools-small-complete.xlsx`.
3. Pause briefly on Overview metrics and Guided Migration Assistant.
4. Open Readiness and Remediation Backlog.
5. Open VM Review and point out editable decisions.
6. Open Wave Planning and Image Import Planning.
7. Open Migration Ops.
8. Open Export.
9. Show Package Settings, Planning State, Preflight Review, and Build And Download.
10. Build the Terraform project.
11. Download and extract the ZIP.
12. Show `README.md`, `main.tf`, module folders, `migration-manifest.json`, `preflight-report.csv`, `image-import-variables.tfvars.example`, and `migration-runbook.md`.

## Voice Recording Options

### Selected Voice Workflow

Use an approved AI voice workflow with Michael Vincent Jones' voice for this demo. The voice model must be created only from a voice sample that Michael Vincent Jones provides for this purpose, and the final narration must be reviewed before publication.

Recommended external tools:

- Descript Overdub
- ElevenLabs Professional Voice Cloning
- PlayHT
- HeyGen
- Another IBM-approved or team-approved tool

Required inputs:

- Explicit consent from Michael Vincent Jones to use his voice for this demo.
- A clean 2-5 minute voice sample, recorded in a quiet room.
- Confirmation of the target platform/tool used for voice generation.
- Final script approval before generating the production voiceover.
- Final audio approval before publishing or sharing the demo.

### Direct Voiceover Alternative

Record yourself reading the script in a quiet room. Use the recording directly as the voiceover.

## Camera And AI Video Options

### Screen Recording Only

Recommended default. Record the app and ZIP walkthrough, then layer AI voiceover and captions on top. This is the simplest and most credible format for IBM internal, GitHub, and customer audiences.

### Camera Intro And Outro

Optional. Record a short real camera introduction and closing from Michael, then use screen recording for the app demo. This is polished without needing a synthetic video avatar.

### AI Talking-Head Video

Possible only through an external approved tool such as HeyGen, Synthesia, Descript, or another service that supports consent-based avatar generation. This repo/session can prepare the script, shot list, prompts, captions, and asset checklist, but the actual AI video generation must happen in that external tool.

Required if using an AI talking-head version:

- Explicit consent from Michael Vincent Jones to use his likeness for this demo.
- A clean reference video or approved avatar source.
- Confirmation that the generated avatar may be used for IBM internal, GitHub, and customer demo audiences.
- Final human review before publication.

Do not use a cloned or synthetic voice or likeness without explicit permission from the person being modeled.

## Assets To Prepare

- Screen recording of the app flow.
- Optional real camera intro/outro or approved avatar source.
- Optional headshot or intro slide.
- Voiceover audio.
- Optional background music, kept low or omitted.
- Optional captions generated from the final script.

## Suggested Video Title And Description

Title:

```text
RVTools to IBM Cloud VPC: Terraform Migration Planning Demo
```

Description:

```text
This demo shows how the RVTools to IBM Cloud VPC tool converts VMware RVTools exports into an IBM Cloud VPC Terraform package with readiness assessment, migration planning, image import tracking, package preflight, and Terraform operator handoff files.

The tool generates Terraform and planning artifacts. It does not execute Terraform, move workloads, import images, or perform application cutover.
```

## What I Need From You

Confirmed choices:

- Length: 5 minutes.
- Tone: workshop-style.
- Voice: approved AI voice workflow using Michael Vincent Jones' voice.
- Audience: IBM internal use, GitHub repo visitors, and customer demos.

Still needed from Michael:

- Clean 2-5 minute voice sample.
- Preferred AI voice tool, or approval to choose one.
- Decision on screen-recording-only, real camera intro/outro, or AI talking-head video.
- If AI talking-head video: explicit likeness permission and a clean reference video or approved avatar source.
- Any required IBM/customer branding restrictions, disclaimers, or approval workflow.
