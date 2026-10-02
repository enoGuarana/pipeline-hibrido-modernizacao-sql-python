"""Calculate reproducible metrics from exported result directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pipeline.evaluation import calculate_metrics


def load_exported_records(results_dir: Path) -> tuple[list[dict[str, Any]], list[int]]:
    """Load only complete exported runs and return records plus their IDs."""

    records: list[dict[str, Any]] = []
    run_ids: list[int] = []
    for run_dir in sorted(results_dir.glob("run-*")):
        if not run_dir.is_dir():
            continue
        try:
            run_id = int(run_dir.name.removeprefix("run-"))
        except ValueError:
            continue
        report_path = run_dir / "report.json"
        metadata_path = run_dir / "metadata.json"
        if not report_path.is_file() or not metadata_path.is_file():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        records.append({"run_id": run_id, "report": report, "metadata": metadata})
        run_ids.append(run_id)
    return records, run_ids


def build_evaluation(results_dir: Path) -> dict[str, Any]:
    records, run_ids = load_exported_records(results_dir)
    return {
        "dataset": str(results_dir),
        "run_ids": run_ids,
        "denominator": len(records),
        "metrics": calculate_metrics(records),
        "limitations": [
            "Static approval does not establish behavioral equivalence.",
            "Only exported directories containing report.json and metadata.json are included.",
            "No generated module is executed by this script.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=PROJECT_ROOT / "results",
        help="Directory containing run-* exported result directories.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()
    evaluation = build_evaluation(args.results_dir)
    rendered = json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
