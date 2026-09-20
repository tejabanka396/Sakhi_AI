import sys
import os
from logging.config import fileConfig
from alembic import context

# Ensure backend folder is on sys.path
sys.path.insert(0, os.path.abspath('backend'))

from app.core.config import settings
from app.database.database import Base, engine
import app.database.models  # load models for metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = str(engine.url).replace("%", "%%")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    try:
        from app.database.database import log_ssl_startup_diagnostic
        log_ssl_startup_diagnostic()
    except Exception:
        pass

    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
