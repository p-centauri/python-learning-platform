"""Store only a one-use recovery credential digest; old accounts stay unchanged."""

from alembic import op
import sqlalchemy as sa

revision = "c3970b860e75"
down_revision = "b286fa759d64"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_recovery_keys",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table("account_recovery_keys")
