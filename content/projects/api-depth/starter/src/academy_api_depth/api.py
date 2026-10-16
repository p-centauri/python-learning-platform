from collections.abc import Awaitable, Callable, Mapping
from dataclasses import asdict
from hashlib import sha256
import logging
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, TimeoutError as PoolTimeout
from starlette.concurrency import run_in_threadpool
from academy_delivery_release import assess
from academy_ingestion_service import create_app as old_app
from academy_ingestion_service.auth import authorize
from academy_ingestion_service.contracts import (
    AuthenticationRequired,
    ConflictingDatum,
    PermissionDenied,
    field,
)
from .contracts import DeliveryConflict, InvalidSignature
from .operations import accept, matches, verify
from .support import key, parse, representation


def create_app(
    engine: Engine,
    tokens: Mapping[str, str],
    secrets: Mapping[str, bytes],
    *,
    clock: Callable[[], int] = lambda: int(time.time()),
) -> FastAPI:
    """Borrow engine and copy authority; no import/factory/request DDL or disposal."""
    authority = dict(tokens)
    child = old_app(engine, authority)  # Reuse unchanged credential configuration validation.
    signing = dict(secrets)
    if not 1 <= len(signing) <= 8:
        raise ValueError("configure 1..8 signing scopes")
    for scope, secret in signing.items():
        field(scope)
        key(secret)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def observe(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        trace = uuid.uuid4().hex
        response.headers["X-Request-ID"] = trace
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        logging.getLogger("academy_api_depth").info(
            "request_completed", extra={"trace_id": trace, "status_code": response.status_code}
        )
        return response

    @app.exception_handler(DBAPIError)
    @app.exception_handler(PoolTimeout)
    async def storage(request: Request, error: DBAPIError | PoolTimeout) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "storage operation failed"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        state = assess(engine)
        if not state.ready:
            raise HTTPException(503, "schema is not ready")
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL lock_timeout = '250ms'"))
            connection.execute(text("SET LOCAL statement_timeout = '1000ms'"))
            connection.execute(
                text("SELECT namespace, delivery_id, body_digest FROM api_webhook_receipt LIMIT 0")
            )
        return {"status": "ready"}

    @app.get("/v1/namespaces/{namespace}/snapshot")
    def snapshot(namespace: str, request: Request) -> Response:
        authorization = request.headers.getlist("authorization")
        try:
            scope = authorize(authority, authorization[0] if len(authorization) == 1 else None, namespace)
        except AuthenticationRequired:
            raise HTTPException(
                401, "authentication required", headers={"WWW-Authenticate": "Bearer"}
            ) from None
        except PermissionDenied:
            raise HTTPException(403, "namespace access denied") from None
        except ValueError:
            raise HTTPException(422, "invalid namespace") from None
        limits = request.query_params.getlist("limit")
        if any(name != "limit" for name in request.query_params) or len(limits) > 1:
            raise HTTPException(422, "invalid request")
        raw = limits[0] if limits else "16"
        if raw not in {str(i) for i in range(1, 33)}:
            raise HTTPException(422, "invalid request")
        conditions = request.headers.getlist("if-none-match")
        conditional = ",".join(conditions) if conditions else None
        # Validate the bounded header before connecting, but only after permission.
        try:
            matches(conditional, '"probe"')
        except ValueError:
            raise HTTPException(400, "invalid conditional header") from None
        body, etag = representation(engine, scope, int(raw))
        headers = {"ETag": etag, "Cache-Control": "private, no-cache", "Vary": "Authorization"}
        if matches(conditional, etag):
            return Response(status_code=304, headers=headers)
        return Response(body, media_type="application/json", headers=headers)

    @app.post("/v1/namespaces/{namespace}/webhooks")
    async def webhook(namespace: str, request: Request) -> JSONResponse:
        secret = signing.get(namespace)
        if secret is None:
            raise HTTPException(401, "webhook authentication required")
        values: list[str] = []
        for name in ("x-delivery-id", "x-signed-at", "x-signature"):
            found = request.headers.getlist(name)
            if len(found) != 1:
                raise HTTPException(401, "webhook authentication required")
            values.append(found[0])
        if request.headers.get("content-type", "").lower() != "application/json":
            raise HTTPException(415, "application/json required")
        if request.headers.get("content-encoding", "identity").lower() != "identity":
            raise HTTPException(415, "identity encoding required")
        chunks = bytearray()
        async for chunk in request.stream():
            if len(chunks) + len(chunk) > 4096:
                raise HTTPException(413, "event too large")
            chunks.extend(chunk)
        body = bytes(chunks)
        delivery, timestamp, signature = values
        try:
            verify(secret, namespace, delivery, timestamp, signature, body, now=clock())
        except InvalidSignature:
            raise HTTPException(401, "webhook authentication required") from None
        try:
            datum = parse(body)
        except ValueError:
            raise HTTPException(422, "invalid event") from None
        try:
            duplicate = await run_in_threadpool(
                accept, engine, namespace, delivery, sha256(body).hexdigest(), datum
            )
        except DeliveryConflict:
            raise HTTPException(409, "delivery identity conflicts") from None
        except ConflictingDatum:
            raise HTTPException(409, "reading identity conflicts") from None
        return JSONResponse(dict(duplicate=duplicate, reading=asdict(datum)))

    app.mount("/", child)
    return app
