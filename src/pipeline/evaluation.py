"""Deterministic metrics derived from persisted terminal pipeline reports."""

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any, TypedDict


class EvaluationMetrics(TypedDict):
    total_runs: int
    first_attempt_static_approval: int
    after_repair_static_approval: int
    failures_by_stage: dict[str, int]
    behavioral_equivalence_tested: int
    simulated_generations: int
    real_generation_runs: int


def _validation_passed(report: Mapping[str, Any]) -> bool:
    validation = report.get("stages", [])
    return any(
        stage.get("stage") == "validation"
        and stage.get("status") == "success"
        and "ast_parse=passed" in stage.get("findings", [])
        and "lint=passed" in stage.get("findings", [])
        for stage in validation
        if isinstance(stage, Mapping)
    )


def calculate_metrics(records: Iterable[Mapping[str, Any]]) -> EvaluationMetrics:
    """Calculate metrics without dropping failures or simulated generations.

    ``records`` must contain terminal runs only. The caller owns that selection so
    pending rows are not mistaken for completed evaluations.
    """
    records = list(records)
    failures_by_stage: Counter[str] = Counter()
    first_attempt = 0
    after_repair = 0
    equivalence_tested = 0
    simulated = 0
    real_generation = 0

    for record in records:
        report = record.get("report") or {}
        if not isinstance(report, Mapping):
            report = {}
        attempts = report.get("traceability", {}).get("generation_attempts", 0)
        if _validation_passed(report):
            if attempts == 1:
                first_attempt += 1
            elif attempts >= 2:
                after_repair += 1

        for error in report.get("errors", []):
            if isinstance(error, Mapping):
                failures_by_stage[str(error.get("stage") or "unknown")] += 1

        if report.get("equivalence") == "tested":
            equivalence_tested += 1
        mode = report.get("generation_mode")
        if mode == "simulated":
            simulated += 1
        elif mode in {"openai", "gemini", "openrouter"}:
            real_generation += 1

    return {
        "total_runs": len(records),
        "first_attempt_static_approval": first_attempt,
        "after_repair_static_approval": after_repair,
        "failures_by_stage": dict(sorted(failures_by_stage.items())),
        "behavioral_equivalence_tested": equivalence_tested,
        "simulated_generations": simulated,
        "real_generation_runs": real_generation,
    }
