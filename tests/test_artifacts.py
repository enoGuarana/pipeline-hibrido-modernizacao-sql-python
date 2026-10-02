import json

import pytest

from pipeline.artifacts import ArtifactExportError, export_run_artifact


def _real_run():
    return {
        "id": 42,
        "source_code": "CREATE FUNCTION example() RETURNS INT ...;",
        "generated_code": "async def example(connection):\n    return 1\n",
        "status": "success",
        "created_at": "2026-10-02T10:00:00Z",
        "report": {
            "generation_mode": "openai",
            "generation_metadata": {"model": "test-model", "prompt_version": "modernize_v1"},
            "equivalence": "not_tested",
            "traceability": {"source_sha256": "source", "generated_code_sha256": "generated"},
        },
    }


def test_export_real_run_creates_reviewable_bundle(tmp_path):
    artifact_dir = export_run_artifact(_real_run(), tmp_path)

    assert (artifact_dir / "source.sql").exists()
    assert (artifact_dir / "generated.py").exists()
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["run_id"] == 42
    assert metadata["equivalence"] == "not_tested"


def test_export_rejects_simulated_run(tmp_path):
    run = _real_run()
    run["report"]["generation_mode"] = "simulated"

    with pytest.raises(ArtifactExportError, match="not a real OpenAI generation"):
        export_run_artifact(run, tmp_path)
