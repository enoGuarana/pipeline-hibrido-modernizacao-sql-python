from typing import Any, TypedDict

from .contracts import (
    ExecutionError,
    ExecutionStatus,
    IntermediateRepresentation,
    ProviderName,
    StageReport,
)


class PipelineState(TypedDict, total=False):
    run_id: int
    source_code: str
    schema: str | None
    source_sha256: str
    schema_sha256: str | None
    # Configuração escolhida na entrada; api_key é transitória e nunca vai para
    # o relatório persistido.
    provider: ProviderName
    api_key: str | None
    model_name: str | None
    parsed: dict[str, Any]
    ir: IntermediateRepresentation
    analysis: dict[str, Any]
    generated_code: str
    generation_metadata: dict[str, Any]
    validation: dict[str, Any]
    status: ExecutionStatus
    report: dict[str, Any]
    stage_reports: list[StageReport]
    errors: list[ExecutionError]
    generation_attempts: int
