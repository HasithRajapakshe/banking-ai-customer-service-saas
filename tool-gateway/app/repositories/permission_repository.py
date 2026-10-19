"""Role -> permission lookup from the role/permission tables (Alembic 0002)."""

import time

from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_engine


class PermissionRepository:
    def __init__(self):
        self._cache: dict[tuple[str, ...], tuple[float, frozenset[str]]] = {}

    async def permissions_for_roles(self, roles: tuple[str, ...]) -> frozenset[str]:
        """Permission codes granted to any of the given global roles (cached briefly)."""
        key = tuple(sorted(set(roles)))
        if not key:
            return frozenset()
        cached = self._cache.get(key)
        now = time.monotonic()
        if cached and now - cached[0] < settings.permission_cache_ttl_seconds:
            return cached[1]

        engine = get_engine()
        if engine is None:
            raise RuntimeError("DATABASE_URL is not configured; cannot resolve role permissions")
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT DISTINCT p.permission_code FROM role r "
                    "JOIN role_permission rp ON rp.role_id = r.id "
                    "JOIN permission p ON p.id = rp.permission_id "
                    "WHERE r.tenant_id IS NULL AND r.role_code = ANY(:roles)"
                ),
                {"roles": list(key)},
            )
            permissions = frozenset(row[0] for row in result.all())
        self._cache[key] = (now, permissions)
        return permissions


permission_repository = PermissionRepository()
