from pipeline.evaluation import calculate_metrics


def _report(*, attempts: int, valid: bool, mode: str, errors=None, equivalence="not_tested"):
    findings = ["ast_parse=passed", "lint=passed"] if valid else []
    return {
        "stages": [{"stage": "validation", "status": "success" if valid else "failure", "findings": findings}],
        "errors": errors or [],
        "generation_mode": mode,
        "equivalence": equivalence,
        "traceability": {"generation_attempts": attempts},
    }


def test_metrics_keep_failures_and_simulated_runs_in_denominator():
    metrics = calculate_metrics(
        [
            {"id": 1, "status": "success", "report": _report(attempts=1, valid=True, mode="simulated")},
            {
                "id": 2,
                "status": "failure",
                "report": _report(
                    attempts=1,
                    valid=False,
                    mode="unknown",
                    errors=[{"code": "LLM_GENERATION", "stage": "generation"}],
                ),
            },
            {
                "id": 3,
                "status": "success",
                "report": _report(attempts=2, valid=True, mode="gemini", equivalence="tested"),
            },
        ]
    )

    assert metrics == {
        "total_runs": 3,
        "first_attempt_static_approval": 1,
        "after_repair_static_approval": 1,
        "failures_by_stage": {"generation": 1},
        "behavioral_equivalence_tested": 1,
        "simulated_generations": 1,
        "real_generation_runs": 1,
    }
