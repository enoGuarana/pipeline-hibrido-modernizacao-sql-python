from contextlib import nullcontext

import httpx
import pytest

from pipeline import api


async def _request(method: str, path: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


class _HealthyConnection:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement):
        assert statement == "SELECT 1"


class _HealthyPool:
    def connection(self):
        return _HealthyConnection()


@pytest.mark.anyio
async def test_health_checks_the_configured_database_pool(monkeypatch):
    monkeypatch.setattr(api.app.state, "db_pool", _HealthyPool(), raising=False)

    response = await _request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_modernize_persists_success_without_exposing_api_key(monkeypatch):
    calls = {}
    pool = object()

    async def fake_create_pending_run(received_pool, *, source_code, report):
        calls["pending"] = {
            "pool": received_pool,
            "source_code": source_code,
            "report": report,
        }
        return 42

    async def fake_finalize_run(received_pool, **kwargs):
        calls["final"] = {"pool": received_pool, **kwargs}

    class FakeGraph:
        async def ainvoke(self, state):
            calls["state"] = state
            return {
                "status": "success",
                "generated_code": "def generated():\n    return 1\n",
                "report": {"stages": [], "errors": []},
            }

    monkeypatch.setattr(api.app.state, "db_pool", pool, raising=False)
    monkeypatch.setattr(api.app.state, "graph", FakeGraph(), raising=False)
    monkeypatch.setattr(api, "create_pending_run", fake_create_pending_run)
    monkeypatch.setattr(api, "finalize_run", fake_finalize_run)
    monkeypatch.setattr(api, "observation", lambda *args, **kwargs: nullcontext(None))

    response = await _request(
        "POST",
        "/modernize",
        json={
            "source_code": "CREATE FUNCTION example() RETURNS INT AS $$ BEGIN RETURN 1; END; $$;",
            "provider": "openrouter",
            "api_key": "request-secret",
            "model_name": "example/model",
        },
    )

    assert response.status_code == 200
    assert response.json()["run_id"] == 42
    assert response.json()["status"] == "success"
    assert "request-secret" not in response.text
    assert calls["pending"]["pool"] is pool
    assert calls["pending"]["report"]["provider"] == "openrouter"
    assert "api_key" not in calls["pending"]["report"]
    assert calls["state"]["api_key"] == "request-secret"
    assert calls["final"]["status"] == "success"
    assert calls["final"]["generated_code"].startswith("def generated")


@pytest.mark.anyio
async def test_modernize_finalizes_unexpected_graph_failure(monkeypatch):
    finalized = {}

    async def fake_create_pending_run(pool, *, source_code, report):
        return 43

    async def fake_finalize_run(pool, **kwargs):
        finalized.update(kwargs)

    class FailingGraph:
        async def ainvoke(self, state):
            raise RuntimeError("unexpected graph failure")

    monkeypatch.setattr(api.app.state, "db_pool", object(), raising=False)
    monkeypatch.setattr(api.app.state, "graph", FailingGraph(), raising=False)
    monkeypatch.setattr(api, "create_pending_run", fake_create_pending_run)
    monkeypatch.setattr(api, "finalize_run", fake_finalize_run)
    monkeypatch.setattr(api, "observation", lambda *args, **kwargs: nullcontext(None))

    response = await _request(
        "POST",
        "/modernize",
        json={"source_code": "CREATE FUNCTION example() RETURNS INT AS $$ BEGIN RETURN 1; END; $$;"},
    )

    assert response.status_code == 500
    assert response.json()["run_id"] == 43
    assert finalized["status"] == "failure"
    assert finalized["report"]["errors"][0]["code"] == "PIPELINE_EXCEPTION"


@pytest.mark.anyio
async def test_evaluation_keeps_terminal_failures_in_denominator(monkeypatch):
    async def fake_fetch_evaluation_runs(pool):
        return [
            {
                "id": 7,
                "status": "failure",
                "report": {
                    "errors": [{"stage": "validation"}],
                    "traceability": {"generation_attempts": 1},
                },
            }
        ]

    monkeypatch.setattr(api.app.state, "db_pool", object(), raising=False)
    monkeypatch.setattr(api, "fetch_evaluation_runs", fake_fetch_evaluation_runs)

    response = await _request("GET", "/evaluation")

    assert response.status_code == 200
    assert response.json()["metrics"]["total_runs"] == 1
    assert response.json()["metrics"]["failures_by_stage"] == {"validation": 1}
    assert response.json()["evaluated_run_ids"] == [7]
