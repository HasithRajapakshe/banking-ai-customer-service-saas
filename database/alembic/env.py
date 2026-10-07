import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Setup paths for microservices
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
bank_dir = os.path.join(root_dir, 'synthetic-bank')
api_gateway_dir = os.path.join(root_dir, 'api-gateway')

# Import Bank Models
sys.path.insert(0, bank_dir)
from app.models.base import Base as BankBase
import app.models.tenant
import app.models.customer
import app.models.account
import app.models.account_transaction
import app.models.card
import app.models.card_transaction
import app.models.loan
import app.models.loan_payment
import app.models.beneficiary
import app.models.payment
import app.models.complaint
sys.path.pop(0)

# Import API Gateway Models
sys.path.insert(0, api_gateway_dir)
from app.models import Base as APIGatewayBase
sys.path.pop(0)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata
target_metadata = [BankBase.metadata, APIGatewayBase.metadata]

# Database URL
database_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://banking_app:change_me_in_production@localhost:5432/banking_ai")
config.set_main_option("sqlalchemy.url", database_url)

def run_migrations_offline() -> None:
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
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
