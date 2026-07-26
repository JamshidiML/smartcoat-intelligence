from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context
from smartcoat.storage.database import (
    knowledge_audit_models,
    knowledge_v2_models,
    models,
)
from smartcoat.storage.database.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_ = (models, knowledge_v2_models, knowledge_audit_models)
target_metadata = Base.metadata


def _target_schema() -> str:
    schema = os.getenv("SMARTCOAT_ALEMBIC_SCHEMA", "public").strip()
    if not schema or "\x00" in schema:
        raise RuntimeError("SMARTCOAT_ALEMBIC_SCHEMA must be a non-empty schema name")
    return schema


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=_target_schema(),
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    schema = _target_schema()
    with connectable.connect() as connection:
        quoted_schema = connection.dialect.identifier_preparer.quote_schema(schema)
        connection.execute(text(f"SET search_path TO {quoted_schema}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema,
            compare_type=True,
            compare_server_default=True,
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
