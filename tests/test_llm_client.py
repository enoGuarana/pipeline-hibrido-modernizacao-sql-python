from types import SimpleNamespace

import pytest

from pipeline.llm import client


@pytest.mark.anyio
async def test_generate_uses_gemini_and_records_available_metadata(monkeypatch):
    class FakeUsage:
        def model_dump(self, *, exclude_none):
            assert exclude_none is True
            return {"prompt_token_count": 10, "candidates_token_count": 5}

    response = SimpleNamespace(
        text="```python\ndef generated():\n    return 1\n```",
        model_version="gemini-test",
        response_id="response-1",
        usage_metadata=FakeUsage(),
    )
    calls = {}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls.update(model=model, contents=contents, config=config)
            return response

    class FakeGeminiClient:
        def __init__(self, **kwargs):
            calls["client_kwargs"] = kwargs
            self.http_client = kwargs["http_options"].httpx_client
            self.models = FakeModels()

        def close(self):
            self.http_client.close()
            calls["closed"] = True

    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setattr(client.genai, "Client", FakeGeminiClient)

    result = await client.generate(prompt="structured context")

    assert result.code == "def generated():\n    return 1"
    assert result.metadata == {
        "provider": "gemini",
        "model": "gemini-test",
        "prompt_version": "modernize_v3",
        "response_id": "response-1",
        "usage": {"prompt_token_count": 10, "candidates_token_count": 5},
    }
    assert calls["model"] == "gemini-test"
    assert calls["contents"] == "structured context"
    assert calls["config"].automatic_function_calling.disable is True
    assert calls["config"].response_mime_type == "text/plain"
    assert calls["closed"] is True


@pytest.mark.anyio
async def test_generate_requires_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(client.LLMError, match="GEMINI_API_KEY is not configured"):
        await client.generate(prompt="context")
