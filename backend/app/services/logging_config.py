"""
Structured logging configuration.

Every log line is one JSON event. It carries the service identity, the context
that the current HTTP request added, and the fields of the call site, so an
operator can group events by request id or job id.

Log messages are constant strings. Dynamic values go into fields.
"""
import json
import logging
import os
import socket
import sys
import uuid
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Dict

SERVICE_NAME = "know-your-product-api"
SERVICE_VERSION = "1.0.0"

# Longest value that a field or an error message keeps in one event.
MAX_FIELD_CHARS = 500
MAX_STACK_CHARS = 8000

# Context that the current request or job added. An HTTP request sets it in
# RequestLoggingMiddleware, and each handler adds the identifiers it resolved.
_request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})

_configured = False


def _service_instance() -> str:
    """Identifier of this process, so that events of one replica group together."""
    return os.getenv("INSTANCE_ID") or socket.gethostname() or uuid.uuid4().hex[:12]


INSTANCE_ID = _service_instance()


def _environment() -> str:
    return (
        os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or os.getenv("VERCEL_ENV")
        or "development"
    )


def _clip(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"


def _normalize(fields: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            normalized[key] = None
        elif isinstance(value, str):
            normalized[key] = _clip(value, MAX_FIELD_CHARS)
        else:
            normalized[key] = value
    return normalized


class JsonFormatter(logging.Formatter):
    """Render one log record as one JSON event."""

    def format(self, record: logging.LogRecord) -> str:
        created = datetime.fromtimestamp(record.created, tz=timezone.utc)
        event: Dict[str, Any] = {
            "timestamp": created.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "service": SERVICE_NAME,
            "service_version": SERVICE_VERSION,
            "environment": _environment(),
            "instance": INSTANCE_ID,
            "logger": record.name,
        }

        event.update(_request_context.get())

        fields = getattr(record, "event_fields", None)
        if isinstance(fields, dict):
            event.update(fields)

        if record.exc_info:
            exception = record.exc_info[1]
            event["error"] = {
                "type": type(exception).__name__,
                "message": _clip(str(exception), MAX_FIELD_CHARS),
                "stack": _clip(self.formatException(record.exc_info), MAX_STACK_CHARS),
            }

        return json.dumps(event, default=str, ensure_ascii=False)


def configure_logging() -> None:
    """Install one JSON handler on the root logger. Safe to call more than once."""
    global _configured
    if _configured:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # Uvicorn installs plain-text handlers. Route its events through the JSON
    # handler instead, and drop its access log: RequestLoggingMiddleware emits a
    # richer event for the same request.
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.propagate = False

    _configured = True


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)


def log_event(event: str, level: int = logging.INFO, **fields: Any) -> None:
    """Emit one event. The event name is a constant string; values are fields."""
    get_logger().log(level, event, extra={"event_fields": _normalize(fields)})


def log_exception(
    event: str,
    error: BaseException,
    level: int = logging.ERROR,
    **fields: Any,
) -> None:
    """Emit one event with the type, message, and stack of the error."""
    get_logger().log(
        level,
        event,
        exc_info=error,
        extra={"event_fields": _normalize(fields)},
    )


def bind_request_context(**fields: Any) -> Token:
    """Start a context that every later event of this request carries."""
    return _request_context.set(_normalize(fields))


def update_request_context(**fields: Any) -> None:
    """Add identifiers that a handler resolved to the current request context."""
    merged = dict(_request_context.get())
    merged.update(_normalize(fields))
    _request_context.set(merged)


def reset_request_context(token: Token) -> None:
    _request_context.reset(token)


def current_request_context() -> Dict[str, Any]:
    return dict(_request_context.get())
