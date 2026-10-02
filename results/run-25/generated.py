from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import psycopg
from psycopg.types.json import Jsonb


def _quantize_18_2(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _quantize_7_4(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        return Decimal("0.0000")
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


async def sp_processar_lote_taxas(conn: psycopg.AsyncConnection, p_data_referencia: date) -> None:
    v_total_taxas = _quantize_18_2(0)
    v_count = 0

    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT id, conta_origem_id, tipo, valor FROM transacoes
             WHERE DATE(data_transacao) = %s
               AND status = 'EFETIVADA' AND tipo <> 'TARIFA'
            """,
            (p_data_referencia,),
        )
        rows = await cur.fetchall()

    for row in rows:
        v_id, v_origem, v_tipo, v_valor_raw = row
        v_valor = _quantize_18_2(v_valor_raw)

        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT percentual, valor_minimo FROM taxas
                 WHERE tipo_operacao = %s AND vigente_de <= %s
                   AND (vigente_ate IS NULL OR vigente_ate >= %s)
                 ORDER BY vigente_de DESC LIMIT 1
                """,
                (v_tipo, p_data_referencia, p_data_referencia),
            )
            taxas_row = await cur.fetchone()

        if not taxas_row:
            continue

        v_percentual_raw, v_minimo_raw = taxas_row
        v_percentual = _quantize_7_4(v_percentual_raw)
        v_minimo = _quantize_18_2(v_minimo_raw)

        if v_percentual is None:
            continue

        calc_taxa = v_valor * v_percentual / Decimal("100.0")
        v_taxa = _quantize_18_2(max(calc_taxa, v_minimo))

        if v_tipo == "TRANSFERENCIA":
            v_taxa = _quantize_18_2(v_taxa)
        elif v_tipo == "SAQUE":
            v_taxa = _quantize_18_2(v_taxa * Decimal("1.10"))
        else:
            v_taxa = _quantize_18_2(v_taxa * Decimal("0.90"))

        if v_origem is not None:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE contas SET saldo = saldo - %s WHERE id = %s",
                    (v_taxa, v_origem),
                )
                await cur.execute(
                    """
                    INSERT INTO transacoes (conta_origem_id, tipo, valor, status)
                    VALUES (%s, 'TARIFA', %s, 'EFETIVADA')
                    """,
                    (v_origem, v_taxa),
                )
                detalhes_dict = {
                    "transacao_origem": v_id,
                    "tipo_origem": v_tipo,
                    "valor_origem": v_valor,
                    "percentual": v_percentual,
                    "taxa_aplicada": v_taxa,
                }
                await cur.execute(
                    """
                    INSERT INTO log_auditoria (entidade, entidade_id, acao, detalhes)
                    VALUES ('transacoes', %s, 'TARIFA_APLICADA', %s)
                    """,
                    (v_id, Jsonb(detalhes_dict)),
                )
            v_total_taxas = _quantize_18_2(v_total_taxas + v_taxa)
            v_count += 1

    async with conn.cursor() as cur:
        detalhes_lote = {
            "data_referencia": p_data_referencia.isoformat(),
            "transacoes": v_count,
            "total_taxas": v_total_taxas,
        }
        await cur.execute(
            """
            INSERT INTO log_auditoria (entidade, acao, detalhes)
            VALUES ('lote_taxas', 'LOTE_PROCESSADO', %s)
            """,
            (Jsonb(detalhes_lote),),
        )