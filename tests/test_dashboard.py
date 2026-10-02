from types import SimpleNamespace

import pytest
import requests

import dashboard


def _response(*, body, ok=True, status_code=200):
    return SimpleNamespace(
        json=lambda: body,
        ok=ok,
        status_code=status_code,
        text="",
    )


def test_api_request_falls_back_to_langgraph_port_on_connection_error(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if url.startswith("http://localhost:8000"):
            raise requests.ConnectionError("port 8000 unavailable")
        return _response(body={"status": "ok"})

    monkeypatch.setattr(
        dashboard,
        "API_URLS",
        ("http://localhost:8000", "http://localhost:8125"),
    )
    monkeypatch.setattr(dashboard.requests, "request", fake_request)

    result = dashboard.fetch_metrics()

    assert result == {"status": "ok"}
    assert [call[1] for call in calls] == [
        "http://localhost:8000/evaluation",
        "http://localhost:8125/evaluation",
    ]


def test_api_request_does_not_fallback_after_http_response(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return _response(body={"message": "degraded"}, ok=False, status_code=503)

    monkeypatch.setattr(
        dashboard,
        "API_URLS",
        ("http://localhost:8000", "http://localhost:8125"),
    )
    monkeypatch.setattr(dashboard.requests, "request", fake_request)

    with pytest.raises(requests.HTTPError, match="HTTP 503: degraded"):
        dashboard.fetch_metrics()

    assert len(calls) == 1
