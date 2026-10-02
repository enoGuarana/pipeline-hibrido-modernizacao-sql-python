import hashlib
import json

import pytest

from pipeline.artifacts import ArtifactExportError, export_run_artifact


def _real_run():
    source_code = "CREATE FUNCTION example() RETURNS INT ...;\n"
    generated_code = "async def example(connection):\n    return 1\n"
    return {
        "id": 42,
        "source_code": source_code,
        "generated_code": generated_code,
        "status": "success",
        "created_at": "2026-10-02T10:00:00Z",
        "report": {
            "generation_mode": "gemini",
            "generation_metadata": {"model": "test-model", "prompt_version": "modernize_v1"},
            "equivalence": "not_tested",
            "traceability": {
                "source_sha256": hashlib.sha256(source_code.encode()).hexdigest(),
                "generated_code_sha256": hashlib.sha256(generated_code.encode()).hexdigest(),
            },
        },
    }


def test_export_real_run_creates_reviewable_bundle(tmp_path):
    artifact_dir = export_run_artifact(_real_run(), tmp_path)

    assert (artifact_dir / "source.sql").exists()
    assert (artifact_dir / "generated.py").exists()
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["run_id"] == 42
    assert metadata["equivalence"] == "not_tested"
    assert (artifact_dir / "source.sql").read_bytes() == _real_run()["source_code"].encode()
    assert (artifact_dir / "generated.py").read_bytes() == _real_run()["generated_code"].encode()
    assert hashlib.sha256((artifact_dir / "source.sql").read_bytes()).hexdigest() == metadata["source_sha256"]
    assert (
        hashlib.sha256((artifact_dir / "generated.py").read_bytes()).hexdigest()
        == metadata["generated_code_sha256"]
    )


def test_export_rejects_simulated_run(tmp_path):
    run = _real_run()
    run["report"]["generation_mode"] = "simulated"

    with pytest.raises(ArtifactExportError, match="not a real Gemini generation"):
        export_run_artifact(run, tmp_path)


def test_export_preserves_real_failed_attempt_with_generated_code(tmp_path):
    run = _real_run()
    run["status"] = "failure"
    run["report"]["errors"] = [{"code": "VALIDATION_LINT", "stage": "validation"}]

    artifact_dir = export_run_artifact(run, tmp_path)

    assert (artifact_dir / "generated.py").exists()
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failure"
