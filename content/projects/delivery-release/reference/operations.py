from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from threading import Event
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import DBAPIError, TimeoutError as PoolTimeout
from academy_ingestion_service import create_app, make_engine
from academy_ingestion_service.database import url_from_dsn
from academy_delivery_schema import HEAD
from academy_delivery_schema.metadata import metadata
from .contracts import Readiness, Reason, Release, Settings, StartupRefused
from .support import emit, revalidate, snapshot


def load_settings(environment: Mapping[str, str]) -> Settings:
    return snapshot(environment)


def assess(engine: Engine) -> Readiness:
    if engine.dialect.name != "postgresql" or engine.dialect.driver != "psycopg2":
        raise ValueError("release requires PostgreSQL/psycopg2")
    try:
        with engine.connect() as connection, connection.begin():
            raw = connection.connection.dbapi_connection
            if raw is None or connection.get_isolation_level() != "READ COMMITTED" or raw.autocommit:
                raise ValueError("release requires non-autocommit READ COMMITTED")
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL lock_timeout = '250ms'"))
            connection.execute(text("SET LOCAL statement_timeout = '1000ms'"))
            heads = tuple(connection.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num LIMIT 2")).scalars())
            if heads != (HEAD,):
                return Readiness(Reason.SCHEMA_HEAD)
            for table in metadata.sorted_tables:
                connection.execute(select(table).limit(0))
        return Readiness(Reason.READY)
    except DBAPIError as error:
        state = getattr(error.orig, "pgcode", None)
        return Readiness(Reason.SCHEMA_CONTRACT if state in {"42P01", "42703"} else Reason.STORAGE_UNAVAILABLE)
    except PoolTimeout:
        return Readiness(Reason.STORAGE_UNAVAILABLE)


def create_release(settings: Settings) -> Release:
    configured = revalidate(settings)
    engine = make_engine(url_from_dsn(configured.dsn))
    stopped, running = Event(), Event()
    disposed = False

    def dispose() -> None:
        nonlocal disposed
        if not disposed:
            disposed = True
            engine.dispose()
            emit("disposed", Reason.STOPPING)

    @asynccontextmanager
    async def lifetime(app: FastAPI) -> AsyncIterator[None]:
        try:
            readiness = Readiness(Reason.STOPPING) if stopped.is_set() else assess(engine)
            if not readiness.ready or stopped.is_set():
                reason = Reason.STOPPING if stopped.is_set() else readiness.reason
                emit("startup-refused", reason)
                raise StartupRefused(reason)
            running.set()
            emit("startup-ready", Reason.READY)
            yield
        finally:
            stopped.set()
            running.clear()
            emit("stopping", Reason.STOPPING)
            dispose()

    try:
        child = create_app(engine, dict(configured.tokens))
        app = FastAPI(title="Local compatible release", docs_url=None, redoc_url=None, lifespan=lifetime)

        @app.middleware("http")
        async def admission(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
            if request.url.path not in {"/health", "/ready"} and (stopped.is_set() or not running.is_set()):
                response: Response = JSONResponse({"detail": "release is stopping"}, status_code=503)
            else:
                response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        @app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "alive"}

        @app.get("/ready")
        def ready() -> JSONResponse:
            result = Readiness(Reason.STOPPING) if stopped.is_set() or not running.is_set() else assess(engine)
            return JSONResponse({"status": "ready" if result.ready else "not-ready", "reason": result.reason.value}, status_code=200 if result.ready else 503)

        app.mount("/", child)
        return Release(app, stopped)
    except BaseException:
        dispose()
        raise
