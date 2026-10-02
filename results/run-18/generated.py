from decimal import Decimal

import psycopg


async def fn_saldo_cliente(conn: psycopg.AsyncConnection, p_cliente_id: int) -> Decimal:
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT COALESCE(SUM(saldo), 0)
              FROM contas
             WHERE cliente_id = %s
               AND status = 'ATIVA'
            """,
            (p_cliente_id,),
        )
        row = await cur.fetchone()
        if row is None or row[0] is None:
            return Decimal("0.00")
        return Decimal(str(row[0]))