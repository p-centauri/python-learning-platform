from collections.abc import Awaitable, Callable, Iterator, Mapping
from dataclasses import asdict
import logging
import re
from typing import Annotated
import uuid
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, TimeoutError as PoolTimeout
from sqlalchemy.orm import Session, sessionmaker
from .auth import authorize
from .contracts import (
    AuthenticationRequired,
    BatchInput,
    ConflictingDatum,
    Cursor,
    CursorOutput,
    Datum,
    InputRow,
    PageOutput,
    PermissionDenied,
    ReceiptOutput,
    field,
)
from .database import HEAD
from .service import ingest, read_page


def create_app(engine: Engine, tokens: Mapping[str, str]) -> FastAPI:
    """Borrow a configured PostgreSQL engine; caller owns migrations/disposal. No DB access on creation."""
    if engine.dialect.name != "postgresql":
        raise ValueError("PostgreSQL engine required")
    snapshot = dict(tokens)
    if not 1 <= len(snapshot) <= 8:
        raise ValueError("configure 1..8 independent credentials")
    for token, namespace in snapshot.items():
        if type(token) is not str or re.fullmatch(r"[A-Za-z0-9_-]{16,64}", token) is None:
            raise ValueError("invalid credential configuration")
        field(namespace)
    app = FastAPI(title="Local ingestion service lab", version="0.1.0", docs_url=None, redoc_url=None)
    sessions = sessionmaker(engine, expire_on_commit=False)

    @app.middleware("http")
    async def correlation(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        trace = uuid.uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = trace
        response.headers["Cache-Control"] = "no-store"
        logging.getLogger("academy_ingestion_service").info(
            "request_completed", extra={"trace_id": trace, "status_code": response.status_code}
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "invalid request"})

    @app.exception_handler(DBAPIError)
    @app.exception_handler(PoolTimeout)
    async def storage_error(request: Request, error: DBAPIError | PoolTimeout) -> JSONResponse:
        # Error does not prove a known rollback/failed commit; clients must reconcile.
        return JSONResponse(status_code=503, content={"detail": "storage operation failed"})

    def permit(namespace: str, authorization: Annotated[str | None, Header()] = None) -> str:
        try:
            return authorize(snapshot, authorization, namespace)
        except AuthenticationRequired:
            raise HTTPException(
                401, "authentication required", headers={"WWW-Authenticate": "Bearer"}
            ) from None
        except PermissionDenied:
            raise HTTPException(403, "namespace access denied") from None
        except ValueError:
            raise HTTPException(422, "invalid namespace") from None

    def database(scope: Annotated[str, Depends(permit)]) -> Iterator[Session]:
        with sessions() as session:
            yield session

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        with sessions() as session:
            with session.begin():
                revision = session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
                if revision != HEAD:
                    raise HTTPException(503, "schema is not ready")
        return {"status": "ready"}

    @app.post("/namespaces/{namespace}/readings", response_model=ReceiptOutput, status_code=200)
    def post_readings(
        body: BatchInput,
        scope: Annotated[str, Depends(permit)],
        session: Annotated[Session, Depends(database, scope="function")],
    ) -> ReceiptOutput:
        rows = tuple(Datum(row.id, row.revision, row.value) for row in body.items)
        try:
            result = ingest(session, scope, rows)
        except ConflictingDatum:
            raise HTTPException(409, "reading identity conflicts") from None
        return ReceiptOutput(**asdict(result))

    @app.get("/namespaces/{namespace}/readings", response_model=PageOutput)
    def get_readings(
        scope: Annotated[str, Depends(permit)],
        session: Annotated[Session, Depends(database, scope="function")],
        limit: Annotated[str, Query(pattern=r"^(?:[1-9]|[12][0-9]|3[0-2])$")] = "16",
        after_id: str | None = None,
        after_revision: Annotated[str | None, Query(pattern=r"^[1-8]$")] = None,
    ) -> PageOutput:
        if (after_id is None) != (after_revision is None):
            raise HTTPException(422, "cursor fields must be paired")
        after = None
        if after_id is not None and after_revision is not None:
            try:
                after = Cursor(after_id, int(after_revision))
            except ValueError:
                raise HTTPException(422, "invalid cursor") from None
        result = read_page(session, scope, limit=int(limit), after=after)
        return PageOutput(
            items=[InputRow(id=row.id, revision=row.revision, value=row.value) for row in result.items],
            next_cursor=CursorOutput(id=result.next_cursor.id, revision=result.next_cursor.revision)
            if result.next_cursor
            else None,
        )

    return app
