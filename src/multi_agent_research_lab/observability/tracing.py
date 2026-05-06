"""Tracing hooks with optional Langfuse integration.

The system always records local span dictionaries and, when Langfuse credentials are
available, also exports traces/spans to Langfuse.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

_langfuse_client: Any | None = None
_current_trace: Any | None = None


def get_langfuse_client() -> Any | None:
    """Return a cached Langfuse client when credentials are configured."""
    global _langfuse_client
    settings = get_settings()
    if not settings.tracing_enabled:
        return None
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    if _langfuse_client is not None:
        return _langfuse_client

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        logger.info("Langfuse tracing enabled")
    except Exception as exc:
        logger.warning("Langfuse tracing disabled: %s", exc)
        _langfuse_client = None
    return _langfuse_client


def start_trace(name: str, user_id: str | None = None, metadata: dict[str, Any] | None = None) -> Any | None:
    """Start a Langfuse trace and make it current for child spans."""
    global _current_trace
    client = get_langfuse_client()
    if client is None:
        _current_trace = None
        return None
    try:
        _current_trace = client.trace(name=name, user_id=user_id, metadata=metadata or {})
        return _current_trace
    except Exception as exc:
        logger.warning("Failed to start Langfuse trace: %s", exc)
        _current_trace = None
        return None


def flush_traces() -> None:
    """Flush pending Langfuse events."""
    client = get_langfuse_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:
        logger.warning("Failed to flush Langfuse traces: %s", exc)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Trace a unit of work locally and in Langfuse when configured."""
    started = perf_counter()
    attrs = attributes or {}
    span: dict[str, Any] = {"name": name, "attributes": attrs, "duration_seconds": None}

    langfuse_span = None
    if _current_trace is not None:
        try:
            langfuse_span = _current_trace.span(name=name, input=attrs, metadata=attrs)
        except Exception as exc:
            logger.warning("Failed to create Langfuse span '%s': %s", name, exc)

    try:
        yield span
        if langfuse_span is not None:
            try:
                langfuse_span.end(output=span.get("output"), metadata=span)
            except Exception as exc:
                logger.warning("Failed to end Langfuse span '%s': %s", name, exc)
    except Exception as exc:
        span["error"] = str(exc)
        if langfuse_span is not None:
            try:
                langfuse_span.end(output={"error": str(exc)}, metadata=span, level="ERROR")
            except Exception:
                pass
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
