"""Export a persisted real Gemini run to results/run-<id>."""

import argparse
import asyncio
from pathlib import Path

from pipeline.artifacts import ArtifactExportError, export_run_artifact
from pipeline.db import fetch_run_for_artifact, make_pool


async def _export(run_id: int, output_root: Path) -> Path:
    pool = make_pool()
    await pool.open()
    try:
        run = await fetch_run_for_artifact(pool, run_id)
    finally:
        await pool.close()
    if run is None:
        raise SystemExit(f"run {run_id} was not found")
    return export_run_artifact(run, output_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id", type=int)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    try:
        artifact_dir = asyncio.run(
            _export(args.run_id, args.output),
            loop_factory=asyncio.SelectorEventLoop,
        )
    except ArtifactExportError as exc:
        raise SystemExit(str(exc)) from exc
    print(artifact_dir)


if __name__ == "__main__":
    main()
