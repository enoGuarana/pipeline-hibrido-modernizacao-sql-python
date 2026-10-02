import json

from psycopg import AsyncConnection


async def sp_atualizar_status_contas_inativas(
    conn: AsyncConnection,
    p_dias: int | None,
) -> int:
    if p_dias is None or p_dias <= 0:
        raise ValueError(f"Parametro p_dias deve ser positivo, recebido: {p_dias}")

    async with conn.cursor() as cur:
        await cur.execute(
            """
            UPDATE contas c
               SET status = 'INATIVA'
             WHERE c.status = 'ATIVA'
               AND NOT EXISTS (
                    SELECT 1 FROM transacoes t
                     WHERE (t.conta_origem_id = c.id OR t.conta_destino_id = c.id)
                       AND t.data_transacao >= NOW() - (%s || ' days')::INTERVAL
               )
            """,
            (p_dias,),
        )
        p_afetadas = cur.rowcount

        detalhes = json.dumps({"dias": p_dias, "afetadas": p_afetadas})
        await cur.execute(
            """
            INSERT INTO log_auditoria (entidade, acao, detalhes)
            VALUES ('contas', 'INATIVACAO_LOTE', %s::jsonb)
            """,
            (detalhes,),
        )

    return p_afetadas