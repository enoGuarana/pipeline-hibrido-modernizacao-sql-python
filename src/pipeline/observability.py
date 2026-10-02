"""Optional Langfuse tracing with a no-op path when credentials are absent."""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import Any, ParamSpec, TypeVar

try:
    from langfuse import get_client
except ImportError:  # pragma: no cover - exercised by the dependency-free path
    get_client = None  # type: ignore[assignment]

P = ParamSpec("P")
R = TypeVar("R")


def tracing_enabled() -> bool:
    """Return true only when SDK and both project credentials are configured."""

    # Sem as duas chaves, o caminho é no-op: observabilidade não pode impedir
    # desenvolvimento local nem enviar dados acidentalmente.
    return bool(
        get_client
        and os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    )


@contextmanager
def observation(
    name: str,
    *,
    input_data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    as_type: str = "span",
) -> Iterator[Any]:
    """Create a Langfuse observation or transparently do nothing."""

    # O mesmo context manager atende Cloud e self-host via LANGFUSE_HOST; o
    # restante da aplicação não precisa conhecer detalhes do provedor.
    if not tracing_enabled():
        yield None
        return

    client = get_client()
    with client.start_as_current_observation(
        as_type=as_type,
        name=name,
        input=input_data,
        metadata=metadata,
    ) as current:
        try:
            yield current
        except Exception as exc:
            current.update(level="ERROR", status_message=str(exc))
            raise
    client.flush()


def trace_node(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Trace a graph node while keeping its original sync/async contract."""

    # O decorator preserva funções síncronas e assíncronas, porque o grafo usa
    # ambos os tipos sem alterar o contrato esperado pelo LangGraph.
    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                state = args[0] if args else {}
                with observation(
                    name,
                    input_data={"run_id": state.get("run_id"), "status": state.get("status")},
                    metadata={"component": "langgraph.node"},
                ) as current:
                    result = await function(*args, **kwargs)  # type: ignore[misc]
                    if current is not None:
                        current.update(output={"status": result.get("status")})
                    return result

            return async_wrapper  # type: ignore[return-value]

        @wraps(function)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            state = args[0] if args else {}
            with observation(
                name,
                input_data={"run_id": state.get("run_id"), "status": state.get("status")},
                metadata={"component": "langgraph.node"},
            ) as current:
                result = function(*args, **kwargs)
                if current is not None:
                    current.update(output={"status": result.get("status")})
                return result

        return sync_wrapper

    return decorator
