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

PROMPT_VERSION = "modernize_v3"
PROMPT_PATH = Path(__file__).parent / "prompts" / "modernize_v3.txt"


class LLMError(RuntimeError):
    """Provider or contract error that should terminate the current run."""


@dataclass(frozen=True)
class LLMResult:
    code: str
    metadata: dict[str, Any]


def build_prompt(*, source_code: str, ir: dict[str, Any], analysis: dict[str, Any], schema: str | None) -> str:
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


async def generate(*, prompt: str) -> LLMResult:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not configured")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
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
            "provider": "gemini",
            "model": getattr(response, "model_version", None) or model,
            "prompt_version": PROMPT_VERSION,
            "response_id": getattr(response, "response_id", None),
            "usage": usage.model_dump(exclude_none=True) if hasattr(usage, "model_dump") else None,
        },
    )
