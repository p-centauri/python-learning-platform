"""Snapshot assessment definitions and preserve original pilot attempts.

Revision ID: b92a4d781f10
Revises: 4a722da17582
"""

import json
from alembic import op
import sqlalchemy as sa

revision = "b92a4d781f10"
down_revision = "4a722da17582"
branch_labels = None
depends_on = None

# Frozen here: migrations must never read a later, edited content bank.
LEGACY_EXAM = json.loads(
    '{"id": "knowledge-pilot-v1", "title": "Engineering foundations · diagnostic", "description": "A 10-question diagnostic across backend and applied AI. This pilot establishes a baseline; it is not the full comprehensive exam or a certification. Answers stay hidden until submission.", "minutes": 20, "questions": [{"id": "exam-python", "skill": "Python", "prompt": "A frozen dataclass has a field `tags: list[str]`. Which operation can still succeed?", "options": ["Assigning a different list to tags", "Appending to the list held by tags", "Deleting the field", "Changing the class to a tuple"], "answer": 1, "explanation": "Frozen dataclasses restrict field assignment, not mutation of objects referenced by fields."}, {"id": "exam-pg", "skill": "PostgreSQL", "prompt": "Two money-transfer transactions lock accounts in opposite order and deadlock. What is the correct recovery unit?", "options": ["Only the last UPDATE", "The entire aborted transaction, with bounded retry", "The whole PostgreSQL server", "The committed transaction in a different session"], "answer": 1, "explanation": "Retry the entire aborted transaction and use consistent lock order to reduce deadlocks."}, {"id": "exam-http", "skill": "HTTP", "prompt": "Three service layers each allow three total attempts. What worst-case number of downstream attempts can one top-level request trigger?", "options": ["3", "6", "9", "27"], "answer": 3, "explanation": "Independent retries multiply: 3 × 3 × 3 = 27. Assign a coordinated retry budget."}, {"id": "exam-dist", "skill": "Distributed systems", "prompt": "An entity projection receives version 12 then version 11, with different event IDs. Deduplication by event ID alone does what?", "options": ["Prevents stale version overwrite", "Guarantees global order", "Allows both; projection version checks are still needed", "Rejects all new events"], "answer": 2, "explanation": "Event deduplication and ordering are different properties. Use aggregate versions where stale updates are unsafe."}, {"id": "exam-llm", "skill": "LLM fundamentals", "prompt": "A legal assistant must answer about a policy published yesterday. Which capability most directly addresses freshness?", "options": ["Fine-tuning once six months ago", "Retrieving the current authorized policy version", "Increasing output token limit", "Suppressing all uncertainty language"], "answer": 1, "explanation": "A current authorized knowledge source addresses freshness. Fine-tuning alone does not ensure access to new policies."}, {"id": "exam-rag", "skill": "RAG", "prompt": "Every citation points to a real document, but several claims are unsupported by those documents. What check is missing?", "options": ["URL existence only", "Claim-to-evidence support verification", "A larger logo", "More unrelated context"], "answer": 1, "explanation": "Valid source identifiers do not establish support. Verify the cited evidence supports each material claim."}, {"id": "exam-tools", "skill": "Tool calling", "prompt": "A user approves transferring 100 units to account A. The proposed tool call later changes the recipient to B. What should happen?", "options": ["Reuse the old approval", "Require validation and approval of the changed action", "Ignore recipient differences", "Let the model infer consent"], "answer": 1, "explanation": "Approval must bind to the concrete action and parameters. Changed recipient requires new authorization/approval."}, {"id": "exam-eval", "skill": "AI evaluation", "prompt": "A release improves English queries but doubles errors on Uzbek queries. The combined average barely changes. Which reporting practice reveals the issue?", "options": ["Only overall mean", "Segment metrics by language with case counts and failures", "Only total token count", "A single model fluency score"], "answer": 1, "explanation": "Segmented metrics reveal subgroup regressions hidden by aggregate scores, especially for smaller populations."}, {"id": "exam-security", "skill": "AI security", "prompt": "A citation endpoint accepts a document ID and returns the file without checking the current user. Retrieval itself was permission-filtered. Is that enough?", "options": ["Yes, document IDs are authorization", "No, downloads must enforce current authorization too", "Yes, citations imply access", "Only if the file is a PDF"], "answer": 1, "explanation": "Every data access boundary needs authorization. IDs or earlier retrieval checks are not durable access grants."}, {"id": "exam-prod", "skill": "Production", "prompt": "A queue worker depends on a shutdown callback to persist its only copy of unfinished work. What failure breaks that design?", "options": ["A force-kill before the callback completes", "A normal cache hit", "A successful health check", "An indexed SQL query"], "answer": 0, "explanation": "Forced termination may skip or interrupt cleanup. Persist important intent before execution and make unfinished work recoverable."}], "version": "2026.09-foundation-v1"}'
)


def upgrade():
    op.add_column("exam_attempts", sa.Column("definition_snapshot", sa.JSON(), nullable=True))
    attempts = sa.table(
        "exam_attempts", sa.column("exam_id", sa.String()), sa.column("definition_snapshot", sa.JSON())
    )
    op.get_bind().execute(
        attempts.update()
        .where(attempts.c.exam_id == LEGACY_EXAM["id"])
        .values(definition_snapshot=LEGACY_EXAM)
    )


def downgrade():
    with op.batch_alter_table("exam_attempts") as batch:
        batch.drop_column("definition_snapshot")
