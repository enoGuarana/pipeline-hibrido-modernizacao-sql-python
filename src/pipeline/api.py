import hashlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .db import create_pending_run, finalize_run, lifespan_pool
from .graph import build_graph


class ModernizeRequest(BaseModel):
    source_code: str = Field(min_length=1)
    schema: str | None = None


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


@app.post("/modernize")
async def modernize(payload: ModernizeRequest, request: Request) -> JSONResponse:
    pool = getattr(request.app.state, "db_pool", None)
    graph = getattr(request.app.state, "graph", None)
    if pool is None or graph is None:
        return JSONResponse(status_code=503, content={"status": "degraded"})

    source_sha256 = hashlib.sha256(payload.source_code.encode("utf-8")).hexdigest()
    schema_sha256 = hashlib.sha256(payload.schema.encode("utf-8")).hexdigest() if payload.schema else None
    pending_report = {
        "status": "pending",
        "reason": "pipeline_started",
        "received_source_length": len(payload.source_code),
        "schema_provided": payload.schema is not None,
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
        "source_sha256": source_sha256,
        "schema_sha256": schema_sha256,
        "status": "pending",
        "stage_reports": [],
        "errors": [],
    }
    try:
        result = await graph.ainvoke(initial_state)
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
