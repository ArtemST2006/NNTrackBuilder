import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- 1. НАСТРОЙКА ПУТЕЙ (чтобы видеть src) ---
import sys
import os

# Выходим из migrations/env.py -> migrations -> User-service
current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_path)
# ---------------------------------------------

# --- 2. ИМПОРТ МОДЕЛЕЙ И КОНФИГА ---
from src.database import Base, DATABASE_URL
from src.models.tables import User  # Импортируй сюда свои модели, чтобы Alembic их увидел

# -----------------------------------

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- 3. ПОДМЕНА URL НА НАШ ИЗ КОНФИГА ---
config.set_main_option("sqlalchemy.url", DATABASE_URL)
# ----------------------------------------

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata нужен для --autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Вспомогательная функция для запуска в синхронном контексте"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    # Создаем асинхронный движок, используя конфиг алемибка (куда мы уже подсунули URL)
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Запускаем Event Loop для асинхронной работы
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()