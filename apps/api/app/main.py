import logging
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from . import assessments, auth, learning, planning, projects, coding, retention, interactivity, comprehensive
from .config import settings
from .database import engine
from . import portfolios
from . import accounts
from . import exports

app = FastAPI(title="Engineering Academy API", version="0.1.0")
logger = logging.getLogger("academy")
auth_requests = defaultdict(deque)
rate_lock = Lock()


@app.middleware("http")
async def boundaries(request: Request, call_next):
    started = time.monotonic()
    request_id = uuid4().hex
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if request.headers.get("x-academy-request") != "1" or (
            origin and origin not in settings.allowed_origins.split(",")
        ):
            return JSONResponse({"detail": "Request origin could not be verified."}, status_code=403)
        if request.url.path in {
            "/api/auth/login",
            "/api/auth/register",
            "/api/account/recover",
            "/api/account/recovery-key",
            "/api/account/password",
        }:
            key = request.client.host if request.client else "unknown"
            now = time.monotonic()
            with rate_lock:
                # Bound storage to active clients, do not retain inactive addresses.
                for address in list(auth_requests):
                    if not auth_requests[address] or auth_requests[address][-1] < now - 60:
                        del auth_requests[address]
                window = auth_requests[key]
                while window and window[0] < now - 60:
                    window.popleft()
                if len(window) >= 20:
                    return JSONResponse(
                        {"detail": "Too many attempts. Try again in one minute."},
                        status_code=429,
                        headers={"Retry-After": "60"},
                    )
                window.append(now)
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > 262144:
                return JSONResponse({"detail": "Request exceeds the 256 KiB body limit."}, status_code=413)
            body.extend(chunk)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info(
        "request id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (time.monotonic() - started) * 1000,
    )
    return response


@app.get("/api/health")
def health():
    try:
        with engine.connect() as conn:
            actual = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if actual != "c3970b860e75":
            return JSONResponse({"status": "schema-not-ready"}, status_code=503)
        return {"status": "ok"}
    except SQLAlchemyError:
        return JSONResponse({"status": "database-unavailable"}, status_code=503)


@app.get("/api/health/live")
def live():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(comprehensive.router, prefix="/api")
app.include_router(portfolios.router, prefix="/api")
app.include_router(planning.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(coding.router, prefix="/api")
app.include_router(retention.router, prefix="/api")
app.include_router(interactivity.router, prefix="/api")
