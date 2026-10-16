from alembic import context
from sqlalchemy.engine import Connection
from academy_ingestion_service.models import Base

connection = context.config.attributes.get("connection")
if not isinstance(connection, Connection):
    raise RuntimeError("migrations require an explicit caller-owned connection")
context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
with context.begin_transaction():
    context.run_migrations()
