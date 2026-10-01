"""Small, configurable OpenAI Responses API boundary."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROMPT_VERSION = "modernize_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "modernize_v1.txt"


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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not configured")
    model = os.getenv("OPENAI_MODEL", "gpt-5.5")
    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=timeout)
        response = await asyncio.to_thread(
            client.responses.create,
            model=model,
            input=prompt,
            store=False,
        )
    except Exception as exc:
        raise LLMError(f"OpenAI request failed: {exc}") from exc
    code = _without_markdown_fences(getattr(response, "output_text", "") or "")
    if not code:
        raise LLMError("OpenAI returned an empty response")
    usage = getattr(response, "usage", None)
    return LLMResult(
        code=code,
        metadata={
            "provider": "openai",
            "model": getattr(response, "model", model),
            "prompt_version": PROMPT_VERSION,
            "response_id": getattr(response, "id", None),
            "usage": usage.model_dump() if hasattr(usage, "model_dump") else None,
        },
    )
