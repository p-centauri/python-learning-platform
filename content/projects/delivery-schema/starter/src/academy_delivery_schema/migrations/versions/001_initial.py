from alembic import op
import sqlalchemy as sa

revision = "service_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feed_source",
        sa.Column("namespace", sa.Text(collation="C"), primary_key=True),
        sa.CheckConstraint("namespace ~ '^[a-z][a-z0-9-]{0,31}$'", name="source_namespace"),
    )
    op.create_table(
        "feed_record",
        sa.Column(
            "namespace", sa.Text(collation="C"), sa.ForeignKey("feed_source.namespace"), primary_key=True
        ),
        sa.Column("id", sa.Text(collation="C"), primary_key=True),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.CheckConstraint("id ~ '^[a-z][a-z0-9-]{0,31}$'", name="record_id"),
        sa.CheckConstraint("revision BETWEEN 1 AND 8", name="record_revision"),
        sa.CheckConstraint("value BETWEEN 0 AND 1000000", name="record_value"),
    )


def downgrade() -> None:
    op.drop_table("feed_record")
    op.drop_table("feed_source")
