from decimal import Decimal
import json

import psycopg


async def sp_transferir_entre_contas(
    conn: psycopg.AsyncConnection,
    p_conta_origem: int,
    p_conta_destino: int,
    p_valor: Decimal,
) -> None:
    if p_valor is None or p_valor <= 0:
        raise ValueError(f"Valor invalido para transferencia: {p_valor}")
    if p_conta_origem == p_conta_destino:
        raise ValueError("Conta de origem e destino nao podem ser iguais")

    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT saldo, status FROM contas WHERE id = %s FOR UPDATE",
                (p_conta_origem,),
            )
            row_origem = await cur.fetchone()

            await cur.execute(
                "SELECT status FROM contas WHERE id = %s FOR UPDATE",
                (p_conta_destino,),
            )
            row_destino = await cur.fetchone()

            if row_origem is None:
                raise ValueError(f"Conta de origem {p_conta_origem} nao encontrada")

            if row_destino is None:
                raise ValueError(f"Conta de destino {p_conta_destino} nao encontrada")

            v_saldo_origem, v_status_origem = row_origem
            v_status_destino = row_destino[0]

            if v_status_origem != "ATIVA" or v_status_destino != "ATIVA":
                raise ValueError("Ambas as contas precisam estar ATIVAS")

            if v_saldo_origem < p_valor:
                raise ValueError(f"Saldo insuficiente: saldo={v_saldo_origem} valor={p_valor}")

            await cur.execute(
                "UPDATE contas SET saldo = saldo - %s WHERE id = %s",
                (p_valor, p_conta_origem),
            )
            await cur.execute(
                "UPDATE contas SET saldo = saldo + %s WHERE id = %s",
                (p_valor, p_conta_destino),
            )
            await cur.execute(
                """
                INSERT INTO transacoes (conta_origem_id, conta_destino_id, tipo, valor)
                VALUES (%s, %s, 'TRANSFERENCIA', %s)
                """,
                (p_conta_origem, p_conta_destino, p_valor),
            )
            await cur.execute(
                """
                INSERT INTO log_auditoria (entidade, entidade_id, acao, detalhes)
                VALUES ('transacoes', NULL, 'TRANSFERENCIA_OK', %s)
                """,
                (
                    json.dumps(
                        {
                            "origem": p_conta_origem,
                            "destino": p_conta_destino,
                            "valor": str(p_valor),
                        }
                    ),
                ),
            )
    except Exception as e:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO log_auditoria (entidade, acao, detalhes)
                VALUES ('transacoes', 'TRANSFERENCIA_ERRO', %s)
                """,
                (
                    json.dumps(
                        {
                            "origem": p_conta_origem,
                            "destino": p_conta_destino,
                            "valor": str(p_valor),
                            "erro": str(e),
                        }
                    ),
                ),
            )
        raise