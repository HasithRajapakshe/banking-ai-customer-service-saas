from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine | None:
    """Shared engine, created on first use; None when DATABASE_URL is unset."""
    global _engine
    if _engine is None and settings.database_url:
        _engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5)
    return _engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
