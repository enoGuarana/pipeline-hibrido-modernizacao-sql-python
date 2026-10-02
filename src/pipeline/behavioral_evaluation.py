"""Comparison primitives for isolated behavioral evaluation.

This module does not execute generated code or claim equivalence by itself. A
scenario runner must provide observations captured from the legacy routine and
the translated implementation in an isolated environment.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BehavioralObservation:
    """Observable result of one scenario execution."""

    return_value: Any
    table_state: dict[str, Any]
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class BehavioralComparison:
    """Comparison result with explicit normalization metadata."""

    equivalent: bool
    differences: tuple[str, ...]
    normalized_paths: tuple[str, ...]


def _canonical(value: Any, *, path: str, volatile_paths: frozenset[str], normalized: list[str]) -> Any:
    if path in volatile_paths:
        normalized.append(path)
        return "<volatile>"
    if isinstance(value, (datetime, date, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): _canonical(item, path=f"{path}.{key}", volatile_paths=volatile_paths, normalized=normalized)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [
            _canonical(item, path=f"{path}[{index}]", volatile_paths=volatile_paths, normalized=normalized)
            for index, item in enumerate(value)
        ]
    return value


def compare_observations(
    legacy: BehavioralObservation,
    translated: BehavioralObservation,
    *,
    volatile_paths: set[str] | frozenset[str] = frozenset(),
) -> BehavioralComparison:
    """Compare return, state and error without hiding undeclared differences."""
    normalized: list[str] = []
    legacy_value = _canonical(
        {"return": legacy.return_value, "state": legacy.table_state, "error": legacy.error},
        path="$",
        volatile_paths=frozenset(volatile_paths),
        normalized=normalized,
    )
    translated_value = _canonical(
        {"return": translated.return_value, "state": translated.table_state, "error": translated.error},
        path="$",
        volatile_paths=frozenset(volatile_paths),
        normalized=normalized,
    )
    if legacy_value == translated_value:
        return BehavioralComparison(True, (), tuple(sorted(set(normalized))))
    return BehavioralComparison(
        False,
        (f"legacy={legacy_value!r}", f"translated={translated_value!r}"),
        tuple(sorted(set(normalized))),
    )
