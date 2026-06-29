import uuid
import logging
from datetime import datetime, timedelta, timezone
from app.db.mongodb import get_collection
from app.schemas.transaction import TransactionRequest, TransactionScoreResponse, TransactionRecord
from app.core.feature_builder import build_features
from app.core.fraud_detector import score_transaction, risk_level_from_prob
from app.core.ai_assistant import generate_fraud_explanation
from config.settings import settings

logger = logging.getLogger(__name__)


async def score_and_store_transaction(txn: TransactionRequest) -> TransactionScoreResponse:
    txn_col = get_collection("transactions")
    cases_col = get_collection("fraud_cases")

    history = await _fetch_cardholder_history(txn.cardholder_id, txn.timestamp)
    cardholder_stats = await _compute_cardholder_stats(txn.cardholder_id)

    txn_dict = txn.model_dump()
    features = build_features(txn_dict, history, cardholder_stats)

    fraud_prob, risk_factors = score_transaction(features)
    risk_level = risk_level_from_prob(fraud_prob)
    is_flagged = fraud_prob >= settings.FRAUD_THRESHOLD

    explanation = generate_fraud_explanation(txn_dict, features, risk_factors, fraud_prob)

    case_id = None
    if is_flagged:
        case_id = str(uuid.uuid4())
        case_doc = {
            "case_id": case_id,
            "transaction_id": txn.transaction_id,
            "cardholder_id": txn.cardholder_id,
            "amount": txn.amount,
            "currency": txn.currency,
            "merchant_name": txn.merchant_name,
            "merchant_category_code": txn.merchant_category_code,
            "fraud_probability": fraud_prob,
            "risk_level": risk_level,
            "fraud_explanation": explanation,
            "top_risk_factors": risk_factors,
            "status": "OPEN",
            "assigned_to": None,
            "notes": [],
            "ai_summary": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await cases_col.insert_one(case_doc)
        logger.info("Fraud case %s created for transaction %s (prob=%.2f)", case_id, txn.transaction_id, fraud_prob)

    record = TransactionRecord(
        **txn_dict,
        fraud_probability=fraud_prob,
        is_flagged=is_flagged,
        risk_level=risk_level,
        fraud_explanation=explanation,
        top_risk_factors=risk_factors,
        case_id=case_id,
    )
    await txn_col.insert_one(record.model_dump())

    return TransactionScoreResponse(
        transaction_id=txn.transaction_id,
        fraud_probability=fraud_prob,
        is_flagged=is_flagged,
        risk_level=risk_level,
        fraud_explanation=explanation,
        top_risk_factors=risk_factors,
        case_id=case_id,
    )


async def get_transaction(transaction_id: str) -> dict:
    doc = await get_collection("transactions").find_one({"transaction_id": transaction_id}, {"_id": 0})
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transaction not found")
    return doc


async def list_transactions(cardholder_id: str | None, flagged_only: bool, limit: int, skip: int) -> list[dict]:
    query: dict = {}
    if cardholder_id:
        query["cardholder_id"] = cardholder_id
    if flagged_only:
        query["is_flagged"] = True
    cursor = get_collection("transactions").find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def _fetch_cardholder_history(cardholder_id: str, before: datetime) -> list[dict]:
    if before.tzinfo is None:
        before = before.replace(tzinfo=timezone.utc)
    cutoff = before - timedelta(days=30)
    cursor = get_collection("transactions").find(
        {"cardholder_id": cardholder_id, "timestamp": {"$gte": cutoff, "$lt": before}},
        {"_id": 0, "amount": 1, "timestamp": 1, "merchant_id": 1, "location_country": 1, "latitude": 1, "longitude": 1},
    ).sort("timestamp", -1).limit(200)
    return await cursor.to_list(length=200)


async def _compute_cardholder_stats(cardholder_id: str) -> dict:
    pipeline = [
        {"$match": {"cardholder_id": cardholder_id}},
        {"$group": {"_id": None, "avg_amount": {"$avg": "$amount"}, "std_amount": {"$stdDevSamp": "$amount"}}},
    ]
    result = await get_collection("transactions").aggregate(pipeline).to_list(length=1)
    return result[0] if result else {"avg_amount": 0, "std_amount": 1}
