import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS modernization_history (
    id BIGSERIAL PRIMARY KEY,
    source_code TEXT NOT NULL,
    generated_code TEXT,
    report JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure', 'partial', 'pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


def database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/modernization")


def make_pool() -> AsyncConnectionPool:
    # O pool evita abrir uma conexão por etapa e permite que a API reutilize a
    # infraestrutura sem acoplar o grafo ao ciclo de vida do banco.
    return AsyncConnectionPool(
        conninfo=database_url(),
        min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
        max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
        open=False,
    )


async def initialize_database(pool: AsyncConnectionPool) -> None:
    async with pool.connection() as connection:
        await connection.execute(CREATE_HISTORY_TABLE)
        await connection.commit()


async def create_pending_run(
    pool: AsyncConnectionPool,
    *,
    source_code: str,
    report: dict[str, object],
) -> int:
    """Create the history row before pipeline processing starts."""
    # A execução nasce como pending para não desaparecer se falhar antes do
    # primeiro nó ou durante uma chamada externa.
    async with pool.connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO modernization_history (source_code, report, status)
                VALUES (%s, %s, 'pending')
                RETURNING id
                """,
                (source_code, Jsonb(report)),
            )
            row = await cursor.fetchone()
        await connection.commit()
    if row is None:
        raise RuntimeError("Persisted run did not receive an identifier")
    return int(row[0])


async def finalize_run(
    pool: AsyncConnectionPool,
    *,
    run_id: int,
    status: str,
    report: dict[str, object],
    generated_code: str | None = None,
) -> None:
    """Update the history row when the current pipeline slice finishes."""
    # JSONB acomoda novos achados e metadados sem uma migração por campo novo.
    async with pool.connection() as connection:
        await connection.execute(
            """
            UPDATE modernization_history
               SET generated_code = %s, report = %s, status = %s
             WHERE id = %s
            """,
            (generated_code, Jsonb(report), status, run_id),
        )
        await connection.commit()


async def fetch_evaluation_runs(pool: AsyncConnectionPool) -> list[dict[str, object]]:
    """Read terminal reports for evaluation without returning source or code."""
    async with pool.connection() as connection, connection.cursor() as cursor:
        await cursor.execute(
            """
            SELECT id, status, report
              FROM modernization_history
             WHERE status IN ('success', 'failure', 'partial')
             ORDER BY id
            """
        )
        rows = await cursor.fetchall()
    return [{"id": int(row[0]), "status": row[1], "report": row[2]} for row in rows]


async def fetch_run_for_artifact(
    pool: AsyncConnectionPool, run_id: int
) -> dict[str, object] | None:
    """Read one completed run for explicit result export."""
    async with pool.connection() as connection, connection.cursor() as cursor:
        await cursor.execute(
            """
            SELECT id, source_code, generated_code, report, status, created_at
              FROM modernization_history
             WHERE id = %s
            """,
            (run_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return {
        "id": int(row[0]),
        "source_code": row[1],
        "generated_code": row[2],
        "report": row[3],
        "status": row[4],
        "created_at": row[5],
    }


@asynccontextmanager
async def lifespan_pool() -> AsyncIterator[AsyncConnectionPool]:
    pool = make_pool()
    await pool.open()
    try:
        await initialize_database(pool)
        yield pool
    finally:
        await pool.close()
