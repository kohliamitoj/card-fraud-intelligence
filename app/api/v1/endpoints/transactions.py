from fastapi import APIRouter, Depends, Query
from app.schemas.transaction import TransactionRequest, TransactionScoreResponse
from app.services.transaction_service import score_and_store_transaction, get_transaction, list_transactions
from app.dependencies import require_auth

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/score", response_model=TransactionScoreResponse)
async def score_transaction(
    txn: TransactionRequest,
    _: dict = Depends(require_auth),
):
    return await score_and_store_transaction(txn)


@router.get("/{transaction_id}")
async def get_txn(transaction_id: str, _: dict = Depends(require_auth)):
    return await get_transaction(transaction_id)


@router.get("/")
async def list_txns(
    cardholder_id: str | None = Query(None),
    flagged_only: bool = Query(False),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    _: dict = Depends(require_auth),
):
    return await list_transactions(cardholder_id, flagged_only, limit, skip)
