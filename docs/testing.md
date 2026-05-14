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
