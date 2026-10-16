from copy import deepcopy
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from pydantic import ConfigDict, StrictInt, StrictStr
from sqlalchemy import select
from .auth import DB, Learner
from .content import catalog, exam_by_id, exam_definitions, lessons
from .config import settings
from .exam_grading import grade_exam
from .learning import Toggle
from .models import ExamAttempt, ProjectProgress, utcnow
from .comprehensive import visible_questions, validate_answer, complete, finish_nonknowledge, review_artifact
from .projects import utc_timestamp

router = APIRouter(tags=["assessments"])


def definition(exam_id="knowledge-pilot-v1"):
    exam = exam_by_id(exam_id)
    if not exam:
        raise HTTPException(404, "Assessment not found.")
    return exam


def owned_attempt(attempt_id, user, db):
    attempt = db.scalar(
        select(ExamAttempt).where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == user.id)
    )
    if not attempt:
        raise HTTPException(404, "Assessment attempt not found.")
    return attempt


def attempt_definition(attempt):
    if not attempt.definition_snapshot:
        raise HTTPException(
            409, "This legacy attempt needs its content snapshot restored. Contact the administrator."
        )
    return attempt.definition_snapshot


def public_attempt(attempt):
    exam = attempt_definition(attempt)
    return {
        "id": attempt.id,
        "exam_id": attempt.exam_id,
        "title": exam["title"],
        "version": exam.get("version", exam["id"]),
        "level": exam.get("level", "Mixed diagnostic"),
        "status": attempt.status,
        "answers": attempt.answers,
        "result": attempt.result,
        "started_at": utc_timestamp(attempt.started_at),
        "mode": exam.get("mode", "knowledge"),
        "minutes": exam["minutes"],
        "workspace": attempt.workspace,
        "stage": (
            {
                "index": attempt.workspace.get("stage", 0),
                "count": len(exam["stages"]),
                "title": exam["stages"][attempt.workspace.get("stage", 0)]["title"],
            }
            if exam.get("mode") == "design"
            else None
        ),
        "execution": (
            {
                "starter": exam["execution"]["starter"],
                "prompt": exam["execution"]["prompt"],
                "check_count": len(exam["execution"]["tests"]),
                "download_url": "/api/exam-packs/practical-repair-v1",
            }
            if exam.get("mode") == "repair"
            else None
        ),
        "questions": [
            {
                key: question[key]
                for key in (
                    "id",
                    "skill",
                    "prompt",
                    "options",
                    "code",
                    "kind",
                    "min_length",
                    "max_length",
                    "title",
                )
                if key in question
            }
            for question in visible_questions(attempt)
        ],
    }


def public_definition(exam):
    return {
        **{key: exam[key] for key in ("id", "title", "description", "minutes")},
        "level": exam.get("level", "Mixed diagnostic"),
        "mode": exam.get("mode", "knowledge"),
        "question_count": len(exam["questions"])
        if exam.get("mode") != "design"
        else sum(len(s["questions"]) for s in exam["stages"]),
        "topics": list(dict.fromkeys(question["skill"] for question in exam["questions"])),
        "libraries": exam.get("libraries", []),
        "library_note": exam.get("library_note", ""),
        "practical_followup": exam.get("practical_followup"),
        "evaluation_policy": exam.get("evaluation_policy"),
    }


@router.get("/exams")
def exams(user: Learner, db: DB):
    attempts = db.scalars(
        select(ExamAttempt).where(ExamAttempt.user_id == user.id).order_by(ExamAttempt.id.desc())
    )
    pilot = public_definition(definition())
    return {
        "exams": [public_definition(exam) for exam in exam_definitions()],
        # Preserve the original read contract for existing clients.
        "exam": pilot,
        "question_count": pilot["question_count"],
        "attempts": [
            {
                "id": attempt.id,
                "exam_id": attempt.exam_id,
                "title": attempt_definition(attempt)["title"],
                "status": attempt.status,
                "result": attempt.result,
                "started_at": attempt.started_at,
            }
            for attempt in attempts
        ],
    }


class StartExam(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exam_id: str = Field(default="knowledge-pilot-v1", max_length=100)


@router.post("/exams/start", status_code=201)
def start(user: Learner, db: DB, data: StartExam | None = None):
    exam = definition(data.exam_id if data else "knowledge-pilot-v1")
    existing = db.scalar(
        select(ExamAttempt).where(
            ExamAttempt.user_id == user.id, ExamAttempt.exam_id == exam["id"], ExamAttempt.status == "active"
        )
    )
    if existing:
        return public_attempt(existing)
    attempt = ExamAttempt(
        user_id=user.id, exam_id=exam["id"], definition_snapshot=deepcopy(exam), answers={}, status="active"
    )
    db.add(attempt)
    db.flush()
    return public_attempt(attempt)


@router.get("/exams/attempts/{attempt_id}")
def get_attempt(attempt_id: int, user: Learner, db: DB):
    return public_attempt(owned_attempt(attempt_id, user, db))


class ExamAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str
    answer: StrictInt | list[StrictInt] | StrictStr


@router.put("/exams/attempts/{attempt_id}/answer")
def save_answer(attempt_id: int, data: ExamAnswer, user: Learner, db: DB):
    attempt = owned_attempt(attempt_id, user, db)
    if attempt.status != "active":
        raise HTTPException(409, "Submitted answers cannot be changed.")
    question = next((q for q in visible_questions(attempt) if q["id"] == data.question_id), None)
    if not question:
        raise HTTPException(422, "Invalid question or answer.")
    exam = attempt_definition(attempt)
    if exam.get("mode") == "design":
        current = exam["stages"][attempt.workspace.get("stage", 0)]["questions"]
        if data.question_id not in {q["id"] for q in current}:
            raise HTTPException(409, "Earlier design stages are committed and cannot be edited.")
    validate_answer(question, data.answer)
    attempt.answers = {**attempt.answers, data.question_id: data.answer}
    return {"saved": True}


@router.post("/exams/attempts/{attempt_id}/submit")
def submit_exam(attempt_id: int, user: Learner, db: DB):
    attempt = owned_attempt(attempt_id, user, db)
    if attempt.status == "submitted":
        return public_attempt(attempt)
    exam = attempt_definition(attempt)
    if exam.get("mode") in {"design", "repair"}:
        attempt.result = finish_nonknowledge(attempt, db)
    else:
        complete(exam["questions"], attempt.answers)
        attempt.result = review_artifact(attempt, grade_exam(exam, attempt.answers, lessons()), db)
    attempt.status = "submitted"
    attempt.submitted_at = utcnow()
    return public_attempt(attempt)


@router.get("/projects")
def projects(user: Learner, db: DB):
    progress = {
        (p.project_id, p.task_id)
        for p in db.scalars(select(ProjectProgress).where(ProjectProgress.user_id == user.id))
    }
    return [
        {**p, "tasks": [{**t, "completed": (p["id"], t["id"]) in progress} for t in p["tasks"]]}
        for p in catalog()["projects"]
    ]


@router.get("/projects/{project_id}/starter")
def project_starter(project_id: str, user: Learner):
    # Authenticated, fixed authored files only. Never accept a filesystem path
    # from the caller or include the maintainer reference/answer banks.
    bundles = {
        "ai-evaluation": (
            "ai-evaluation",
            (
                "README.md",
                "RELEASE_CONTRACT.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_ai_evaluation/__init__.py",
                "src/academy_ai_evaluation/contracts.py",
                "src/academy_ai_evaluation/dataset.py",
                "src/academy_ai_evaluation/harness.py",
                "src/academy_ai_evaluation/operations.py",
                "src/academy_ai_evaluation/py.typed",
                "src/academy_ai_evaluation/release-cases.json",
                "tests/test_dataset.py",
                "tests/test_gates.py",
                "tests/test_harness.py",
                "tests/test_metrics.py",
            ),
        ),
        "tools": (
            "tools",
            (
                "README.md",
                "TOOL_CONTRACT.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_tools/__init__.py",
                "src/academy_tools/contracts.py",
                "src/academy_tools/fixtures.py",
                "src/academy_tools/operations.py",
                "src/academy_tools/py.typed",
                "src/academy_tools/store.py",
                "src/academy_tools/support.py",
                "tests/test_execution.py",
                "tests/test_fixture.py",
                "tests/test_loop.py",
                "tests/test_proposals.py",
            ),
        ),
        "rag": (
            "rag",
            (
                "RAG_CONTRACT.md",
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_rag/__init__.py",
                "src/academy_rag/contracts.py",
                "src/academy_rag/fixtures.py",
                "src/academy_rag/operations.py",
                "src/academy_rag/py.typed",
                "src/academy_rag/store.py",
                "src/academy_rag/support.py",
                "tests/test_answers.py",
                "tests/test_context.py",
                "tests/test_fixture.py",
                "tests/test_store.py",
            ),
        ),
        "retrieval": (
            "retrieval",
            (
                "README.md",
                "RETRIEVAL_CONTRACT.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_retrieval/__init__.py",
                "src/academy_retrieval/contracts.py",
                "src/academy_retrieval/dataset.py",
                "src/academy_retrieval/fixture.json",
                "src/academy_retrieval/operations.py",
                "src/academy_retrieval/py.typed",
                "src/academy_retrieval/support.py",
                "tests/test_chunks.py",
                "tests/test_fixture.py",
                "tests/test_metrics.py",
                "tests/test_ranking.py",
            ),
        ),
        "model-contracts": (
            "model-contracts",
            (
                "MODEL_CONTRACT.md",
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_model_contracts/__init__.py",
                "src/academy_model_contracts/adapters.py",
                "src/academy_model_contracts/contracts.py",
                "src/academy_model_contracts/fakes.py",
                "src/academy_model_contracts/operations.py",
                "src/academy_model_contracts/py.typed",
                "src/academy_model_contracts/support.py",
                "tests/test_contracts.py",
                "tests/test_replies.py",
                "tests/test_run.py",
            ),
        ),
        "python-practical-review": (
            "practical-review",
            (
                "README.md",
                "REVIEW_TASK.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_practical_review/__init__.py",
                "src/academy_practical_review/client.py",
                "src/academy_practical_review/contracts.py",
                "src/academy_practical_review/evidence.py",
                "src/academy_practical_review/jobs.py",
                "src/academy_practical_review/operations.py",
                "src/academy_practical_review/py.typed",
                "src/academy_practical_review/rehearsal.py",
                "src/academy_practical_review/server.py",
                "src/academy_practical_review/support.py",
                "tests/conftest.py",
                "tests/test_client.py",
                "tests/test_contracts.py",
                "tests/test_live.py",
            ),
        ),
        "python-api-depth": (
            "api-depth",
            (
                "HTTP_CONTRACT.md",
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_api_depth/__init__.py",
                "src/academy_api_depth/api.py",
                "src/academy_api_depth/contracts.py",
                "src/academy_api_depth/operations.py",
                "src/academy_api_depth/py.typed",
                "src/academy_api_depth/rehearsal.py",
                "src/academy_api_depth/support.py",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_live.py",
            ),
        ),
        "python-query-analysis": (
            "query-analysis",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_query_analysis/__init__.py",
                "src/academy_query_analysis/annotation.sql",
                "src/academy_query_analysis/contracts.py",
                "src/academy_query_analysis/history.sql",
                "src/academy_query_analysis/notes.sql",
                "src/academy_query_analysis/operations.py",
                "src/academy_query_analysis/plans.py",
                "src/academy_query_analysis/py.typed",
                "src/academy_query_analysis/range.sql",
                "src/academy_query_analysis/rehearsal.py",
                "src/academy_query_analysis/search.sql",
                "src/academy_query_analysis/summary.sql",
                "src/academy_query_analysis/support.py",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_live.py",
            ),
        ),
        "python-delivery-release": (
            "delivery-release",
            (
                "README.md",
                "RUNBOOK.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_delivery_release/__init__.py",
                "src/academy_delivery_release/contracts.py",
                "src/academy_delivery_release/operate.py",
                "src/academy_delivery_release/operations.py",
                "src/academy_delivery_release/py.typed",
                "src/academy_delivery_release/rehearsal.py",
                "src/academy_delivery_release/support.py",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_live.py",
            ),
        ),
        "python-delivery-recovery": (
            "delivery-recovery",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_delivery_recovery/__init__.py",
                "src/academy_delivery_recovery/contracts.py",
                "src/academy_delivery_recovery/operations.py",
                "src/academy_delivery_recovery/support.py",
                "src/academy_delivery_recovery/prune.lua",
                "src/academy_delivery_recovery/py.typed",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_live.py",
            ),
        ),
        "python-delivery-schema": (
            "delivery-schema",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_delivery_schema/__init__.py",
                "src/academy_delivery_schema/metadata.py",
                "src/academy_delivery_schema/migrations/env.py",
                "src/academy_delivery_schema/migrations/versions/001_initial.py",
                "src/academy_delivery_schema/migrations/versions/002_observed_at.py",
                "src/academy_delivery_schema/migrations/versions/003_outbox.py",
                "src/academy_delivery_schema/migrations/versions/004_worker.py",
                "src/academy_delivery_schema/operations.py",
                "src/academy_delivery_schema/py.typed",
                "src/academy_delivery_schema/support.py",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_live.py",
            ),
        ),
        "python-stream-delivery": (
            "stream-delivery",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_stream_delivery/__init__.py",
                "src/academy_stream_delivery/contracts.py",
                "src/academy_stream_delivery/delivery.py",
                "src/academy_stream_delivery/envelope.py",
                "src/academy_stream_delivery/evidence.py",
                "src/academy_stream_delivery/py.typed",
                "src/academy_stream_delivery/transport.py",
                "tests/conftest.py",
                "tests/test_delivery.py",
                "tests/test_envelope.py",
                "tests/test_live.py",
                "worker_process.py",
            ),
        ),
        "python-leased-worker": (
            "leased-worker",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_leased_worker/__init__.py",
                "src/academy_leased_worker/contracts.py",
                "src/academy_leased_worker/core.py",
                "src/academy_leased_worker/evidence.py",
                "src/academy_leased_worker/py.typed",
                "src/academy_leased_worker/schema.py",
                "src/academy_leased_worker/schema.sql",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_postgres.py",
                "worker_process.py",
            ),
        ),
        "python-durable-outbox": (
            "durable-outbox",
            (
                "README.md",
                "crash_worker.py",
                "demo.py",
                "pyproject.toml",
                "src/academy_durable_outbox/__init__.py",
                "src/academy_durable_outbox/contracts.py",
                "src/academy_durable_outbox/core.py",
                "src/academy_durable_outbox/evidence.py",
                "src/academy_durable_outbox/py.typed",
                "src/academy_durable_outbox/schema.py",
                "src/academy_durable_outbox/schema.sql",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_postgres.py",
            ),
        ),
        "python-competing-ingestion": (
            "competing-ingestion",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_competing_ingestion/__init__.py",
                "src/academy_competing_ingestion/contracts.py",
                "src/academy_competing_ingestion/experiments.py",
                "src/academy_competing_ingestion/py.typed",
                "src/academy_competing_ingestion/reconcile.py",
                "src/academy_competing_ingestion/retry.py",
                "tests/conftest.py",
                "tests/test_postgres.py",
                "tests/test_reconcile.py",
                "tests/test_retry.py",
            ),
        ),
        "python-ingestion-service": (
            "ingestion-service",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "serve.py",
                "src/academy_ingestion_service/__init__.py",
                "src/academy_ingestion_service/api.py",
                "src/academy_ingestion_service/auth.py",
                "src/academy_ingestion_service/contracts.py",
                "src/academy_ingestion_service/database.py",
                "src/academy_ingestion_service/migrations/env.py",
                "src/academy_ingestion_service/migrations/versions/001_initial.py",
                "src/academy_ingestion_service/migrations/versions/002_observed_at.py",
                "src/academy_ingestion_service/models.py",
                "src/academy_ingestion_service/py.typed",
                "src/academy_ingestion_service/service.py",
                "tests/conftest.py",
                "tests/test_api.py",
                "tests/test_contracts.py",
                "tests/test_migrations.py",
            ),
        ),
        "python-ingestion-persistence": (
            "ingestion-persistence",
            (
                "README.md",
                "demo.py",
                "pyproject.toml",
                "src/academy_ingestion_persistence/__init__.py",
                "src/academy_ingestion_persistence/contracts.py",
                "src/academy_ingestion_persistence/py.typed",
                "src/academy_ingestion_persistence/schema.sql",
                "src/academy_ingestion_persistence/store.py",
                "tests/conftest.py",
                "tests/test_contracts.py",
                "tests/test_postgres.py",
            ),
        ),
        "python-measured-cache": (
            "measured-cache",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "src/academy_measured_cache/__init__.py",
                "src/academy_measured_cache/contracts.py",
                "src/academy_measured_cache/measurement.py",
                "src/academy_measured_cache/cache.py",
                "src/academy_measured_cache/py.typed",
                "tests/test_measurement.py",
                "tests/test_cache.py",
            ),
        ),
        "python-bounded-offload": (
            "bounded-offload",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "src/academy_bounded_offload/__init__.py",
                "src/academy_bounded_offload/contracts.py",
                "src/academy_bounded_offload/offload.py",
                "src/academy_bounded_offload/py.typed",
                "tests/test_collector.py",
                "tests/test_workers.py",
            ),
        ),
        "python-resource-scopes": (
            "resource-scopes",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "src/academy_resource_scopes/__init__.py",
                "src/academy_resource_scopes/contracts.py",
                "src/academy_resource_scopes/scopes.py",
                "src/academy_resource_scopes/py.typed",
                "tests/test_scopes.py",
            ),
        ),
        "python-typed-transforms": (
            "typed-transforms",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "check_types.py",
                "src/academy_typed_transforms/__init__.py",
                "src/academy_typed_transforms/contracts.py",
                "src/academy_typed_transforms/transform.py",
                "src/academy_typed_transforms/py.typed",
                "tests/test_transform.py",
                "typing/positive.py",
                "typing/negative.json",
            ),
        ),
        "python-feed-objects": (
            "feed-objects",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "src/academy_feed_objects/__init__.py",
                "src/academy_feed_objects/objects.py",
                "src/academy_feed_objects/py.typed",
                "tests/test_objects.py",
            ),
        ),
        "python-async-feeds": (
            "async-feeds",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "src/academy_async_feeds/__init__.py",
                "src/academy_async_feeds/models.py",
                "src/academy_async_feeds/parser.py",
                "src/academy_async_feeds/http.py",
                "src/academy_async_feeds/worker.py",
                "src/academy_async_feeds/py.typed",
                "tests/conftest.py",
                "tests/test_feeds.py",
            ),
        ),
        "python-feed-policy": (
            "feed-policy",
            (
                "README.md",
                "pyproject.toml",
                "demo.py",
                "src/academy_feed_policy/__init__.py",
                "src/academy_feed_policy/contracts.py",
                "src/academy_feed_policy/policy.py",
                "src/academy_feed_policy/py.typed",
                "tests/conftest.py",
                "tests/test_policy.py",
            ),
        ),
        "python-ingestion-package": (
            "ingestion-package",
            (
                "README.md",
                "pyproject.toml",
                "sample.ndjson",
                "expected.json",
                "src/academy_ingest/__init__.py",
                "src/academy_ingest/__main__.py",
                "src/academy_ingest/models.py",
                "src/academy_ingest/parser.py",
                "src/academy_ingest/http.py",
                "src/academy_ingest/cli.py",
                "src/academy_ingest/defaults.json",
                "src/academy_ingest/py.typed",
                "tests/test_ingest.py",
            ),
        ),
        "python-log-stream": (
            "log-stream",
            ("README.md", "stream.py", "cli.py", "sample.ndjson", "expected.json", "tests/test_stream.py"),
        ),
        "python-expenses": (
            "expense-tracker",
            ("README.md", "expenses.py", "cli.py", "sample.csv", "expected.json", "tests/test_expenses.py"),
        ),
        "python-event-timeline": (
            "event-timeline",
            ("README.md", "events.py", "cli.py", "sample.json", "expected.json", "tests/test_events.py"),
        ),
        "python-task-inbox": (
            "task-inbox",
            (
                "README.md",
                "inbox.py",
                "demo.py",
                "typecheck_examples.py",
                "pyproject.toml",
                "tests/test_inbox.py",
            ),
        ),
    }
    if project_id not in bundles:
        raise HTTPException(404, "Project starter not found.")
    directory, files = bundles[project_id]
    root = settings.content_dir / "projects" / directory / "starter"
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name in files:
            archive.writestr(f"{directory}/{name}", (root / name).read_bytes())
    return Response(
        output.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{directory}-starter.zip"'},
    )


@router.put("/projects/{project_id}/tasks/{task_id}")
def update_project(project_id: str, task_id: str, data: Toggle, user: Learner, db: DB):
    project = next((p for p in catalog()["projects"] if p["id"] == project_id), None)
    if not project or not any(t["id"] == task_id for t in project["tasks"]):
        raise HTTPException(404, "Project milestone not found.")
    existing = db.scalar(
        select(ProjectProgress).where(
            ProjectProgress.user_id == user.id,
            ProjectProgress.project_id == project_id,
            ProjectProgress.task_id == task_id,
        )
    )
    if data.enabled and not existing:
        db.add(ProjectProgress(user_id=user.id, project_id=project_id, task_id=task_id))
    elif existing and not data.enabled:
        db.delete(existing)
    return {"completed": data.enabled}
