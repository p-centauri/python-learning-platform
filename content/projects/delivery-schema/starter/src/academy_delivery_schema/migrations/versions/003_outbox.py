from alembic import op

revision = "delivery_003"
down_revision = "service_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        '-- Explicit one-time addition after the prior service_002 migration in a disposable schema.\nCREATE TABLE delivery_outbox (\n namespace text COLLATE "C" NOT NULL,\n id text COLLATE "C" NOT NULL,\n revision integer NOT NULL,\n value integer NOT NULL CHECK (value BETWEEN 0 AND 1000000),\n acknowledged boolean NOT NULL DEFAULT false,\n PRIMARY KEY (namespace,id,revision),\n FOREIGN KEY (namespace,id,revision) REFERENCES feed_record(namespace,id,revision)\n);\nCREATE TABLE delivery_inbox (\n namespace text COLLATE "C" NOT NULL CHECK (namespace ~ \'^[a-z][a-z0-9-]{0,31}$\'),\n id text COLLATE "C" NOT NULL CHECK (id ~ \'^[a-z][a-z0-9-]{0,31}$\'),\n revision integer NOT NULL CHECK (revision BETWEEN 1 AND 8),\n value integer NOT NULL CHECK (value BETWEEN 0 AND 1000000),\n PRIMARY KEY (namespace,id,revision)\n);\nCREATE TABLE delivery_effect (\n namespace text COLLATE "C" PRIMARY KEY CHECK (namespace ~ \'^[a-z][a-z0-9-]{0,31}$\'),\n total bigint NOT NULL CHECK (total >= 0),\n applied bigint NOT NULL CHECK (applied > 0)\n);\n'
    )


def downgrade() -> None:
    op.drop_table("delivery_effect")
    op.drop_table("delivery_inbox")
    op.drop_table("delivery_outbox")
