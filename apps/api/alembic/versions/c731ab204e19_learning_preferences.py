"""Save account-scoped learning choices without changing existing progress."""

from alembic import op
import sqlalchemy as sa

revision = "c731ab204e19"
down_revision = "b92a4d781f10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "learning_preferences",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("goal", sa.String(20), nullable=False),
        sa.Column("weekly_hours", sa.Integer(), nullable=False),
        sa.Column("starting_mode", sa.String(20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("weekly_hours BETWEEN 1 AND 20", name="ck_plan_hours"),
        sa.CheckConstraint("goal IN ('python', 'backend', 'applied-ai', 'backend-ai')", name="ck_plan_goal"),
        sa.CheckConstraint("starting_mode IN ('recommended', 'from-start')", name="ck_plan_start"),
    )


def downgrade():
    op.drop_table("learning_preferences")
