"""Deterministic structural extraction for the PL/pgSQL challenge fixtures.

This module deliberately does not claim to be a complete PL/pgSQL parser. It
extracts the routine wrapper and classifies body constructs while preserving
the original body for later analysis and generation.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .contracts import IntermediateRepresentation, ParameterContract


def _split_top_level(value: str, delimiter: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    for index, char in enumerate(value):
        if quote:
            if char == quote and (index == 0 or value[index - 1] != "\\"):
                quote = None
            continue
        if char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == delimiter and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]


def _mask_comments_and_strings(source: str) -> str:
    """Mask comments and quoted strings without changing offsets."""
    chars = list(source)
    index = 0
    while index < len(chars):
        if source.startswith("--", index):
            end = source.find("\n", index)
            end = len(source) if end < 0 else end
            for position in range(index, end):
                chars[position] = " "
            index = end
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            end = len(source) - 2 if end < 0 else end
            for position in range(index, end + 2):
                chars[position] = " "
            index = end + 2
            continue
        if chars[index] == "'":
            index += 1
            while index < len(chars):
                chars[index] = " "
                if source[index] == "'":
                    if index + 1 < len(chars) and source[index + 1] == "'":
                        chars[index + 1] = " "
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
            continue
        index += 1
    return "".join(chars)


def _parameters(raw: str) -> list[ParameterContract]:
    result: list[ParameterContract] = []
    for item in _split_top_level(raw):
        tokens = item.split()
        if not tokens:
            continue
        mode = tokens[0].upper() if tokens[0].upper() in {"IN", "OUT", "INOUT"} else "IN"
        if mode != "IN":
            tokens.pop(0)
        if not tokens:
            continue
        name = tokens.pop(0)
        result.append({"name": name, "mode": mode, "data_type": " ".join(tokens) or None})  # type: ignore[typeddict-item]
    return result


def _wrapper(source: str) -> tuple[re.Match[str], str, str] | None:
    match = re.search(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?(?P<kind>FUNCTION|PROCEDURE)\s+"
        r"(?P<name>[\w.]+)\s*\(",
        source,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    open_index = source.find("(", match.start())
    depth = 0
    close_index = -1
    quote: str | None = None
    for index in range(open_index, len(source)):
        char = source[index]
        if quote:
            if char == quote and source[index - 1] != "\\":
                quote = None
            continue
        if char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                close_index = index
                break
    if close_index < 0:
        return None
    body_match = re.search(r"\$\$(?P<body>.*?)\$\$", source[close_index:], re.IGNORECASE | re.DOTALL)
    if body_match is None:
        return None
    header_end = close_index + body_match.start()
    return match, source[open_index + 1 : close_index], source[close_index + 1 : header_end]


def parse_routine(source: str) -> tuple[dict[str, Any], IntermediateRepresentation] | None:
    found = _wrapper(source)
    if found is None:
        return None
    match, raw_parameters, header = found
    body_match = re.search(r"\$\$(?P<body>.*?)\$\$", source, re.IGNORECASE | re.DOTALL)
    if body_match is None:
        return None
    body = body_match.group("body")
    masked = _mask_comments_and_strings(body)
    language_match = re.search(r"LANGUAGE\s+(\w+)", header, re.IGNORECASE)
    returns_match = re.search(r"RETURNS\s+(.+?)(?=\s+LANGUAGE\b|\s+AS\b|$)", header, re.IGNORECASE | re.DOTALL)
    declaration = re.sub(r"^\s*DECLARE\b", "", body.split("BEGIN", 1)[0], flags=re.IGNORECASE)
    variable_pattern = re.compile(r"^\s*([a-z_]\w*)\s+([^;]+);", re.IGNORECASE | re.MULTILINE)
    variables = [
        {"name": name, "data_type": data_type.strip()}
        for name, data_type in variable_pattern.findall(declaration)
    ]
    keywords = {
        "select": r"\bSELECT\b",
        "insert": r"\bINSERT\b",
        "update": r"\bUPDATE\b",
        "delete": r"\bDELETE\b",
        "cursor": r"\bCURSOR\b",
        "loop": r"\b(?:LOOP|FOR\s+\w+\s+IN)\b",
        "cte_recursive": r"\bWITH\s+RECURSIVE\b",
        "exception": r"\bEXCEPTION\b",
        "raise": r"\bRAISE\b",
        "locking": r"\bFOR\s+UPDATE\b|\bFOR\s+SHARE\b",
        "jsonb": r"\bJSONB\b|\bJSONB_[A-Z_]+\b",
        "function_call": r"\b[A-Z_]\w*\s*\(",
    }
    operations = [name for name, pattern in keywords.items() if re.search(pattern, masked, re.IGNORECASE)]
    table_matches = re.findall(
        r"\b(?:FROM|JOIN|UPDATE|INTO)\s+([a-z_]\w*)", masked, re.IGNORECASE
    )
    call_matches = re.findall(r"\b([a-z_]\w*)\s*\(", masked, re.IGNORECASE)
    unsupported = []
    for marker in ("COMMIT", "ROLLBACK", "SAVEPOINT", "PERFORM", "EXECUTE"):
        if re.search(rf"\b{marker}\b", masked, re.IGNORECASE):
            unsupported.append(marker)
    variable_names = {variable["name"] for variable in variables}
    ir: IntermediateRepresentation = {
        "routine_name": match.group("name"),
        "routine_kind": match.group("kind").lower(),  # type: ignore[typeddict-item]
        "language": language_match.group(1) if language_match else None,
        "parameters": _parameters(raw_parameters),
        "return_type": returns_match.group(1).strip() if returns_match else None,
        "variables": variables,
        "operations": operations,
        "tables": sorted({table for table in table_matches if table not in variable_names}),
        "function_calls": sorted(set(call_matches)),
        "source_spans": [],
        "unsupported_constructs": unsupported,
    }
    return ({"body": body, "header": header, "masked_body": masked, "source_sha256": hashlib.sha256(source.encode()).hexdigest()}, ir)
