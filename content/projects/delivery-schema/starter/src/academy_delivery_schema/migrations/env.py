from alembic import context
from sqlalchemy import Connection
from academy_delivery_schema.metadata import metadata

connection = context.config.attributes.get("connection")
if not isinstance(connection, Connection):
    raise RuntimeError("an explicit owned connection is required")
context.configure(
    connection=connection, target_metadata=metadata, compare_type=True, compare_server_default=True
)
with context.begin_transaction():
    context.run_migrations()
