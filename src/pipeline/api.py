import hashlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .contracts import ProviderName
from .db import create_pending_run, fetch_evaluation_runs, finalize_run, lifespan_pool
from .evaluation import calculate_metrics
from .graph import build_graph
from .observability import observation


class ModernizeRequest(BaseModel):
    # O SQL chega como texto bruto para preservar a origem; o schema é apenas
    # contexto opcional e não dispara alterações automáticas no banco.
    source_code: str = Field(min_length=1)
    schema: str | None = None
    provider: ProviderName = "gemini"
    api_key: str | None = Field(default=None, repr=False)
    model_name: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with lifespan_pool() as pool:
        app.state.db_pool = pool
        app.state.graph = build_graph()
        yield


app = FastAPI(title="Pipeline Híbrido SQL → Python", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health(request: Request) -> dict[str, str]:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        return JSONResponse(status_code=503, content={"status": "degraded"})
    try:
        async with pool.connection() as connection:
            await connection.execute("SELECT 1")
    except Exception:  # noqa: BLE001 - API boundary must report DB health failure
        return JSONResponse(status_code=503, content={"status": "degraded"})
    return {"status": "ok"}


@app.get("/evaluation")
async def evaluation(request: Request) -> JSONResponse:
    """Return reproducible metrics from all persisted terminal executions."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        return JSONResponse(status_code=503, content={"status": "degraded"})
    try:
        records = await fetch_evaluation_runs(pool)
        metrics = calculate_metrics(records)
    except Exception:  # noqa: BLE001 - API boundary must report DB failure
        return JSONResponse(status_code=503, content={"status": "degraded"})
    return JSONResponse(
        status_code=200,
        content={
            "metrics": metrics,
            "evaluated_run_ids": [record["id"] for record in records],
            "limitations": [
                "Static approval does not establish behavioral equivalence.",
                "Behavioral equivalence is counted only when a report explicitly marks it as tested.",
                "The denominator includes terminal failures and simulated generations.",
            ],
        },
    )


@app.post("/modernize")
async def modernize(payload: ModernizeRequest, request: Request) -> JSONResponse:
    # A API não executa o Python gerado: ela orquestra o grafo e persiste a
    # evidência de cada tentativa para revisão posterior.
    pool = getattr(request.app.state, "db_pool", None)
    graph = getattr(request.app.state, "graph", None)
    if pool is None or graph is None:
        return JSONResponse(status_code=503, content={"status": "degraded"})

    source_sha256 = hashlib.sha256(payload.source_code.encode("utf-8")).hexdigest()
    schema_sha256 = hashlib.sha256(payload.schema.encode("utf-8")).hexdigest() if payload.schema else None
    pending_report = {
        # Registrar pending antes do grafo permite rastrear que a execução
        # começou, mesmo que uma falha ocorra antes do primeiro nó.
        "status": "pending",
        "reason": "pipeline_started",
        "received_source_length": len(payload.source_code),
        "schema_provided": payload.schema is not None,
        "provider": payload.provider,
        "model_name": payload.model_name,
        "source_sha256": source_sha256,
        "schema_sha256": schema_sha256,
    }
    try:
        run_id = await create_pending_run(
            pool,
            source_code=payload.source_code,
            report=pending_report,
        )
    except Exception:  # noqa: BLE001 - persistence failure is converted to 503
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "message": "Não foi possível persistir a execução."},
        )

    initial_state = {
        "run_id": run_id,
        "source_code": payload.source_code,
        "schema": payload.schema,
        "provider": payload.provider,
        "api_key": payload.api_key,
        "model_name": payload.model_name,
        "source_sha256": source_sha256,
        "schema_sha256": schema_sha256,
        "status": "pending",
        "stage_reports": [],
        "errors": [],
    }
    try:
        with observation(
            "modernize",
            input_data={"run_id": run_id, "source_sha256": source_sha256},
            metadata={"component": "pipeline", "route": "/modernize"},
            as_type="agent",
        ) as trace:
            # O LangGraph controla a sequência dos nós; a API permanece
            # responsável pelo ciclo de vida HTTP e pela persistência final.
            result = await graph.ainvoke(initial_state)
            if trace is not None:
                trace.update(output={"run_id": run_id, "status": result.get("status")})
        status = result.get("status", "failure")
        report = result.get("report", {})
        await finalize_run(
            pool,
            run_id=run_id,
            status=status,
            report=report,
            generated_code=result.get("generated_code"),
        )
    except Exception as exc:  # noqa: BLE001 - controlled pipeline failure path
        # Este é o último contorno de segurança: uma exceção inesperada vira
        # relatório de falha e tenta finalizar o pending, sem ocultar a causa.
        failure_report = {
            "status": "failure",
            "errors": [{"code": "PIPELINE_EXCEPTION", "message": str(exc), "stage": "pipeline"}],
        }
        try:
            await finalize_run(pool, run_id=run_id, status="failure", report=failure_report)
        except Exception:  # noqa: BLE001 - report inability to finalize explicitly
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "message": "Falha na pipeline e na persistência final."},
            )
        return JSONResponse(status_code=500, content={"run_id": run_id, **failure_report})

    response = {
        "run_id": run_id,
        "status": status,
        "generated_code": result.get("generated_code"),
        "report": report,
    }
    return JSONResponse(status_code=200 if status == "success" else 422, content=response)
