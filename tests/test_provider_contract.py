from pipeline.api import ModernizeRequest


def test_request_defaults_to_gemini_without_exposing_a_key():
    request = ModernizeRequest(source_code="SELECT 1")

    assert request.provider == "gemini"
    assert request.api_key is None
    assert request.model_name is None


def test_request_accepts_provider_key_and_model_override():
    request = ModernizeRequest(
        source_code="SELECT 1",
        provider="openrouter",
        api_key="request-only",
        model_name="meta-llama/llama-test",
    )

    assert request.provider == "openrouter"
    assert request.api_key == "request-only"
    assert request.model_name == "meta-llama/llama-test"
