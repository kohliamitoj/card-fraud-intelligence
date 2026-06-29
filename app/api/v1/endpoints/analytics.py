from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta, timezone
from app.db.mongodb import get_collection
from app.dependencies import require_auth

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard(_: dict = Depends(require_auth)):
    cases_col = get_collection("fraud_cases")
    txn_col = get_collection("transactions")

    total_cases = await cases_col.count_documents({})
    open_cases = await cases_col.count_documents({"status": "OPEN"})
    confirmed_fraud = await cases_col.count_documents({"status": "CONFIRMED_FRAUD"})
    false_positives = await cases_col.count_documents({"status": "FALSE_POSITIVE"})
    critical_cases = await cases_col.count_documents({"risk_level": "CRITICAL"})
    total_transactions = await txn_col.count_documents({})
    flagged_transactions = await txn_col.count_documents({"is_flagged": True})

    amount_pipeline = [
        {"$match": {"status": "CONFIRMED_FRAUD"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    amount_result = await cases_col.aggregate(amount_pipeline).to_list(1)
    total_fraud_amount = amount_result[0]["total"] if amount_result else 0

    detection_rate = round(confirmed_fraud / total_cases * 100, 1) if total_cases else 0
    false_positive_rate = round(false_positives / total_cases * 100, 1) if total_cases else 0
    flag_rate = round(flagged_transactions / total_transactions * 100, 2) if total_transactions else 0

    return {
        "total_transactions_scored": total_transactions,
        "total_flagged": flagged_transactions,
        "flag_rate_percent": flag_rate,
        "total_cases": total_cases,
        "open_cases": open_cases,
        "critical_cases": critical_cases,
        "confirmed_fraud_cases": confirmed_fraud,
        "false_positive_cases": false_positives,
        "detection_rate_percent": detection_rate,
        "false_positive_rate_percent": false_positive_rate,
        "total_confirmed_fraud_amount_usd": round(total_fraud_amount, 2),
    }


@router.get("/trends")
async def fraud_trends(days: int = Query(30, le=90), _: dict = Depends(require_auth)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "total_cases": {"$sum": 1},
            "confirmed_fraud": {"$sum": {"$cond": [{"$eq": ["$status", "CONFIRMED_FRAUD"]}, 1, 0]}},
            "total_amount": {"$sum": "$amount"},
        }},
        {"$sort": {"_id": 1}},
    ]
    trends = await get_collection("fraud_cases").aggregate(pipeline).to_list(length=days)
    return {"period_days": days, "daily_trends": trends}


@router.get("/by-merchant-category")
async def fraud_by_mcc(_: dict = Depends(require_auth)):
    pipeline = [
        {"$match": {"is_flagged": True}},
        {"$group": {
            "_id": "$merchant_category_code",
            "flagged_count": {"$sum": 1},
            "total_amount": {"$sum": "$amount"},
            "avg_fraud_prob": {"$avg": "$fraud_probability"},
        }},
        {"$sort": {"flagged_count": -1}},
        {"$limit": 15},
    ]
    return await get_collection("transactions").aggregate(pipeline).to_list(length=15)


@router.get("/by-channel")
async def fraud_by_channel(_: dict = Depends(require_auth)):
    pipeline = [
        {"$group": {
            "_id": "$channel",
            "total": {"$sum": 1},
            "flagged": {"$sum": {"$cond": ["$is_flagged", 1, 0]}},
            "avg_amount": {"$avg": "$amount"},
        }},
        {"$sort": {"total": -1}},
    ]
    return await get_collection("transactions").aggregate(pipeline).to_list(length=10)
