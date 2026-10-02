"""Run isolated behavioral comparisons for the real B and C artifacts."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.behavioral_evaluation import (
    BehavioralObservation,
    compare_observations,
)

SCHEMA_SQL = """
CREATE TABLE contas (
    id BIGINT PRIMARY KEY,
    cliente_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    saldo NUMERIC(18, 2) NOT NULL
);
CREATE TABLE transacoes (
    id BIGINT PRIMARY KEY,
    conta_origem_id BIGINT,
    conta_destino_id BIGINT,
    data_transacao TIMESTAMPTZ NOT NULL
);
CREATE TABLE log_auditoria (
    id BIGSERIAL PRIMARY KEY,
    entidade TEXT NOT NULL,
    acao TEXT NOT NULL,
    detalhes JSONB NOT NULL
);
"""


def load_function(path: Path, name: str) -> Callable[..., Awaitable[Any]]:
    module_name = f"behavioral_{name}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name)


async def execute_sql(
    conn: psycopg.AsyncConnection[Any],
    sql: str,
    params: tuple[Any, ...] | None = None,
) -> None:
    async with conn.cursor() as cursor:
        if params is None:
            await cursor.execute(sql)
        else:
            await cursor.execute(sql, params)


async def snapshot(conn: psycopg.AsyncConnection[Any]) -> dict[str, Any]:
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT id, cliente_id, status, saldo FROM contas ORDER BY id")
        contas = [list(row) for row in await cursor.fetchall()]
        await cursor.execute(
            "SELECT entidade, acao, detalhes FROM log_auditoria ORDER BY id"
        )
        logs = [list(row) for row in await cursor.fetchall()]
    return {"contas": contas, "log_auditoria": logs}


async def prepare_schema(conn: psycopg.AsyncConnection[Any], schema: str) -> None:
    await execute_sql(conn, f'CREATE SCHEMA "{schema}"')
    await execute_sql(conn, f'SET search_path TO "{schema}"')
    await execute_sql(conn, SCHEMA_SQL)
    await execute_sql(conn, (ROOT / "fixtures/B.sql").read_text(encoding="utf-8"))
    await execute_sql(conn, (ROOT / "fixtures/C.sql").read_text(encoding="utf-8"))
    await conn.commit()


async def seed_b(conn: psycopg.AsyncConnection[Any]) -> None:
    await execute_sql(
        conn,
        """
        INSERT INTO contas (id, cliente_id, status, saldo) VALUES
            (1, 101, 'ATIVA', 10.20),
            (2, 101, 'ATIVA', 5.30),
            (3, 101, 'INATIVA', 100.00),
            (4, 202, 'ATIVA', 7.00)
        """,
    )
    await conn.commit()


async def seed_c(conn: psycopg.AsyncConnection[Any]) -> None:
    await execute_sql(
        conn,
        """
        INSERT INTO contas (id, cliente_id, status, saldo) VALUES
            (1, 101, 'ATIVA', 10.20),
            (2, 101, 'ATIVA', 5.30),
            (3, 202, 'ATIVA', 7.00),
            (4, 303, 'INATIVA', 9.00)
        """,
    )
    await execute_sql(
        conn,
        """
        INSERT INTO transacoes (id, conta_origem_id, conta_destino_id, data_transacao) VALUES
            (1, 1, NULL, NOW() - INTERVAL '10 days'),
            (2, 2, NULL, NOW() - INTERVAL '40 days')
        """,
    )
    await conn.commit()


async def clear_data(conn: psycopg.AsyncConnection[Any]) -> None:
    await execute_sql(conn, "TRUNCATE contas, transacoes, log_auditoria")
    await conn.commit()


async def observe_b(
    conninfo: str,
    schema: str,
    function: Callable[..., Awaitable[Any]],
    seed: Callable[[psycopg.AsyncConnection[Any]], Awaitable[None]],
    *,
    translated: bool,
) -> BehavioralObservation:
    async with await psycopg.AsyncConnection.connect(conninfo) as conn:
        await execute_sql(conn, f'SET search_path TO "{schema}"')
        await clear_data(conn)
        await seed(conn)
        try:
            if translated:
                value = await function(conn, 101)
            else:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT fn_saldo_cliente(%s)", (101,))
                    value = (await cursor.fetchone())[0]
            state = await snapshot(conn)
            await conn.commit()
            return BehavioralObservation(value, state)
        except (psycopg.Error, ValueError) as exc:
            await conn.rollback()
            return BehavioralObservation(None, await snapshot(conn), {"category": type(exc).__name__})


async def observe_c(
    conninfo: str,
    schema: str,
    procedure: Callable[..., Awaitable[Any]],
    seed: Callable[[psycopg.AsyncConnection[Any]], Awaitable[None]],
    *,
    translated: bool,
    days: int | None,
) -> BehavioralObservation:
    async with await psycopg.AsyncConnection.connect(conninfo) as conn:
        await execute_sql(conn, f'SET search_path TO "{schema}"')
        await clear_data(conn)
        await seed(conn)
        try:
            if translated:
                value = await procedure(conn, days)
            else:
                async with conn.cursor() as cursor:
                    await cursor.execute("CALL sp_atualizar_status_contas_inativas(%s, NULL)", (days,))
                    row = await cursor.fetchone()
                    value = row[0] if row else None
            state = await snapshot(conn)
            await conn.commit()
            return BehavioralObservation(value, state)
        except (psycopg.Error, ValueError) as exc:
            await conn.rollback()
            category = "invalid_parameter" if days is None or days <= 0 else type(exc).__name__
            return BehavioralObservation(None, await snapshot(conn), {"category": category})


async def run(conninfo: str) -> dict[str, Any]:
    schema = f"behavioral_eval_{uuid.uuid4().hex[:12]}"
    b_function = load_function(ROOT / "results/run-18/generated.py", "fn_saldo_cliente")
    c_procedure = load_function(
        ROOT / "results/run-23/generated.py", "sp_atualizar_status_contas_inativas"
    )
    try:
        async with await psycopg.AsyncConnection.connect(conninfo) as conn:
            await prepare_schema(conn, schema)
        cases: list[tuple[str, BehavioralObservation, BehavioralObservation]] = []
        cases.append(
            (
                "B saldo cliente 101",
                await observe_b(conninfo, schema, b_function, seed_b, translated=False),
                await observe_b(conninfo, schema, b_function, seed_b, translated=True),
            )
        )
        cases.append(
            (
                "C inativacao 30 dias",
                await observe_c(conninfo, schema, c_procedure, seed_c, translated=False, days=30),
                await observe_c(conninfo, schema, c_procedure, seed_c, translated=True, days=30),
            )
        )
        cases.append(
            (
                "C parametro invalido",
                await observe_c(conninfo, schema, c_procedure, seed_c, translated=False, days=0),
                await observe_c(conninfo, schema, c_procedure, seed_c, translated=True, days=0),
            )
        )
        output_cases = []
        for name, legacy, translated in cases:
            comparison = compare_observations(legacy, translated)
            output_cases.append(
                {
                    "name": name,
                    "equivalent": comparison.equivalent,
                    "differences": comparison.differences,
                    "normalized_paths": comparison.normalized_paths,
                    "legacy": {"return": legacy.return_value, "state": legacy.table_state, "error": legacy.error},
                    "translated": {
                        "return": translated.return_value,
                        "state": translated.table_state,
                        "error": translated.error,
                    },
                }
            )
        return {
            "database_isolation": "temporary_schema",
            "schema": schema,
            "artifacts": ["results/run-18", "results/run-23"],
            "cases": output_cases,
            "summary": {
                "total": len(output_cases),
                "equivalent": sum(case["equivalent"] for case in output_cases),
            },
            "limitations": [
                "Only the declared B and C scenarios were executed.",
                "Generated code was executed only inside the isolated evaluation schema.",
                "The invalid-parameter case compares the declared semantic category, not database exception class identity.",
            ],
        }
    finally:
        async with await psycopg.AsyncConnection.connect(conninfo) as conn:
            await conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            await conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:55432/modernization"),
    )
    parser.add_argument("--output", type=Path, default=ROOT / "results/behavioral-bc.json")
    args = parser.parse_args()
    result = asyncio.run(
        run(args.database_url),
        loop_factory=asyncio.SelectorEventLoop,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
