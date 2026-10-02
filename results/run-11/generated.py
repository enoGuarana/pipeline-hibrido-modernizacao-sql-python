from decimal import Decimal
from typing import Any, Optional


async def fn_saldo_cliente(conn: Any, p_cliente_id: Optional[int]) -> Decimal:
    if hasattr(conn, "fetchval"):
        query = """
            SELECT CAST(COALESCE(SUM(saldo), 0) AS NUMERIC(18, 2))
              FROM contas
             WHERE cliente_id = $1
               AND status = 'ATIVA';
        """
        result = await conn.fetchval(query, p_cliente_id)
    else:
        query = """
            SELECT CAST(COALESCE(SUM(saldo), 0) AS NUMERIC(18, 2))
              FROM contas
             WHERE cliente_id = %s
               AND status = 'ATIVA';
        """
        async with conn.cursor() as cursor:
            await cursor.execute(query, (p_cliente_id,))
            row = await cursor.fetchone()
            result = row[0] if row is not None else None

    if result is None:
        return Decimal("0.00")

    if not isinstance(result, Decimal):
        result = Decimal(str(result))

    return result