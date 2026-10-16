from alembic import op
import sqlalchemy as sa

revision = "service_002"
down_revision = "service_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "feed_record",
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    # Explicitly loses ingestion-time metadata; original key/value rows remain.
    op.drop_column("feed_record", "ingested_at")
