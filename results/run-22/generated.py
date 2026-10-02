import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


async def fn_saldo_cliente(conn, p_cliente_id: int) -> Decimal | None:
    row = await conn.fetchrow("SELECT fn_saldo_cliente($1) AS saldo", p_cliente_id)
    if row and row["saldo"] is not None:
        return Decimal(str(row["saldo"]))
    return None


async def sp_relatorio_mensal_cliente(
    conn,
    p_cliente_id: int,
    p_data_inicio: datetime.date,
    p_data_fim: datetime.date,
) -> list[tuple[datetime.date, Decimal, Decimal, Decimal, int]]:
    if p_data_inicio > p_data_fim:
        raise ValueError(f"Periodo invalido: inicio {p_data_inicio} > fim {p_data_fim}")

    v_saldo_atual: Decimal | None = None
    try:
        v_saldo_atual = await fn_saldo_cliente(conn, p_cliente_id)
        logger.info("Saldo atual do cliente %s: %s", p_cliente_id, v_saldo_atual)

        query = """
        WITH RECURSIVE meses AS (
            SELECT DATE_TRUNC('month', $2::date)::DATE AS mes
            UNION ALL
            SELECT (mes + INTERVAL '1 month')::DATE FROM meses
             WHERE mes < DATE_TRUNC('month', $3::date)
        ), movimento AS (
            SELECT DATE_TRUNC('month', t.data_transacao)::DATE AS mes,
                   SUM(CASE WHEN t.conta_destino_id IN (SELECT id FROM contas WHERE cliente_id = $1) THEN t.valor ELSE 0 END) AS creditos,
                   SUM(CASE WHEN t.conta_origem_id IN (SELECT id FROM contas WHERE cliente_id = $1) THEN t.valor ELSE 0 END) AS debitos,
                   COUNT(*) AS qtd
              FROM transacoes t
             WHERE t.status = 'EFETIVADA' AND t.data_transacao >= $2::date
               AND t.data_transacao < $3::date + INTERVAL '1 day'
             GROUP BY 1
        )
        SELECT m.mes, COALESCE(mv.creditos, 0), COALESCE(mv.debitos, 0),
               COALESCE($4, 0) + COALESCE(mv.creditos, 0) - COALESCE(mv.debitos, 0),
               COALESCE(mv.qtd, 0)::INT
          FROM meses m LEFT JOIN movimento mv ON mv.mes = m.mes ORDER BY m.mes;
        """

        saldo_val = v_saldo_atual if v_saldo_atual is not None else Decimal("0.00")
        rows = await conn.fetch(query, p_cliente_id, p_data_inicio, p_data_fim, saldo_val)

        result = []
        for row in rows:
            result.append((
                row[0],
                Decimal(str(row[1])),
                Decimal(str(row[2])),
                Decimal(str(row[3])),
                int(row[4])
            ))
        return result

    except Exception as e:
        logger.warning("Falha ao gerar relatorio: %s. Retornando linha de fallback.", e)
        fallback_mes = datetime.datetime.combine(p_data_inicio, datetime.time.min).replace(day=1).date()
        fallback_saldo = v_saldo_atual if v_saldo_atual is not None else Decimal("0.00")
        return [(
            fallback_mes,
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal(str(fallback_saldo)),
            0
        )]