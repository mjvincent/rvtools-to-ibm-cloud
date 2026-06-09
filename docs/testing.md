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
python -m pytest
python -m py_compile app.py rvtools_parser.py assessments.py assessment_quality.py sizing.py catalog_pricing.py terraform_renderer.py preflight.py ui.py logic_engine.py streamlit_app/*.py rvtools/*.py handoff/*.py models/*.py scripts/generate_pricing_cache.py scripts/validate_terraform_package.py
python scripts/validate_terraform_package.py
git diff --check
```

3. Start Streamlit from the repository root:

```bash
python -m streamlit run app.py
```

If the default port is busy, choose another local port:

```bash
python -m streamlit run app.py --server.port 8502
```

4. In the browser, upload `samples/rvtools-small-complete.xlsx` for the first pass. For a larger realistic exercise, upload `samples/SizingWorkshop-RVTools.xlsx`; readiness and preflight findings are expected in that workbook.

5. Confirm the workbench renders without Streamlit errors:
   - Sidebar settings, pricing status, and upload control are visible.
   - `Overview` shows estate metrics, recommended next actions, assessment quality, and the Guided Migration Assistant checklist.
   - `Apply Safe Defaults` in the assistant initializes image import and remediation tracking only; it does not mark images imported, change target mappings, or build Terraform.
   - `Readiness`, `Remediation Backlog`, `VM Review`, `Wave Planning`, `Image Import Planning`, `Migration Ops`, `Networks`, `Storage`, and `Export` tabs open without tracebacks.
   - `Export` shows sections for package settings, subnet CIDRs, package summary, planning downloads, preflight review, and build/download controls.
   - `Download Business Case (CSV)` is available from the `Export` planning downloads section.
   - `Download Planning State` is available, shows a planning-state summary, and imported planning state reports restored VM decisions, wave rows, remediation items, image groups, and skipped rows.
   - `Build Terraform Project` runs package preflight. If blockers are present, the build stops with findings; after resolving or excluding affected VMs, it completes and shows `Project Ready`.
   - `Download Terraform Bundle` is available.

6. Download and inspect the Terraform bundle. It should include the root Terraform files, networking/storage/VSI module files, mapping CSVs, readiness exports, assessment quality exports, `preflight-report.json`, `preflight-report.csv`, `pricing-diagnostics.json`, `pricing-diagnostics.csv`, `cutover-readiness.csv`, `planning-state.json`, `image-import-variables.tfvars.example`, `migration-manifest.json`, and `migration-runbook.md`.

7. Extract the bundle to a temporary directory and run the validation harness:

```bash
python scripts/validate_terraform_package.py --dir .
```

The harness runs `terraform fmt -check -recursive` when Terraform is installed and skips clearly when the executable is unavailable. It can also build and check a representative sample package when called without `--zip` or `--dir`.

You can still run Terraform formatting directly:

```bash
terraform fmt -check -recursive .
```

Run `terraform validate` only after `terraform init` has been intentionally performed for that temporary extraction. Do not initialize providers during lightweight browser validation unless provider download/network access is expected for the environment.

## Container Validation
Run this checklist after changing deployment assets, dependencies, or Streamlit launch configuration. GitHub Actions also runs a container smoke job that builds the Docker image, starts Streamlit on a test host port, and checks `/_stcore/health`.

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
