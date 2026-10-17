"""The Alembic migrations are the schema source of truth; every service's ORM
must agree with them.

Requires a disposable PostgreSQL + pgvector database in DATABASE_URL: the test
downgrades it to base and upgrades it to head.
Run from the repository root:  python -m pytest database/tests
"""

import asyncio
import importlib
import os
import pkgutil
import subprocess
import sys
from pathlib import Path

import pgvector.sqlalchemy  # noqa: F401  (registers the vector type for reflection)
import pytest
from sqlalchemy import MetaData, inspect
from sqlalchemy.ext.asyncio import create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must point at a disposable PostgreSQL + pgvector database")

# service directory -> ORM package whose modules define the mapped tables
SERVICES = {
    "api-gateway": "app.models",
    "rag": "app.models",
    "synthetic-bank": "app.models",
}


def _alembic(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=REPO_ROOT,
        check=True,
        env={**os.environ, "DATABASE_URL": DATABASE_URL},
    )


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


def load_service_metadata(service: str) -> MetaData:
    """Import a service's models in isolation (every service's package is named `app`)."""
    _purge_app_modules()
    service_dir = str(REPO_ROOT / service)
    sys.path.insert(0, service_dir)
    try:
        package = importlib.import_module(SERVICES[service])
        if hasattr(package, "__path__"):
            for module in pkgutil.iter_modules(package.__path__):
                importlib.import_module(f"{package.__name__}.{module.name}")
        bases = {
            obj
            for module in list(sys.modules.values())
            if module and getattr(module, "__name__", "").startswith("app.models")
            for obj in vars(module).values()
            if isinstance(obj, type) and hasattr(obj, "metadata") and hasattr(obj, "registry")
        }
        assert len({id(b.metadata) for b in bases}) == 1, f"{service}: expected one declarative Base"
        return next(iter(bases)).metadata
    finally:
        sys.path.remove(service_dir)
        _purge_app_modules()


def _type_family(sql_type) -> str:
    try:
        return sql_type.python_type.__name__
    except NotImplementedError:
        return type(sql_type).__name__.lower()


@pytest.fixture(scope="module")
def db_schema() -> dict[str, dict[str, dict]]:
    """Migrate a clean database to head and reflect it."""
    _alembic("downgrade", "base")
    _alembic("upgrade", "head")

    async def reflect():
        engine = create_async_engine(DATABASE_URL)
        try:
            async with engine.connect() as conn:
                def collect(sync_conn):
                    insp = inspect(sync_conn)
                    schema = {}
                    for table in insp.get_table_names():
                        pk = set(insp.get_pk_constraint(table)["constrained_columns"])
                        schema[table] = {
                            col["name"]: {**col, "primary_key": col["name"] in pk}
                            for col in insp.get_columns(table)
                        }
                    return schema

                return await conn.run_sync(collect)
        finally:
            await engine.dispose()

    return asyncio.run(reflect())


def test_migrations_round_trip(db_schema):
    # db_schema already ran downgrade base -> upgrade head on this database.
    assert "alembic_version" in db_schema
    assert {"tenant", "app_user", "document_chunk"} <= db_schema.keys()


@pytest.mark.parametrize("service", sorted(SERVICES))
def test_orm_matches_migrated_schema(service, db_schema):
    metadata = load_service_metadata(service)
    problems = []

    for table in metadata.sorted_tables:
        db_columns = db_schema.get(table.name)
        if db_columns is None:
            problems.append(f"table {table.name}: missing from migrated schema")
            continue

        for column in table.columns:
            db_col = db_columns.get(column.name)
            where = f"{table.name}.{column.name}"
            if db_col is None:
                problems.append(f"{where}: mapped by ORM but not in schema")
                continue
            if column.primary_key != db_col["primary_key"]:
                problems.append(f"{where}: primary_key ORM={column.primary_key} DB={db_col['primary_key']}")
            if not column.primary_key and column.nullable != db_col["nullable"]:
                problems.append(f"{where}: nullable ORM={column.nullable} DB={db_col['nullable']}")
            orm_family, db_family = _type_family(column.type), _type_family(db_col["type"])
            if orm_family != db_family:
                problems.append(f"{where}: type ORM={orm_family} DB={db_family}")

        # NOT NULL columns the ORM does not map must have a DB default,
        # otherwise every INSERT from this service fails.
        for name, db_col in db_columns.items():
            if name not in table.columns and not db_col["nullable"] and db_col["default"] is None:
                problems.append(f"{table.name}.{name}: NOT NULL without default and not mapped by ORM")

    assert not problems, f"{service} ORM drift:\n  " + "\n  ".join(problems)
