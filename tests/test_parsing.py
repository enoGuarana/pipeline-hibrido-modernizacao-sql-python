from pathlib import Path

import pytest

from pipeline.parsing import parse_routine

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize(
    ("fixture", "routine", "required"),
    [
        ("B.sql", "fn_saldo_cliente", {"select"}),
        ("C.sql", "sp_atualizar_status_contas_inativas", {"update", "jsonb"}),
        ("D.sql", "sp_transferir_entre_contas", {"select", "update", "locking", "exception"}),
        ("E.sql", "sp_processar_lote_taxas", {"cursor", "loop", "jsonb"}),
        ("F.sql", "sp_relatorio_mensal_cliente", {"cte_recursive", "raise", "function_call"}),
    ],
)
def test_fixture_extracts_wrapper_operations_and_tables(fixture, routine, required):
    parsed = parse_routine((FIXTURES / fixture).read_text(encoding="utf-8"))

    assert parsed is not None
    _, ir = parsed
    assert ir["routine_name"] == routine
    assert required.issubset(set(ir["operations"]))
    assert ir["tables"]
    assert ir["variables"] or fixture in {"C.sql", "F.sql"}
    assert ir["parameters"]
    assert ir["source_spans"] == []


def test_comments_and_strings_do_not_create_false_operations():
    source = """CREATE FUNCTION safe(p_id BIGINT) RETURNS INT LANGUAGE plpgsql AS $$
    BEGIN
        -- RAISE EXCEPTION; UPDATE fake_table; FOR UPDATE
        PERFORM 'SELECT * FROM fake_table';
        RETURN 1;
    END;
    $$;"""

    parsed = parse_routine(source)

    assert parsed is not None
    _, ir = parsed
    assert "exception" not in ir["operations"]
    assert "locking" not in ir["operations"]
    assert "fake_table" not in ir["tables"]
