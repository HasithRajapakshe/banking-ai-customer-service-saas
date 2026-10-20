from app.api.routes.accounts import router as accounts_router
from app.api.routes.beneficiaries import router as beneficiaries_router
from app.api.routes.cards import router as cards_router
from app.api.routes.complaints import router as complaints_router
from app.api.routes.customers import router as customers_router
from app.api.routes.loans import router as loans_router
from app.api.routes.payments import router as payments_router


__all__ = [
    "accounts_router",
    "beneficiaries_router",
    "cards_router",
    "complaints_router",
    "customers_router",
    "loans_router",
    "payments_router",
]