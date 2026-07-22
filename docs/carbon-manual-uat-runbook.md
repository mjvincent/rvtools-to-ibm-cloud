# Carbon Manual UAT Runbook

Use this runbook when a migration reviewer, accessibility reviewer, or release
owner needs to execute a repeatable Carbon user-acceptance review. It is the
practical companion to the
[Carbon Accessibility and UAT Checklist](carbon-accessibility-uat-checklist.md)
and the
[Carbon Accessibility and UAT Results Template](carbon-accessibility-uat-results-template.md).
Use [Carbon Manual UAT Evidence Index](carbon-manual-uat-evidence-index.md)
to confirm which evidence sources already exist and which manual review areas
are still open.
Use [Carbon UAT Session Worksheet](carbon-uat-session-worksheet.md) as the
working document during each individual review session before summarizing final
results in the template.

Streamlit remains the supported production UI until this review is completed,
signed off, and accepted in the Carbon promotion review.

## Review Packet

Create one evidence folder or ticket for the review. Use a neutral name such as
`carbon-uat-2026-07-15` or the release-candidate tag. Do not include customer
workbook paths, raw RVTools data, VM names, IP addresses, application names, or
owner names in the folder name or notes.

Include:

- completed checklist
- completed session worksheet for each reviewer run
- completed results template
- Carbon commit SHA
- validation command output
- `docker compose ps` output or hosted-runtime health evidence
- browser and assistive-technology notes
- sanitized screenshots or recordings
- Carbon readiness report JSON
- Carbon Terraform ZIP or sanitized ZIP inventory
- Streamlit comparison ZIP or parity-test output when used
- issue log with owner, severity, and status

## Setup

From the repository root:

```bash
git status --short --branch
git rev-parse HEAD
docker compose up -d --build carbon-ui
docker compose ps
```

Open:

- Carbon: `http://localhost:3000`
- Streamlit fallback: `http://localhost:8501`

If Carbon is running another approved way, record the URL, startup command, and
runtime health check in the evidence packet.

## Pre-Review Validation

Run or attach the latest validation output:

```bash
make compile
venv/bin/python -m pytest -q
cd prototype/carbon-ui
npx tsc --noEmit --incremental false
npm test -- --runInBand
npm run test:e2e
```

If the browser suite cannot run in the review environment, record why and run
the component/unit checks plus a manual browser smoke review.

## Recommended Workbook

Start with the checked-in small sample workbook:

`samples/rvtools-small-complete.xlsx`

Use the larger workshop sample only after the small sample pass is complete:

`samples/SizingWorkshop-RVTools.xlsx`

For private or customer workbooks, record only a sanitized label such as
`customer-workbook-a`. Do not paste workbook paths, filenames, VM names, IP
addresses, owners, applications, screenshots with sensitive values, or raw
RVTools rows into the evidence packet.

## Review Sequence

1. Open Carbon and confirm the page shell loads without app console errors.
2. Open the current workflow `Help` control and confirm step-specific guidance
   appears.
3. Click `Open user guide` and confirm the guide opens in a separate browser
   window or tab that can remain visible during the review.
4. Upload the small sample workbook from Workbook Intake.
5. Save the project with a neutral name such as `Carbon UAT sample`.
6. Refresh the browser and reload the saved project.
7. Confirm VM Assignment rows, readiness chips, and assignment bucket controls
   are still populated.
8. Use keyboard-only navigation for one subnet/security/storage/wave assignment.
9. Use drag/drop for one VM assignment and confirm the placement modal appears.
10. Open Network Plan.
11. Review the `Network validation` region.
12. Open an existing network component edit action, confirm the modal fields are
    labeled, then cancel or save a harmless note change.
13. Review Remediation Backlog and edit one non-sensitive owner/status/note
    value.
14. Review Image Import Planning and edit one import status or note.
15. Review Migration Ops and confirm open blockers/ready rows are understandable.
16. Open Export Readiness.
17. Run preflight and use at least one `Review issue` route when findings exist.
18. Preview Terraform, filter files, download one selected file, and close the
    preview.
19. Download the readiness report JSON.
20. Resolve blockers if needed, or use a clean project, then download the
    Terraform ZIP.
21. Generate or compare Streamlit output for the same workbook when this is a
    promotion or pilot-readiness review.
22. Complete the checklist, result matrix, issue log, known gaps, and sign-off
    sections.

## Accessibility Review

At minimum, review with keyboard only:

- `Tab` and `Shift+Tab` through the shell and left navigation
- `Enter` or `Space` on navigation, buttons, checkboxes, and modal actions
- explicit assignment buttons as the drag/drop alternative
- Network Plan component edit actions
- Export preview file selection and close/download controls

For screen-reader review, use VoiceOver, NVDA, JAWS, or the assistive
technology required by the deployment environment. Confirm:

- current workflow and navigation state are understandable
- readiness chips explain status and destination
- VM row checkboxes include VM identity
- Network validation is discoverable as a named region
- validation findings include severity, subject, message, and recommended action
- notifications announce upload, save, preflight, preview, and export status
- no modal, dropdown, preview, or panel traps focus

## Evidence To Capture

Capture concise evidence, not raw data:

- screenshot of the loaded Carbon shell with sensitive values hidden
- screenshot or recording of keyboard assignment
- screenshot of Network Plan validation and component edit modal
- screenshot of Export preflight findings or clean preflight result
- screenshot of Terraform preview
- readiness report JSON
- ZIP inventory or sanitized ZIP filename
- command output for validation and runtime health

Do not capture:

- raw RVTools workbook content
- full customer VM names
- IP addresses or CIDR plans from private environments
- owner or application names from private workbooks
- IBM Cloud credentials, API keys, Terraform state, or secrets

## Result Rules

Use these definitions in the results template:

- `Pass`: reviewer completed the flow without blockers and no unresolved high
  or medium issues remain.
- `Pass with issues`: reviewer completed the flow, but one or more accepted
  medium or low issues remain with owners and revisit dates.
- `Fail`: reviewer could not complete a primary workflow, found a data-loss
  risk, found an unacceptable accessibility issue, or generated output was not
  acceptable compared with Streamlit.
- `Not started`: area was not reviewed.

Severity guidance:

- `Blocker`: prevents workbook intake, project recovery, assignment, preflight,
  preview, ZIP export, or creates unacceptable accessibility/data-loss risk.
- `High`: primary workflow requires a difficult workaround.
- `Medium`: workflow is usable but confusing, inefficient, or missing expected
  feedback.
- `Low`: polish issue that does not block pilot use.

## Exit Criteria

Carbon can move toward pilot only when:

- the checklist is complete
- the results template has named reviewers and decisions
- blocker/high issues are closed or explicitly accepted by the release owner
- medium/low issues have owners and revisit dates
- Carbon output is acceptable against Streamlit for the reviewed workbook
- rollback to Streamlit remains available

Carbon should not become the default UI from this runbook alone. The promotion
decision still belongs in the Carbon promotion gate review.
