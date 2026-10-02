from datetime import date, datetime
from decimal import Decimal
import sys

import psycopg
from psycopg import OperationalError, ProgrammingError


def _quantize_18_2(val: Decimal | None) -> Decimal | None:
    if val is None:
        return None
    return val.quantize(Decimal("0.01"))


async def _fn_saldo_cliente(conn: psycopg.AsyncConnection, cliente_id: int) -> Decimal | None:
    async with conn.cursor() as cur:
        await cur.execute("SELECT fn_saldo_cliente(%s)", (cliente_id,))
        row = await cur.fetchone()
        if row is not None:
            return _quantize_18_2(row[0])
        return None


async def sp_relatorio_mensal_cliente(
    conn: psycopg.AsyncConnection,
    p_cliente_id: int,
    p_data_inicio: date,
    p_data_fim: date,
) -> list[tuple[date, Decimal, Decimal, Decimal, int]]:
    v_saldo_atual: Decimal | None = None
    try:
        if p_data_inicio > p_data_fim:
            raise ValueError(f"Periodo invalido: inicio {p_data_inicio} > fim {p_data_fim}")

        v_saldo_atual = await _fn_saldo_cliente(conn, p_cliente_id)
        if v_saldo_atual is not None:
            v_saldo_atual = _quantize_18_2(v_saldo_atual)

        print(f"NOTICE: Saldo atual do cliente {p_cliente_id}: {v_saldo_atual}", file=sys.stderr)

        query = """
            WITH RECURSIVE meses AS (
                SELECT DATE_TRUNC('month', %s::date)::date AS mes
                UNION ALL
                SELECT (mes + INTERVAL '1 month')::date FROM meses
                 WHERE mes < DATE_TRUNC('month', %s::date)
            ), movimento AS (
                SELECT DATE_TRUNC('month', t.data_transacao)::date AS mes,
                       SUM(CASE WHEN t.conta_destino_id IN (SELECT id FROM contas WHERE cliente_id = %s) THEN t.valor ELSE 0 END) AS creditos,
                       SUM(CASE WHEN t.conta_origem_id IN (SELECT id FROM contas WHERE cliente_id = %s) THEN t.valor ELSE 0 END) AS debitos,
                       COUNT(*) AS qtd
                  FROM transacoes t
                 WHERE t.status = 'EFETIVADA' AND t.data_transacao >= %s::date
                   AND t.data_transacao < %s::date + INTERVAL '1 day'
                 GROUP BY 1
            )
            SELECT m.mes, COALESCE(mv.creditos, 0), COALESCE(mv.debitos, 0),
                   %s::numeric + COALESCE(mv.creditos, 0) - COALESCE(mv.debitos, 0),
                   COALESCE(mv.qtd, 0)::int
              FROM meses m LEFT JOIN movimento mv ON mv.mes = m.mes ORDER BY m.mes
        """

        async with conn.cursor() as cur:
            await cur.execute(
                query,
                (
                    p_data_inicio,
                    p_data_fim,
                    p_cliente_id,
                    p_cliente_id,
                    p_data_inicio,
                    p_data_fim,
                    v_saldo_atual if v_saldo_atual is not None else Decimal("0.00"),
                ),
            )
            rows = await cur.fetchall()
            result = []
            for row in rows:
                mes_ref = row[0]
                if isinstance(mes_ref, datetime):
                    mes_ref = mes_ref.date()
                cred = _quantize_18_2(row[1]) or Decimal("0.00")
                deb = _quantize_18_2(row[2]) or Decimal("0.00")
                saldo_cons = _quantize_18_2(row[3]) or Decimal("0.00")
                qtd = int(row[4])
                result.append((mes_ref, cred, deb, saldo_cons, qtd))
            return result

    except (ValueError, OperationalError, ProgrammingError, psycopg.Error) as e:
        sql_err_m = str(e)
        print(f"WARNING: Falha ao gerar relatorio: {sql_err_m}. Retornando linha de fallback.", file=sys.stderr)
        fallback_mes = datetime.combine(p_data_inicio, datetime.min.time()).replace(day=1).date()
        fallback_saldo = _quantize_18_2(v_saldo_atual) if v_saldo_atual is not None else Decimal("0.00")
        return [(fallback_mes, _quantize_18_2(Decimal("0.00")) or Decimal("0.00"), _quantize_18_2(Decimal("0.00")) or Decimal("0.00"), fallback_saldo, 0)]