"""Export verified real-generation runs as reviewable result bundles."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ArtifactExportError(ValueError):
    """The persisted run is not eligible for a real-generation artifact."""


def export_run_artifact(run: Mapping[str, Any], output_root: Path) -> Path:
    """Write one immutable artifact bundle without executing generated code."""
    report = run.get("report")
    if not isinstance(report, Mapping):
        raise ArtifactExportError("run report is missing or invalid")
    if run.get("status") not in {"success", "partial", "failure"}:
        raise ArtifactExportError("only terminal runs can be exported")
    if report.get("generation_mode") != "gemini":
        raise ArtifactExportError("run is not a real Gemini generation")
    generated_code = run.get("generated_code")
    if not isinstance(generated_code, str) or not generated_code.strip():
        raise ArtifactExportError("run has no generated code")

    run_id = int(run["id"])
    artifact_dir = output_root / f"run-{run_id}"
    if artifact_dir.exists():
        raise ArtifactExportError(f"artifact already exists: {artifact_dir}")
    artifact_dir.mkdir(parents=True)

    source_code = str(run.get("source_code") or "")
    traceability = report.get("traceability", {})
    if not isinstance(traceability, Mapping):
        traceability = {}
    metadata = {
        "run_id": run_id,
        "status": run.get("status"),
        "created_at": run.get("created_at"),
        "source_sha256": traceability.get("source_sha256"),
        "generated_code_sha256": traceability.get("generated_code_sha256"),
        "generation_metadata": report.get("generation_metadata", {}),
        "equivalence": report.get("equivalence", "not_tested"),
        "limitations": [
            "Static validation does not establish behavioral equivalence.",
            "The generated module was stored for review and was not executed by the API.",
        ],
    }
    (artifact_dir / "source.sql").write_text(source_code, encoding="utf-8")
    (artifact_dir / "generated.py").write_text(generated_code, encoding="utf-8")
    (artifact_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return artifact_dir
