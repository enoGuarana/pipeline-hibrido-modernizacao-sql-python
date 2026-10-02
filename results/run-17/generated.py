import psycopg
from decimal import Decimal


async def fn_saldo_cliente(conn: psycopg.AsyncConnection, p_cliente_id: int) -> Decimal | None:
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
        if row is not None:
            return row[0]
        return None