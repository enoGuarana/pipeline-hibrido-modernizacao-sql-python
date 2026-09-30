from typing import Any, Literal, TypedDict


class PipelineState(TypedDict, total=False):
    source_code: str
    schema: str | None
    parsed: dict[str, Any]
    analysis: dict[str, Any]
    generated_code: str
    validation: dict[str, Any]
    status: Literal["success", "failure", "partial", "pending"]
    report: dict[str, Any]

