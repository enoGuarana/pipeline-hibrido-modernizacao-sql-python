"""Typed contracts shared by the API, graph nodes, and persistence layer."""

from typing import Literal, TypedDict

ExecutionStatus = Literal["success", "failure", "partial", "pending"]
StageStatus = Literal["not_started", "running", "success", "failure", "partial"]
ParameterMode = Literal["IN", "OUT", "INOUT", "unknown"]


class InputContract(TypedDict):
    source_code: str
    schema: str | None


class ParameterContract(TypedDict, total=False):
    name: str
    mode: ParameterMode
    data_type: str | None
    default: str | None
    source_span: tuple[int, int] | None


class IntermediateRepresentation(TypedDict, total=False):
    routine_name: str | None
    routine_kind: Literal["function", "procedure", "unknown"]
    language: str | None
    parameters: list[ParameterContract]
    return_type: str | None
    variables: list[dict[str, str | None]]
    operations: list[str]
    tables: list[str]
    function_calls: list[str]
    source_spans: list[dict[str, int | str]]
    unsupported_constructs: list[str]


class ExecutionError(TypedDict, total=False):
    code: str
    message: str
    stage: str
    recoverable: bool
    details: dict[str, str | int | float | bool | None]


class StageReport(TypedDict, total=False):
    stage: str
    status: StageStatus
    findings: list[str]
    decisions: list[str]
    warnings: list[str]
    errors: list[ExecutionError]
    duration_ms: float | None


class ModernizeResponseContract(TypedDict, total=False):
    run_id: int
    status: ExecutionStatus
    generated_code: str | None
    report: dict[str, object]
    message: str
    received_source_length: int
