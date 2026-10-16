from alembic import command
from sqlalchemy import Connection, Engine
from .support import HEAD, NotReady, current, migration, target


def upgrade(engine: Engine, revision: str = "head") -> None:
    target(revision)
    with migration(engine) as cfg:
        command.upgrade(cfg, revision)


def downgrade(engine: Engine, revision: str, *, allow_loss: bool = False) -> None:
    target(revision, backwards=True)
    if type(allow_loss) is not bool or allow_loss is not True:
        raise ValueError("delivery rollback discards history; explicitly pass allow_loss=True")
    with migration(engine) as cfg:
        command.downgrade(cfg, revision)


def check(engine: Engine) -> None:
    with migration(engine) as cfg:
        connection = cfg.attributes["connection"]
        if not isinstance(connection, Connection):
            raise TypeError("missing owned migration connection")
        if current(connection).revisions != (HEAD,):
            raise NotReady("combined delivery schema is not at its expected head")
        command.check(cfg)
