import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db

from app.core.customer_context import require_customer_context
from app.schemas.card import CardResponse
from app.schemas.card_transaction import CardTransactionResponse
from app.services.card_service import CardService
from app.services.card_transaction_service import (
    CardTransactionService,
)


router = APIRouter(
    prefix="/api/v1/cards",
    tags=["Cards"],
)

card_service = CardService()
card_transaction_service = CardTransactionService()


@router.get(
    "/{card_id}",
    response_model=CardResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_card(
    card_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    card = await card_service.get_card(
        db,
        card_id,
        tenant_id,
        customer_id,
    )

    if card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found",
        )

    return card


@router.post(
    "/{card_id}/block",
    response_model=CardResponse,
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def block_card(
    card_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    card = await card_service.block_card(
        db,
        card_id,
        tenant_id,
        customer_id,
    )

    if card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found",
        )

    return card


@router.get(
    "/{card_id}/transactions",
    response_model=list[CardTransactionResponse],
    dependencies=[
        Depends(require_customer_context),
    ],
)
async def get_card_transactions(
    card_id: uuid.UUID,
    request: Request,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = request.state.tenant_id
    customer_id = request.state.customer_id

    card = await card_service.get_card(
        db,
        card_id,
        tenant_id,
        customer_id,
    )

    if card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found",
        )

    return await card_transaction_service.get_card_transactions(
        db,
        card_id,
        tenant_id,
        limit,
        offset,
    )