from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .db import lifespan_pool


class ModernizeRequest(BaseModel):
    source_code: str = Field(min_length=1)
    schema: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with lifespan_pool() as pool:
        app.state.db_pool = pool
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
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded"})
    return {"status": "ok"}


@app.post("/modernize", status_code=501)
async def modernize(payload: ModernizeRequest) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "status": "pending",
            "message": "Os quatro nós ainda não foram implementados; nenhum código equivalente foi produzido.",
            "received_source_length": len(payload.source_code),
        },
    )

