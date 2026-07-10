# Carbon Performance Fixtures

Use this process to validate Carbon against larger RVTools exports without
committing customer data to git.

## Data Handling

- Do not commit customer RVTools workbooks.
- Keep private workbooks outside the repository, or in a local ignored path.
- The repository `.gitignore` ignores `*.xlsx` files by default and only allows
  the sanitized files in `samples/`.
- Record evidence as counts and timings only. Do not paste VM names, host names,
  IP addresses, network names, owners, or application names into docs or issues.

## Run Private Workbook Summary Guards

Set `CARBON_PERF_CUSTOMER_WORKBOOKS` to one or more workbook paths separated by
the operating system path separator. On macOS/Linux, use `:` between paths.

```bash
CARBON_PERF_CUSTOMER_WORKBOOKS="/path/to/customer-a.xlsx:/path/to/customer-b.xlsx" \
venv/bin/python -m pytest tests/test_carbon_large_workbook_performance.py -q
```

Optional threshold override:

```bash
CARBON_PERF_CUSTOMER_SUMMARY_MAX_SECONDS=45 \
CARBON_PERF_CUSTOMER_WORKBOOKS="/path/to/customer-a.xlsx" \
venv/bin/python -m pytest tests/test_carbon_large_workbook_performance.py -q
```

When `CARBON_PERF_CUSTOMER_WORKBOOKS` is not set, the private-customer fixture
test is skipped and the checked-in sample workbook guards still run.

## Run Generated UI Filter Guards

The Carbon Jest suite also includes a generated 5,000-row UI guard for VM
Assignment search/sort and VM Overrides missing-reason filtering. Run it with:

```bash
cd prototype/carbon-ui
npm test -- --runInBand __tests__/large-ui-performance.test.ts
```

Optional threshold overrides:

```bash
CARBON_UI_ASSIGNMENT_FILTER_MAX_MS=250 \
CARBON_UI_OVERRIDES_FILTER_MAX_MS=250 \
npm test -- --runInBand __tests__/large-ui-performance.test.ts
```

## Evidence Template

Capture only sanitized evidence:

```text
Date:
Carbon branch/commit:
Environment:
Workbook label:
Workbook size category:
Assignment rows:
Summary parse elapsed:
Threshold:
Result:
Notes:
```

## Promotion Use

For Carbon promotion, collect at least two private workbook runs:

- One medium workbook close to a normal migration wave.
- One large workbook representative of the largest expected customer export.

Keep the raw workbooks outside git and store any sanitized evidence with the
promotion package or operations records.
