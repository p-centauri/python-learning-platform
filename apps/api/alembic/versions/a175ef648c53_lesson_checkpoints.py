"""Keep guided checkpoint history separate from mastery and recall."""

from alembic import op
import sqlalchemy as sa

revision = "a175ef648c53"
down_revision = "f064de537b42"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lesson_checkpoint_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(100), nullable=False),
        sa.Column("checkpoint_id", sa.String(150), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False),
        sa.Column("answer", sa.Integer(), nullable=False),
        sa.Column("definition_snapshot", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "request_key"),
    )
    for column in ("user_id", "lesson_id", "created_at"):
        op.create_index(f"ix_lesson_checkpoint_attempts_{column}", "lesson_checkpoint_attempts", [column])


def downgrade():
    op.drop_table("lesson_checkpoint_attempts")
