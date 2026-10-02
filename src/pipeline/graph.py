"""Initial four-node flow for the supported Anexo B shape."""

import ast
import hashlib
import os
import subprocess
import sys
from typing import Any

from langgraph.graph import END, START, StateGraph

from .contracts import ExecutionError, StageReport
from .llm.client import LLMError, build_prompt, generate
from .parsing import parse_routine
from .state import PipelineState


def _stage(
    name: str,
    status: str,
    *,
    findings: list[str] | None = None,
    decisions: list[str] | None = None,
    warnings: list[str] | None = None,
    errors: list[ExecutionError] | None = None,
) -> StageReport:
    return {
        "stage": name,
        "status": status,  # type: ignore[typeddict-item]
        "findings": findings or [],
        "decisions": decisions or [],
        "warnings": warnings or [],
        "errors": errors or [],
        "duration_ms": None,
    }


def _with_stage(state: PipelineState, report: StageReport) -> list[StageReport]:
    return [*state.get("stage_reports", []), report]


def _error(code: str, message: str, stage: str, *, recoverable: bool = False) -> ExecutionError:
    return {"code": code, "message": message, "stage": stage, "recoverable": recoverable}


def _failed(state: PipelineState, report: StageReport, error: ExecutionError) -> dict[str, Any]:
    return {
        "status": "failure",
        "stage_reports": _with_stage(state, report),
        "errors": [*state.get("errors", []), error],
    }


def _skipped(state: PipelineState, name: str) -> dict[str, Any]:
    return {"stage_reports": _with_stage(state, _stage(name, "failure", warnings=["stage_skipped"]))}


def parse_node(state: PipelineState) -> dict[str, Any]:
    stage = "parsing"
    source = state.get("source_code", "")
    parsed = parse_routine(source)
    if parsed is None:
        error = _error("PARSE_UNSUPPORTED", "Routine wrapper or dollar-quoted body not found", stage)
        return _failed(state, _stage(stage, "failure", errors=[error]), error)
    parsed_body, ir = parsed
    return {
        "parsed": parsed_body,
        "ir": ir,
        "stage_reports": _with_stage(
            state,
            _stage(
                stage,
                "success",
                findings=["routine_wrapper", "dollar_quoted_body", "parameters", "variables", "operations", "tables"],
                warnings=["body parsing is structural classification, not a complete PL/pgSQL AST"],
            ),
        ),
        "status": "pending",
    }


def semantic_analysis_node(state: PipelineState) -> dict[str, Any]:
    stage = "semantic_analysis"
    if state.get("status") == "failure":
        return _skipped(state, stage)
    ir = state.get("ir", {})
    operations = ir.get("operations", [])
    findings = [
        f"routine={ir.get('routine_name')}",
        f"parameters={len(ir.get('parameters', []))}",
        f"variables={len(ir.get('variables', []))}",
        *[f"operation={operation}" for operation in operations],
        *[f"table={table}" for table in ir.get("tables", [])],
    ]
    risks = []
    risk_by_operation = {
        "cursor": "cursor_or_row_by_row_processing",
        "loop": "loop_control_flow",
        "exception": "exception_handler_and_rollback_semantics",
        "raise": "raise_or_notice_behavior",
        "locking": "explicit_row_locking",
        "jsonb": "jsonb_shape_and_null_semantics",
        "cte_recursive": "recursive_cte",
    }
    risks.extend(risk_by_operation[operation] for operation in operations if operation in risk_by_operation)
    unsupported = ir.get("unsupported_constructs", [])
    analysis = {
        "facts": findings,
        "risks": risks,
        "inferences": ["BEGIN/END procedural blocks are not classified as explicit transactions"],
        "unsupported_constructs": unsupported,
    }
    status = "partial" if unsupported else "pending"
    return {
        "analysis": analysis,
        "stage_reports": _with_stage(
            state,
            _stage(
                stage,
                "success",
                findings=findings,
                decisions=["Preserve NUMERIC semantics and distinguish facts from inferences"],
                warnings=["unsupported constructs require manual review"] if unsupported else [],
            ),
        ),
        "status": status,
    }


async def generation_node(state: PipelineState) -> dict[str, Any]:
    stage = "generation"
    if state.get("status") == "failure":
        return _skipped(state, stage)
    if os.getenv("GEMINI_API_KEY"):
        try:
            result = await generate(
                prompt=build_prompt(
                    source_code=state.get("source_code", ""),
                    ir=dict(state.get("ir", {})),
                    analysis=state.get("analysis", {}),
                    schema=state.get("schema"),
                )
            )
        except LLMError as exc:
            error = _error("LLM_GENERATION", str(exc), stage)
            return _failed(state, _stage(stage, "failure", errors=[error]), error)
        return {
            "generated_code": result.code,
            "generation_metadata": result.metadata,
            "generation_attempts": 1,
            "stage_reports": _with_stage(
                state,
                _stage(stage, "success", decisions=["Use Gemini API with versioned context"]),
            ),
            "status": state.get("status", "pending"),
        }
    routine_name = state.get("ir", {}).get("routine_name") or "generated_routine"
    generated_code = f'''async def {routine_name}(connection, *args, **kwargs):
    """Simulated output; not an executable translation."""
    raise NotImplementedError("simulated generation")
'''
    return {
        "generated_code": generated_code,
        "generation_metadata": {
            "provider": "simulated",
            "model": None,
            "prompt_version": None,
            "response_id": None,
            "usage": None,
        },
        "generation_attempts": 1,
        "stage_reports": _with_stage(
            state,
            _stage(
                stage,
                "success",
                decisions=["Use simulated generator for the first flow"],
                warnings=["generated code is a development stub and is not equivalent"],
            ),
        ),
        "status": "pending",
    }


def validation_node(state: PipelineState) -> dict[str, Any]:
    stage = "validation"
    if state.get("status") == "failure":
        return _skipped(state, stage)
    code = state.get("generated_code", "")
    try:
        ast.parse(code, filename="generated.py", mode="exec")
    except SyntaxError as exc:
        error = _error("VALIDATION_SYNTAX", str(exc), stage)
        return _failed(state, _stage(stage, "failure", errors=[error]), error)

    try:
        lint = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--stdin-filename", "generated.py", "-"],
            input=code,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        error = _error("VALIDATION_LINT_UNAVAILABLE", str(exc), stage)
        return _failed(state, _stage(stage, "failure", errors=[error]), error)
    if lint.returncode != 0:
        error = _error("VALIDATION_LINT", lint.stdout or lint.stderr, stage)
        return _failed(state, _stage(stage, "failure", errors=[error]), error)

    return {
        "validation": {"ast_parse": "passed", "lint": "passed", "equivalence": "not_tested"},
        "stage_reports": _with_stage(
            state,
            _stage(
                stage,
                "success",
                findings=["ast_parse=passed", "lint=passed"],
                warnings=["static validation does not establish equivalence"],
            ),
        ),
        "status": "pending",
    }


def _route_after_validation(state: PipelineState) -> str:
    errors = state.get("errors", [])
    if any(error.get("code", "").startswith("LLM_") for error in errors):
        return "finalization"
    validation_error = any(error.get("code", "").startswith("VALIDATION_") for error in errors)
    if validation_error and os.getenv("GEMINI_API_KEY") and state.get("generation_attempts", 1) < 2:
        return "repair"
    return "finalization"


async def repair_node(state: PipelineState) -> dict[str, Any]:
    stage = "repair"
    previous_code = state.get("generated_code", "")
    errors = state.get("errors", [])
    repair_prompt = build_prompt(
        source_code=state.get("source_code", ""),
        ir=dict(state.get("ir", {})),
        analysis={
            **state.get("analysis", {}),
            "validation_errors": errors,
            "previous_generated_code": previous_code,
            "instruction": "Return corrected Python only. This is the single allowed repair attempt.",
        },
        schema=state.get("schema"),
    )
    try:
        result = await generate(prompt=repair_prompt)
    except LLMError as exc:
        error = _error("LLM_REPAIR", str(exc), stage)
        return _failed(state, _stage(stage, "failure", errors=[error]), error)
    return {
        "generated_code": result.code,
        "generation_metadata": {**result.metadata, "repaired": True},
        "generation_attempts": state.get("generation_attempts", 1) + 1,
        "errors": [],
        "status": "pending",
        "stage_reports": _with_stage(
            state,
            _stage(stage, "success", warnings=["previous generated code and validation report were preserved"]),
        ),
    }


def finalize_node(state: PipelineState) -> dict[str, Any]:
    errors = state.get("errors", [])
    status = "failure" if errors else ("partial" if state.get("status") == "partial" else "success")
    finalization_report = _stage("finalization", "success")
    all_stage_reports = _with_stage(state, finalization_report)
    return {
        "status": status,
        "report": {
            "stages": all_stage_reports,
            "errors": errors,
            "generation_mode": state.get("generation_metadata", {}).get("provider", "unknown"),
            "generation_metadata": state.get("generation_metadata", {}),
            "equivalence": "not_tested",
            "traceability": {
                "run_id": state.get("run_id"),
                "source_sha256": state.get("source_sha256"),
                "schema_sha256": state.get("schema_sha256"),
                "generated_code_sha256": hashlib.sha256(state["generated_code"].encode("utf-8")).hexdigest()
                if state.get("generated_code")
                else None,
                "generation_attempts": state.get("generation_attempts", 0),
            },
        },
        "stage_reports": all_stage_reports,
    }


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("parsing", parse_node)
    graph.add_node("semantic_analysis", semantic_analysis_node)
    graph.add_node("generation", generation_node)
    graph.add_node("validation", validation_node)
    graph.add_node("repair", repair_node)
    graph.add_node("finalization", finalize_node)
    graph.add_edge(START, "parsing")
    graph.add_edge("parsing", "semantic_analysis")
    graph.add_edge("semantic_analysis", "generation")
    graph.add_edge("generation", "validation")
    graph.add_conditional_edges(
        "validation",
        _route_after_validation,
        {"repair": "repair", "finalization": "finalization"},
    )
    graph.add_edge("repair", "validation")
    graph.add_edge("finalization", END)
    return graph.compile()
