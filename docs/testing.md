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
streamlit run app.py
```

If the default port is busy, choose another local port:

```bash
streamlit run app.py --server.port 8502
```

4. In the browser, upload `RVTools_VA-site-1.xlsx` or another representative RVTools workbook.

5. Confirm the workbench renders without Streamlit errors:
   - Sidebar settings, pricing status, and upload control are visible.
   - `Overview` shows estate metrics, recommended next actions, and assessment quality.
   - `Readiness`, `Remediation Backlog`, `VM Review`, `Wave Planning`, `Image Import Planning`, `Migration Ops`, `Networks`, `Storage`, and `Export` tabs open without tracebacks.
   - `Download Business Case (CSV)` is available from `Export`.
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
