from app.api.routes.customers import router as customers_router
from app.api.routes.accounts import router as accounts_router
from app.api.routes.cards import router as cards_router


__all__ = [
    "customers_router",
    "accounts_router",
    "cards_router",
]