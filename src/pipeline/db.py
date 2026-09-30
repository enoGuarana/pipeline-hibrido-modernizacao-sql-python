from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os

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


@asynccontextmanager
async def lifespan_pool() -> AsyncIterator[AsyncConnectionPool]:
    pool = make_pool()
    await pool.open()
    try:
        await initialize_database(pool)
        yield pool
    finally:
        await pool.close()

