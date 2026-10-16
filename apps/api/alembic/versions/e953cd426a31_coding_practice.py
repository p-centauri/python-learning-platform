"""Keep coding drafts and fixed objective execution evidence separately."""

from alembic import op
import sqlalchemy as sa

revision = "e953cd426a31"
down_revision = "d842bc315f20"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "coding_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.String(100), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "exercise_id"),
    )
    op.create_index("ix_coding_drafts_user_id", "coding_drafts", ["user_id"])
    op.create_table(
        "coding_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.String(100), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("definition_snapshot", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "request_key"),
    )
    op.create_index("ix_coding_attempts_user_id", "coding_attempts", ["user_id"])
    op.create_index("ix_coding_attempts_created_at", "coding_attempts", ["created_at"])


def downgrade():
    op.drop_table("coding_attempts")
    op.drop_table("coding_drafts")
