#!/usr/bin/env python3
"""Collect sanitized Carbon workbook performance evidence.

The script accepts local workbook paths, but intentionally does not print those
paths or workbook filenames. Use caller-provided labels such as "medium-wave"
or "large-estate" for evidence records.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import warnings
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
logging.getLogger("httpx").setLevel(logging.WARNING)

from fastapi.testclient import TestClient  # noqa: E402

from prototype.api.app import app  # noqa: E402


DEFAULT_THRESHOLD_SECONDS = 30.0
CUSTOMER_WORKBOOKS_ENV = "CARBON_PERF_CUSTOMER_WORKBOOKS"
CUSTOMER_THRESHOLD_ENV = "CARBON_PERF_CUSTOMER_SUMMARY_MAX_SECONDS"


def git_value(args: list[str], fallback: str = "unknown") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return fallback
    return result.stdout.strip() or fallback


def upload_summary(client: TestClient, workbook_path: Path):
    with workbook_path.open("rb") as workbook:
        return client.post(
            "/api/workbooks/summary",
            files={
                "workbook": (
                    workbook_path.name,
                    workbook,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )


def collect_record(
    client: TestClient,
    workbook_path: Path,
    label: str,
    threshold_seconds: float,
) -> dict[str, object]:
    started = time.perf_counter()
    response = upload_summary(client, workbook_path)
    elapsed = time.perf_counter() - started

    row_count = 0
    status_code = response.status_code
    if response.status_code == 200:
        payload = response.json()
        row_count = len(payload.get("assignment_rows", []))

    return {
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": git_value(["branch", "--show-current"]),
        "commit": git_value(["rev-parse", "--short", "HEAD"]),
        "workbook_label": label,
        "assignment_rows": row_count,
        "summary_parse_elapsed_seconds": round(elapsed, 3),
        "threshold_seconds": threshold_seconds,
        "result": "pass" if response.status_code == 200 and elapsed < threshold_seconds else "fail",
        "http_status": status_code,
    }


def parse_labeled_workbook(value: str, index: int) -> tuple[str, Path]:
    if "=" in value:
        label, raw_path = value.split("=", 1)
        label = label.strip() or f"workbook-{index}"
    else:
        label, raw_path = f"workbook-{index}", value
    return label, Path(raw_path).expanduser()


def parse_labeled_workbooks(values: list[str]) -> list[tuple[str, Path]]:
    return [
        parse_labeled_workbook(value, index)
        for index, value in enumerate(values, start=1)
    ]


def workbook_values_from_env(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [value for value in raw_value.split(os.pathsep) if value.strip()]


def render_text(records: list[dict[str, object]]) -> str:
    lines = []
    for record in records:
        lines.extend(
            [
                f"Date: {record['date']}",
                f"Carbon branch/commit: {record['branch']} / {record['commit']}",
                f"Workbook label: {record['workbook_label']}",
                f"Assignment rows: {record['assignment_rows']}",
                f"Summary parse elapsed: {record['summary_parse_elapsed_seconds']}s",
                f"Threshold: {record['threshold_seconds']}s",
                f"Result: {record['result']}",
                f"HTTP status: {record['http_status']}",
                "Notes:",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Collect sanitized Carbon workbook summary performance evidence. "
            "Workbook paths are read locally but never printed."
        )
    )
    parser.add_argument(
        "workbooks",
        nargs="*",
        help=(
            "Workbook path or label=/path/to/workbook.xlsx. Labels are printed; "
            "paths and filenames are not."
        ),
    )
    parser.add_argument(
        "--from-env",
        action="store_true",
        help=(
            f"Read workbook paths from {CUSTOMER_WORKBOOKS_ENV}. Values may be "
            f"plain paths or label=path entries separated by {os.pathsep!r}."
        ),
    )
    parser.add_argument(
        "--threshold-seconds",
        type=float,
        default=None,
        help=f"Pass/fail threshold per workbook. Default: {DEFAULT_THRESHOLD_SECONDS}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file for sanitized evidence. The path is not printed.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit sanitized JSON instead of text evidence blocks.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    workbook_values = list(args.workbooks)
    if args.from_env:
        workbook_values.extend(workbook_values_from_env(os.environ.get(CUSTOMER_WORKBOOKS_ENV)))
    if not workbook_values:
        print(
            "Error: provide workbook paths or use --from-env with "
            f"{CUSTOMER_WORKBOOKS_ENV}.",
            file=sys.stderr,
        )
        return 2

    threshold_seconds = args.threshold_seconds
    if threshold_seconds is None:
        threshold_seconds = float(os.environ.get(CUSTOMER_THRESHOLD_ENV, DEFAULT_THRESHOLD_SECONDS))

    labeled_paths = parse_labeled_workbooks(workbook_values)
    missing = [(label, path) for label, path in labeled_paths if not path.exists()]
    if missing:
        for label, _path in missing:
            print(f"Error: workbook for label '{label}' does not exist.", file=sys.stderr)
        return 2

    client = TestClient(app)
    records = [
        collect_record(client, path, label, threshold_seconds)
        for label, path in labeled_paths
    ]
    if args.json:
        output = json.dumps(records, indent=2)
    else:
        output = render_text(records)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{output}\n", encoding="utf-8")
        print("Sanitized evidence written.")
    else:
        print(output)
    return 0 if all(record["result"] == "pass" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
