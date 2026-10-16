"""Pin fresh recall sessions independently from scenario mastery."""

from alembic import op
import sqlalchemy as sa

revision = "f064de537b42"
down_revision = "e953cd426a31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recall_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.String(100), nullable=False),
        sa.Column("active_key", sa.String(100), nullable=True),
        sa.Column("question_id", sa.String(150), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("definition_snapshot", sa.JSON(), nullable=False),
        sa.Column("answer", sa.String(120), nullable=False),
        sa.Column("used_help", sa.Boolean(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "active_key"),
        sa.CheckConstraint("status IN ('active', 'submitted', 'abandoned')", name="ck_recall_status"),
        sa.CheckConstraint("mode IN ('practice', 'delayed')", name="ck_recall_mode"),
    )
    op.create_index("ix_recall_sessions_user_id", "recall_sessions", ["user_id"])
    op.create_index("ix_recall_sessions_concept_id", "recall_sessions", ["concept_id"])


def downgrade():
    op.drop_table("recall_sessions")
