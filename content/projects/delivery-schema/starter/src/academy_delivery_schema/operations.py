from sqlalchemy import Engine


def upgrade(engine: Engine, revision: str = "head") -> None:
    """Validate target; own one guarded transaction and call Alembic upgrade."""
    raise NotImplementedError("implement explicit transactional upgrade")


def downgrade(engine: Engine, revision: str, *, allow_loss: bool = False) -> None:
    """Require exact True before opening a connection; permit only delivery rollback targets."""
    raise NotImplementedError("implement explicit destructive downgrade")


def check(engine: Engine) -> None:
    """Require the combined head, then run the bounded autogenerate drift check."""
    raise NotImplementedError("implement separate head and drift checks")
