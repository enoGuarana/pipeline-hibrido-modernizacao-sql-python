import pytest

from pipeline.graph import build_graph

ANEXO_B = """CREATE OR REPLACE FUNCTION fn_saldo_cliente(p_cliente_id BIGINT)
RETURNS NUMERIC(18,2)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total NUMERIC(18,2);
BEGIN
    SELECT COALESCE(SUM(saldo), 0)
       INTO v_total
       FROM contas
      WHERE cliente_id = p_cliente_id
        AND status = 'ATIVA';
    RETURN v_total;
END;
$$;"""


@pytest.mark.anyio
async def test_anexo_b_completes_all_stages_with_simulated_generation():
    result = await build_graph().ainvoke(
        {"source_code": ANEXO_B, "status": "pending", "stage_reports": [], "errors": []}
    )

    assert result["status"] == "success"
    assert result["generation_attempts"] == 1
    assert result["validation"] == {
        "ast_parse": "passed",
        "lint": "passed",
        "equivalence": "not_tested",
    }
    assert [report["stage"] for report in result["stage_reports"]] == [
        "parsing",
        "semantic_analysis",
        "generation",
        "validation",
        "finalization",
    ]
    assert result["report"]["generation_mode"] == "simulated"


@pytest.mark.anyio
async def test_invalid_generated_output_is_reported_without_losing_prior_reports(monkeypatch):
    from pipeline import graph

    monkeypatch.setattr(
        graph,
        "generation_node",
        lambda state: {
            "generated_code": "def broken(:\n    pass\n",
            "generation_attempts": 1,
            "stage_reports": graph._with_stage(
                state, graph._stage("generation", "success", warnings=["test fixture"])
            ),
            "status": "pending",
        },
    )
    result = await graph.build_graph().ainvoke(
        {"source_code": ANEXO_B, "status": "pending", "stage_reports": [], "errors": []}
    )

    assert result["status"] == "failure"
    assert result["errors"][0]["code"] == "VALIDATION_SYNTAX"
    assert [report["stage"] for report in result["stage_reports"]] == [
        "parsing",
        "semantic_analysis",
        "generation",
        "validation",
        "finalization",
    ]


@pytest.mark.anyio
async def test_parse_failure_routes_to_finalization_before_generation():
    result = await build_graph().ainvoke(
        {"source_code": "SELECT 1;", "status": "pending", "stage_reports": [], "errors": []}
    )

    assert result["status"] == "failure"
    assert result["errors"][0]["code"] == "PARSE_UNSUPPORTED"
    assert result.get("generated_code") is None
    assert [report["stage"] for report in result["stage_reports"]] == [
        "parsing",
        "semantic_analysis",
        "generation",
        "validation",
        "finalization",
    ]


def test_validation_route_allows_only_one_repair(monkeypatch):
    from pipeline import graph

    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    failed = {"errors": [{"code": "VALIDATION_SYNTAX"}], "generation_attempts": 1}
    exhausted = {"errors": [{"code": "VALIDATION_SYNTAX"}], "generation_attempts": 2}

    assert graph._route_after_validation(failed) == "repair"
    assert graph._route_after_validation(exhausted) == "finalization"


@pytest.mark.anyio
async def test_repair_preserves_attempt_count_and_marks_metadata(monkeypatch):
    from pipeline import graph
    from pipeline.llm.client import LLMResult

    monkeypatch.setenv("GEMINI_API_KEY", "test-only")

    async def fake_generate(*, prompt="", **_kwargs):
        _ = prompt
        return LLMResult("def repaired():\n    return 1\n", {"provider": "gemini", "model": "test"})

    monkeypatch.setattr(graph, "generate", fake_generate)
    result = await graph.repair_node(
        {
            "source_code": ANEXO_B,
            "ir": {"routine_name": "fn_saldo_cliente"},
            "analysis": {},
            "generated_code": "def broken(:\n",
            "generation_attempts": 1,
            "errors": [{"code": "VALIDATION_SYNTAX", "stage": "validation"}],
            "stage_reports": [],
            "status": "failure",
        }
    )

    assert result["generation_attempts"] == 2
    assert result["generation_metadata"]["repaired"] is True
    assert result["errors"] == []
