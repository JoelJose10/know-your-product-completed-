"""
HTTP request observability.

Every HTTP request gets a request id and exactly one event. It carries the
method, the path, the status, the duration, the request id, and the identifiers
that handlers added. The same request id goes back to the caller in the
x-request-id response header.

The event is emitted when the response body is complete, so background work that
runs after the response (the upload pipeline) does not delay it and does not
count in duration_ms.
"""
import logging
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.services.logging_config import (
    bind_request_context,
    log_event,
    log_exception,
    reset_request_context,
)

REQUEST_ID_HEADER = "x-request-id"
MAX_REQUEST_ID_CHARS = 128


def _request_id(headers: Headers) -> str:
    incoming = (headers.get(REQUEST_ID_HEADER) or "").strip()
    if incoming:
        return incoming[:MAX_REQUEST_ID_CHARS]
    return uuid.uuid4().hex


def _log_level(status_code: int) -> int:
    if status_code >= 500:
        return logging.ERROR
    if status_code >= 400:
        return logging.WARNING
    return logging.INFO


class RequestLoggingMiddleware:
    """Emit one event per HTTP request, including the unhandled error if one occurs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = _request_id(headers)
        token = bind_request_context(
            request_id=request_id,
            http_method=scope.get("method"),
            http_path=scope.get("path"),
        )

        status_code = 500
        error: Exception | None = None
        started = time.perf_counter()
        duration_ms: float | None = None
        emitted = False

        def emit() -> None:
            """Write the one event of this request. Later calls do nothing."""
            nonlocal emitted, duration_ms
            if emitted:
                return
            emitted = True
            if duration_ms is None:
                duration_ms = round((time.perf_counter() - started) * 1000, 2)

            fields = {"http_status": status_code, "duration_ms": duration_ms}

            # A job id in the path keeps this event joinable with the job events,
            # also when the handler rejected the request before it read the job.
            path_params = scope.get("path_params") or {}
            if isinstance(path_params, dict) and path_params.get("job_id"):
                fields["job_id"] = path_params["job_id"]

            if error is None:
                log_event("http_request_completed", level=_log_level(status_code), **fields)
            else:
                log_exception("http_request_completed", error, level=logging.ERROR, **fields)

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, duration_ms
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message).append(REQUEST_ID_HEADER, request_id)
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                duration_ms = round((time.perf_counter() - started) * 1000, 2)
                # A 5xx can still become an unhandled error, so it is reported in
                # the finally block with the error object attached.
                if status_code < 500:
                    emit()

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception as exc:
            error = exc
            raise
        finally:
            emit()
            reset_request_context(token)
