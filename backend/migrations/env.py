from alembic import context

from backend.database import database_path, open_database


def migrate() -> None:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = open_database(path)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError('Run migrations against the local SQLite database.')

migrate()
