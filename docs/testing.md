# Testing

## Pytest Suite
The supported test suite lives under `tests/` and runs with:

```bash
python -m pytest
```

Run focused checks by file when iterating:

```bash
python -m pytest tests/test_catalog_pricing.py
python -m pytest tests/test_disk_mapping.py
```

If `make` is available, the full pytest suite can also run with:

```bash
make test
```

`pytest.ini` limits collection to `tests/` and excludes `experiments/`. The scripts under `experiments/` are preserved research artifacts, not production test coverage.

The suite should not emit application-owned `datetime.utcnow()` deprecation
warnings. FastAPI/Starlette `TestClient` checks use `httpx2` so the suite does
not emit the deprecated `httpx` test-client path warning.

## Fixtures
Shared setup lives in `tests/conftest.py`.

Use fixtures for repeated records and generated inputs, including:
* `sample_vm_record`
* `sample_vm_model`
* `disk_vm_record`
* `partition_workbook`
* `sample_live_catalog`
* `parse_csv_rows`
* `parse_json`

Prefer extending these fixtures over copying large sample dictionaries into new tests.

## Snapshots
Plain text snapshots live in `tests/snapshots/`. Snapshot tests compare generated output against committed files for stable contracts such as Terraform HCL, CSV handoff files, image import tfvars, and migration manifest JSON.

When a generated contract intentionally changes:
1. Inspect the failing pytest diff.
2. Regenerate or manually update only the affected snapshot file.
3. Review the snapshot diff as part of the code change.
4. Run `python -m pytest` before committing.

Snapshots are not auto-updated during normal test runs. This keeps output contract changes visible in review.

## Streamlit Browser Validation
Run this checklist before release-style handoff, after dependency changes, or after changes that touch Streamlit orchestration, parsing, Terraform rendering, or handoff exports.

1. Install or verify dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Run the automated checks:

```bash
python -m pip_audit -r requirements.txt
python -m pytest
python -m pytest -W error::DeprecationWarning
python -m py_compile app.py rvtools_parser.py assessments.py assessment_quality.py sizing.py catalog_pricing.py terraform_renderer.py preflight.py ui.py logic_engine.py streamlit_app/*.py rvtools/*.py handoff/*.py models/*.py scripts/generate_pricing_cache.py scripts/validate_terraform_package.py
python scripts/validate_terraform_package.py
git diff --check
```

Strict Terraform init validation is still required for CI and release checks:

```bash
python scripts/validate_terraform_package.py --init-validate
```

If `terraform init` fails only because the IBM provider cannot be downloaded from
the Terraform Registry in a local, offline, VPN, or proxy-constrained
environment, use the explicit local-only tolerant mode:

```bash
python scripts/validate_terraform_package.py --init-validate --allow-provider-download-failure
```

Do not use the tolerant flag in CI; it is intended only to distinguish package
format validation from external provider download availability.

3. Start Streamlit from the repository root:

```bash
python -m streamlit run app.py
```

If the default port is busy, choose another local port:

```bash
python -m streamlit run app.py --server.port 8502
```

4. In the browser, click `Load Sample Workbook` for the first pass, or upload `samples/rvtools-small-complete.xlsx` manually. For a larger realistic exercise, upload `samples/SizingWorkshop-RVTools.xlsx`; readiness and preflight findings documented in `docs/sample-findings-walkthrough.md` are expected in that workbook.

5. Confirm the workbench renders without Streamlit errors:
   - Sidebar settings, pricing status, and upload control are visible.
   - `Help And Samples` explains the bundled samples, workshop practice findings, workflow, documentation references, and Terraform execution boundary.
   - `Load Sample Workbook` loads the bundled sample and shows the sample workbook status message.
   - The console does not repeat Streamlit `use_container_width` deprecation warnings.
   - `Overview` shows estate metrics, recommended next actions, assessment quality, and the Guided Migration Assistant checklist.
   - `Apply Safe Defaults` in the assistant initializes image import and remediation tracking only; it does not mark images imported, change target mappings, or build Terraform.
   - `Readiness`, `Remediation Backlog`, `VM Review`, `Wave Planning`, `Image Import Planning`, `Migration Ops`, `Networks`, `Storage`, and `Export` tabs open without tracebacks.
   - `Export` shows sections for package settings, subnet CIDRs, package summary, bundle contents preview, build readiness checklist, planning downloads, preflight review, Terraform validation guidance, and build/download controls.
   - `Bundle Contents Preview` lists major Terraform, handoff, planning-state, image-import, and operator files before build.
   - `Build Readiness Checklist` shows Ready, Review, and Blocked counts and summarizes readiness, wave planning, image import, planning-state, and preflight signals without blocking the build.
   - `Download Business Case (CSV)` is available from the `Export` planning downloads section.
   - `Session Safety` explains what planning-state JSON restores, what remains session-only, and when to download it.
   - `Download Planning State` is available, shows a planning-state summary, and imported planning state reports restored VM decisions, wave rows, remediation items, image groups, and skipped rows.
   - `Build Terraform Project` runs package preflight. If blockers are present, the build stops with findings grouped by fix category; after resolving or excluding affected VMs, it completes and shows `Project Ready`.
   - `Download Terraform Bundle` is available.

6. Download and inspect the Terraform bundle. It should include root `README.md` operator instructions, the root Terraform files, networking/storage/VSI module files, mapping CSVs, readiness exports, assessment quality exports, `preflight-report.json`, `preflight-report.csv`, `pricing-diagnostics.json`, `pricing-diagnostics.csv`, `cutover-readiness.csv`, `planning-state.json`, `image-import-variables.tfvars.example`, `migration-manifest.json`, and `migration-runbook.md`.

7. Extract the bundle to a temporary directory and run the validation harness:

```bash
python scripts/validate_terraform_package.py --dir .
```

The harness runs `terraform fmt -check -recursive` when Terraform is installed and skips clearly when the executable is unavailable. It can also build and check a representative sample package when called without `--zip` or `--dir`. When `--init-validate` is used, provider registry or download failures remain nonzero by default and include guidance for VPN, proxy, DNS, and retry troubleshooting.

You can still run Terraform formatting directly:

```bash
terraform fmt -check -recursive .
```

Run `terraform validate` only after `terraform init` has been intentionally performed for that temporary extraction. Do not initialize providers during lightweight browser validation unless provider download/network access is expected for the environment.

## Carbon Manual Smoke

After Carbon UI changes, start the Compose stack and open `http://localhost:3000`.
Use `docs/carbon-manual-uat-runbook.md` for formal reviewer execution,
`docs/carbon-uat-session-worksheet.md` as the fillable per-session working
copy, and `docs/carbon-manual-uat-evidence-index.md` to assemble the review packet. For a
quick developer smoke:

Automated Carbon checks mirror CI:

```bash
cd prototype/carbon-ui
npm audit --audit-level=high
npx tsc --noEmit --incremental false
npm test -- --runInBand
npm run build
```

When Carbon CI fails, download the `carbon-ui-failure-artifacts` artifact from
the run. It contains captured npm audit, TypeScript, Jest, and Next build logs
when those steps reached execution.
For hosted/pilot readiness changes, also review
`docs/carbon-hosted-operations-readiness.md` and confirm the branch records
health-check, alerting, logging, retention, backup/restore, artifact-handling,
support-owner, and rollback evidence requirements.
For promotion-decision changes, review
`docs/carbon-promotion-decision-packet.md` and confirm the packet references
parity, UAT, accessibility, hosted operations, rollback, validation, and open
issue evidence.
For issue-template changes, validate `.github/ISSUE_TEMPLATE/carbon-pilot-finding.yml`
and confirm it captures severity, workflow, reproduction steps, expected/actual
results, evidence, owner, mitigation, Streamlit fallback status, promotion
impact, and sensitive-data confirmation.
For dry-run evidence changes, confirm the evidence record names the commands
run, sample labels used, results observed, remaining human/hosted evidence gaps,
and sensitive-data boundary.

1. Confirm the shell loads and the left workflow navigation is visible.
2. Confirm the `Progress guide` shows workflow step statuses and a next
   recommended action that routes to the matching workflow.
3. Confirm the active workflow shows a compact `Complete when` checklist below
   its header and that it can be collapsed and expanded.
4. Open a workflow-header `Step help` control and confirm purpose,
   before-continuing, complete-when, common-mistakes, and next-step guidance
   appears.
5. Click `Open user guide` and confirm it opens `/help/user-guide` in a separate
   window or tab.
6. Click `Load sample workbook` from Workbook Intake for the bundled small
   sample path, then optionally upload `samples/rvtools-small-complete.xlsx`
   manually to confirm upload still overrides loaded sample data.
7. Confirm Workbook Intake shows the clean sample, real RVTools upload, and
   workshop sample choices, then shows `What happens next` after a workbook
   loads.
8. Confirm project save guidance appears near the saved-project controls and
   explains whether work is browser-only, queued for autosave, saved to
   Postgres, or blocked by API/database availability.
9. Visit VM Assignment, Network Plan, Remediation Backlog, Migration Ops, and
   Export Readiness.
10. Confirm Export Readiness shows summary metrics for saved-project state,
   planning gaps, preflight status, remediation queue, preview, and ZIP
   readiness.
11. Confirm Export Readiness shows a current-state banner with the next export
   action, such as saved project, planning gaps, preflight, blockers, preview,
   or download readiness.
12. Confirm Export Readiness shows recommended resolution order guidance from
   saved project through planning gaps, preflight, preview, and handoff
   download.
13. Confirm Export Readiness shows handoff guidance for package controls, key
   generated files, owner roles, and the Terraform execution boundary.
14. Run preflight or preview/download checks appropriate for the branch under
   test and confirm the success or error message explains what happened and the
   next action.
15. Confirm package preflight findings are grouped by severity and category,
   with blockers shown before warnings and informational findings.
16. Confirm package preflight search and severity filters narrow findings by VM,
   category, message, fix context, and severity.
17. Confirm active package preflight filter indicators appear and `Clear filters`
   restores the unfiltered findings.
18. When more than five package preflight findings exist, confirm Carbon shows
   the top findings first and can expand or collapse the full finding list.
19. For Carbon API failure-path changes, simulate or inspect failed upload,
   save, preflight, preview, and ZIP generation paths and confirm errors give a
   concrete recovery action instead of only a raw backend or browser exception.

## Carbon Private Performance Fixtures

Carbon includes checked-in performance guards for the sanitized sample workbooks.
For customer-scale RVTools exports, use private local fixtures instead of adding
workbooks to git. See [Carbon Performance Fixtures](carbon-performance-fixtures.md)
for the environment-variable workflow and sanitized evidence template.

## Container Validation
Run this checklist after changing deployment assets, dependencies, or Streamlit launch configuration. GitHub Actions also runs a container smoke job that builds the Docker image, starts Streamlit on a test host port, and checks `/_stcore/health`.

When a CI container smoke job fails, download the relevant failure artifact:
`streamlit-container-smoke-artifacts` for the single-container health check or
`compose-smoke-artifacts` for the Compose persistence stack. These include
container or Compose logs plus service status output when available.

1. Build the image:

```bash
docker build -t rvtools-to-ibm-cloud .
```

Or:

```bash
make docker-build
```

2. Run the container:

```bash
docker run --rm -p 8501:8501 rvtools-to-ibm-cloud
```

Or:

```bash
make docker-run
```

3. Confirm the app opens at:

```text
http://localhost:8501
```

4. Confirm the health endpoint returns successfully:

```bash
curl --fail http://localhost:8501/_stcore/health
```
