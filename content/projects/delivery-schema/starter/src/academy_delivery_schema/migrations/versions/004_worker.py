from alembic import op

revision = "delivery_004"
down_revision = "delivery_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE worker_policy (\n namespace text COLLATE \"C\" PRIMARY KEY REFERENCES feed_source(namespace),\n lease_ms integer NOT NULL CHECK (lease_ms BETWEEN 100 AND 60000),\n max_attempts integer NOT NULL CHECK (max_attempts BETWEEN 1 AND 8),\n delays_ms integer[] NOT NULL CHECK (cardinality(delays_ms) = max_attempts - 1)\n   CHECK (0 <= ALL(delays_ms) AND 60000 >= ALL(delays_ms))\n);\nCREATE TABLE delivery_job (\n namespace text COLLATE \"C\" NOT NULL REFERENCES worker_policy(namespace),\n id text COLLATE \"C\" NOT NULL,\n revision integer NOT NULL,\n generation bigint NOT NULL DEFAULT 0 CHECK (generation BETWEEN 0 AND 8),\n state text NOT NULL DEFAULT 'ready' CHECK (state IN ('ready','leased','done','dead')),\n next_at timestamptz NOT NULL DEFAULT clock_timestamp(),\n lease_until timestamptz,\n reason text CHECK (reason IN ('retry','poison','exhausted')),\n PRIMARY KEY(namespace,id,revision),\n FOREIGN KEY(namespace,id,revision) REFERENCES delivery_outbox(namespace,id,revision),\n CHECK ((state = 'leased') = (lease_until IS NOT NULL)),\n CHECK (state <> 'leased' OR generation > 0)\n);\nCREATE INDEX delivery_job_ready ON delivery_job(namespace,next_at,id,revision) WHERE state='ready';\n"
    )


def downgrade() -> None:
    op.drop_table("delivery_job")
    op.drop_table("worker_policy")
