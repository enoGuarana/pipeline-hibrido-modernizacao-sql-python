from decimal import ROUND_DOWN, Decimal

from psycopg import AsyncConnection, Error as PsycopgError
from psycopg.types.json import Jsonb


def _quantize_numeric(value: Decimal | float | str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


async def sp_transferir_entre_contas(
    conn: AsyncConnection,
    p_conta_origem: int,
    p_conta_destino: int,
    p_valor: Decimal | float | str,
) -> None:
    p_valor_q = _quantize_numeric(p_valor)

    if p_valor_q is None or p_valor_q <= Decimal("0.00"):
        raise ValueError(f"Valor invalido para transferencia: {p_valor}")

    if p_conta_origem == p_conta_destino:
        raise ValueError("Conta de origem e destino nao podem ser iguais")

    v_saldo_origem: Decimal | None = None
    v_status_origem: str | None = None
    v_status_destino: str | None = None

    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT saldo, status FROM contas WHERE id = %s FOR UPDATE",
                (p_conta_origem,),
            )
            row_origem = await cur.fetchone()
            if row_origem:
                v_saldo_origem = _quantize_numeric(row_origem[0])
                v_status_origem = row_origem[1]

            await cur.execute(
                "SELECT status FROM contas WHERE id = %s FOR UPDATE",
                (p_conta_destino,),
            )
            row_destino = await cur.fetchone()
            if row_destino:
                v_status_destino = row_destino[0]

        if v_saldo_origem is None:
            raise ValueError(f"Conta de origem {p_conta_origem} nao encontrada")

        if v_status_origem != "ATIVA" or v_status_destino != "ATIVA":
            raise ValueError("Ambas as contas precisam estar ATIVAS")

        if v_saldo_origem < p_valor_q:
            raise ValueError(
                f"Saldo insuficiente: saldo={v_saldo_origem} valor={p_valor_q}"
            )

        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE contas SET saldo = saldo - %s WHERE id = %s",
                (p_valor_q, p_conta_origem),
            )
            await cur.execute(
                "UPDATE contas SET saldo = saldo + %s WHERE id = %s",
                (p_valor_q, p_conta_destino),
            )
            await cur.execute(
                """
                INSERT INTO transacoes (conta_origem_id, conta_destino_id, tipo, valor)
                VALUES (%s, %s, 'TRANSFERENCIA', %s)
                """,
                (p_conta_origem, p_conta_destino, p_valor_q),
            )
            await cur.execute(
                """
                INSERT INTO log_auditoria (entidade, entidade_id, acao, detalhes)
                VALUES ('transacoes', NULL, 'TRANSFERENCIA_OK', %s)
                """,
                (
                    Jsonb(
                        {
                            "origem": p_conta_origem,
                            "destino": p_conta_destino,
                            "valor": str(p_valor_q),
                        }
                    ),
                ),
            )
    except (ValueError, PsycopgError) as err:
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO log_auditoria (entidade, acao, detalhes)
                    VALUES ('transacoes', 'TRANSFERENCIA_ERRO', %s)
                    """,
                    (
                        Jsonb(
                            {
                                "origem": p_conta_origem,
                                "destino": p_conta_destino,
                                "valor": str(p_valor_q),
                                "erro": str(err),
                            }
                        ),
                    ),
                )
        except PsycopgError:
            pass
        raise