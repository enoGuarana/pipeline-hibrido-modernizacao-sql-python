import json
from datetime import date
from decimal import Decimal

import psycopg


async def sp_processar_lote_taxas(conn: psycopg.AsyncConnection, p_data_referencia: date) -> None:
    v_total_taxas = Decimal("0.00")
    v_count = 0

    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT id, conta_origem_id, tipo, valor
              FROM transacoes
             WHERE DATE(data_transacao) = %s
               AND status = 'EFETIVADA'
               AND tipo <> 'TARIFA'
            """,
            (p_data_referencia,),
        )
        transacoes = await cur.fetchall()

    for v_id, v_origem, v_tipo, v_valor in transacoes:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT percentual, valor_minimo
                  FROM taxas
                 WHERE tipo_operacao = %s
                   AND vigente_de <= %s
                   AND (vigente_ate IS NULL OR vigente_ate >= %s)
                 ORDER BY vigente_de DESC
                 LIMIT 1
                """,
                (v_tipo, p_data_referencia, p_data_referencia),
            )
            taxa_row = await cur.fetchone()

        if taxa_row is None:
            continue

        v_percentual, v_minimo = taxa_row
        if v_percentual is None:
            continue

        v_taxa = max(v_valor * v_percentual / Decimal("100.0"), v_minimo)

        if v_tipo == "SAQUE":
            v_taxa = v_taxa * Decimal("1.10")
        elif v_tipo != "TRANSFERENCIA":
            v_taxa = v_taxa * Decimal("0.90")

        if v_origem is not None:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE contas
                       SET saldo = saldo - %s
                     WHERE id = %s
                    """,
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
                    "valor_origem": str(v_valor),
                    "percentual": str(v_percentual),
                    "taxa_aplicada": str(v_taxa),
                }
                await cur.execute(
                    """
                    INSERT INTO log_auditoria (entidade, entidade_id, acao, detalhes)
                    VALUES ('transacoes', %s, 'TARIFA_APLICADA', %s)
                    """,
                    (v_id, json.dumps(detalhes_dict)),
                )

            v_total_taxas += v_taxa
            v_count += 1

    async with conn.cursor() as cur:
        detalhes_lote = {
            "data_referencia": p_data_referencia.isoformat(),
            "transacoes": v_count,
            "total_taxas": str(v_total_taxas),
        }
        await cur.execute(
            """
            INSERT INTO log_auditoria (entidade, acao, detalhes)
            VALUES ('lote_taxas', 'LOTE_PROCESSADO', %s)
            """,
            (json.dumps(detalhes_lote),),
        )