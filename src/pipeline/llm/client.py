"""Small, configurable Gemini API boundary."""

from __future__ import annotations

import asyncio
import os
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import truststore
from google import genai
from google.genai import types
from openai import AsyncOpenAI

PROMPT_VERSION = "modernize_v4"
PROMPT_PATH = Path(__file__).parent / "prompts" / "modernize_v4.txt"


class LLMError(RuntimeError):
    """Provider or contract error that should terminate the current run."""


@dataclass(frozen=True)
class LLMResult:
    code: str
    metadata: dict[str, Any]


def resolve_provider_config(
    provider: str,
    api_key: str | None = None,
    model_name: str | None = None,
) -> tuple[str | None, str]:
    """Resolve request overrides first, then the provider-specific environment."""

    if provider == "gemini":
        return api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), model_name or os.getenv(
            "GEMINI_MODEL", "gemini-3.5-flash-lite"
        )
    if provider == "openrouter":
        return api_key or os.getenv("OPENROUTER_API_KEY"), model_name or os.getenv(
            "OPENROUTER_MODEL", "openai/gpt-4o-mini"
        )
    if provider == "openai":
        return api_key or os.getenv("OPENAI_API_KEY"), model_name or os.getenv(
            "OPENAI_MODEL", "gpt-4o-mini"
        )
    raise LLMError(f"Unsupported LLM provider: {provider}")


def provider_has_credentials(provider: str, api_key: str | None = None) -> bool:
    """Check whether the selected provider can make a real request."""

    key, _ = resolve_provider_config(provider, api_key)
    return bool(key)


def build_prompt(*, source_code: str, ir: dict[str, Any], analysis: dict[str, Any], schema: str | None) -> str:
    # A LLM recebe origem, IR e análise para não depender apenas do SQL bruto
    # nem perder riscos identificados antes da geração.
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        source_code=source_code,
        intermediate_representation=ir,
        analysis=analysis,
        schema=schema or "not provided",
        contract="async function accepting a PostgreSQL connection and typed routine parameters",
        transaction_policy="the caller owns the connection and transaction; use parameterized SQL",
    )


def _without_markdown_fences(value: str) -> str:
    text = value.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        return "\n".join(lines[1:-1]).strip()
    return text


async def generate(
    *,
    prompt: str,
    provider: str = "gemini",
    api_key: str | None = None,
    model_name: str | None = None,
) -> LLMResult:
    # A chave explícita tem prioridade sobre o ambiente, mas nunca entra no
    # prompt, relatório ou metadados persistidos.
    resolved_key, model = resolve_provider_config(provider, api_key, model_name)
    if not resolved_key:
        env_name = {
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
        }[provider]
        raise LLMError(f"{env_name} is not configured")

    if provider in {"openai", "openrouter"}:
        return await _generate_openai_compatible(
            prompt=prompt,
            provider=provider,
            api_key=resolved_key,
            model=model,
        )

    timeout_ms = int(float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60")) * 1000)
    http_client: httpx.Client | None = None
    client: genai.Client | None = None
    try:
        tls_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        http_client = httpx.Client(verify=tls_context)
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=timeout_ms,
                httpx_client=http_client,
            ),
        )
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                response_mime_type="text/plain",
            ),
        )
    except Exception as exc:
        raise LLMError(f"Gemini request failed: {exc}") from exc
    finally:
        if client is not None:
            client.close()
        elif http_client is not None:
            http_client.close()
    code = _without_markdown_fences(getattr(response, "text", "") or "")
    if not code:
        raise LLMError("Gemini returned an empty response")
    usage = getattr(response, "usage_metadata", None)
    return LLMResult(
        code=code,
        metadata={
            "provider": provider,
            "model": getattr(response, "model_version", None) or model,
            "prompt_version": PROMPT_VERSION,
            "response_id": getattr(response, "response_id", None),
            "usage": usage.model_dump(exclude_none=True) if hasattr(usage, "model_dump") else None,
        },
    )


async def _generate_openai_compatible(
    *, prompt: str, provider: str, api_key: str, model: str
) -> LLMResult:
    """Call OpenAI or an OpenAI-compatible endpoint with one normalized output."""

    base_url = "https://openrouter.ai/api/v1" if provider == "openrouter" else None
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
    except Exception as exc:
        raise LLMError(f"{provider} request failed: {exc}") from exc
    finally:
        await client.close()

    message = response.choices[0].message.content if response.choices else None
    code = _without_markdown_fences(message or "")
    if not code:
        raise LLMError(f"{provider} returned an empty response")
    usage = getattr(response, "usage", None)
    return LLMResult(
        code=code,
        metadata={
            "provider": provider,
            "model": getattr(response, "model", None) or model,
            "prompt_version": PROMPT_VERSION,
            "response_id": getattr(response, "id", None),
            "usage": usage.model_dump(exclude_none=True) if hasattr(usage, "model_dump") else None,
        },
    )
