"""Add resumable exam state and fixed isolated-run evidence without changing history."""

from alembic import op
import sqlalchemy as sa

revision = "b286fa759d64"
down_revision = "a175ef648c53"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("exam_attempts", sa.Column("workspace", sa.JSON(), nullable=False, server_default="{}"))
    op.create_table(
        "exam_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("exam_attempts.id"), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("definition_snapshot", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "request_key"),
    )
    for col in ("user_id", "attempt_id", "created_at"):
        op.create_index(f"ix_exam_runs_{col}", "exam_runs", [col])


def downgrade():
    op.drop_table("exam_runs")
    op.drop_column("exam_attempts", "workspace")
