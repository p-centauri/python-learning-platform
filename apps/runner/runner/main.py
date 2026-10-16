import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache
import hmac
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
from threading import BoundedSemaphore
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .sandbox import SandboxFailure, execute, checked
from .verification import verify

token = os.environ.get("RUNNER_TOKEN", "")
gate = BoundedSemaphore(1)


@lru_cache
def definitions():
    return json.loads((Path(__file__).resolve().parents[3] / "content/coding-exercises.json").read_text())


@asynccontextmanager
async def lifespan(app):
    app.state.verification = None
    if len(token) < 32:
        raise RuntimeError("RUNNER_TOKEN must contain at least 32 characters.")
    try:
        app.state.verification = await asyncio.to_thread(verify)
        logging.getLogger("runner").warning("Runner isolation verified: %s", app.state.verification["checks"])
    except Exception:
        logging.getLogger("runner").exception("Runner verification failed. Learner execution is disabled.")
    yield


app = FastAPI(
    title="Academy isolated runner", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
)


@app.middleware("http")
async def boundary(request: Request, call_next):
    supplied = request.headers.get("x-runner-token", "")
    if len(token) < 32 or not hmac.compare_digest(supplied.encode(), token.encode()):
        return JSONResponse({"detail": "Runner authentication required."}, status_code=401)
    if request.method == "POST":
        try:
            length = int(request.headers.get("content-length", "-1"))
        except ValueError:
            length = -1
        if not 0 <= length <= 65536:
            return JSONResponse({"detail": "Runner body limit exceeded."}, status_code=413)
    return await call_next(request)


@app.get("/health")
def health():
    if app.state.verification is not None:
        try:
            checked(["version", "--format", "{{.Server.Version}}"], timeout=2)
        except SandboxFailure:
            app.state.verification = None
    return {
        "ready": app.state.verification is not None,
        "version": definitions()["version"],
        "verification": app.state.verification,
    }


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exercise_id: str = Field(max_length=100)
    version: str = Field(max_length=60)
    code: str = Field(min_length=1, max_length=12000)

    @field_validator("code")
    @classmethod
    def code_size(cls, value):
        if len(value.encode()) > 16384 or not value.strip():
            raise ValueError("Code must be nonblank and at most 16 KiB UTF-8.")
        return value


@app.post("/run")
def run(data: RunInput):
    if app.state.verification is None:
        raise HTTPException(503, "Isolation verification is incomplete. Execution is disabled.")
    definition = next((e for e in definitions()["exercises"] if e["id"] == data.exercise_id), None)
    if data.version != definitions()["version"] or definition is None:
        raise HTTPException(
            409, "Runner content does not match the academy. Restart both services after content changes."
        )
    return run_definition(data.code, definition)


class ExamRunInput(RunInput):
    exercise_id: str = "practical-repair-v1"
    exam_id: str = Field(max_length=100)
    execution_digest: str = Field(min_length=64, max_length=64)


@lru_cache
def repair_definition():
    return json.loads(
        (Path(__file__).resolve().parents[3] / "content/assessments/practical-repair-v1.json").read_text()
    )


@app.post("/exam-run")
def exam_run(data: ExamRunInput):
    exam = repair_definition()
    digest = sha256(json.dumps(exam["execution"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if data.exam_id != exam["id"] or data.version != exam["version"] or data.execution_digest != digest:
        raise HTTPException(409, "Frozen practical content does not match the runner. No grade was recorded.")
    return run_definition(data.code, exam["execution"])


def run_definition(code, definition):
    if app.state.verification is None:
        raise HTTPException(503, "Isolation verification is incomplete. Execution is disabled.")
    if not gate.acquire(blocking=False):
        raise HTTPException(429, "The runner is busy. Save your code and try again shortly.")
    try:
        return execute(code, definition)
    except SandboxFailure as error:
        app.state.verification = None
        raise HTTPException(503, str(error)) from error
    except Exception as error:
        app.state.verification = None
        logging.getLogger("runner").exception("Runner failure; disabled until restart.")
        raise HTTPException(
            503, "The runner stopped safely. Restart it to verify isolation again."
        ) from error
    finally:
        gate.release()
