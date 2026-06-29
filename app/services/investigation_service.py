import logging
from fastapi import HTTPException
from app.db.mongodb import get_collection
from app.core.ai_assistant import answer_investigation_query, generate_case_summary
from app.schemas.investigation import InvestigationChatRequest, CaseSummaryResponse, SimilarCase
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def chat_with_case(request: InvestigationChatRequest, analyst: str) -> dict:
    case = await get_collection("fraud_cases").find_one({"case_id": request.case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    history = [m.model_dump() for m in request.conversation_history]
    answer, suggested_actions = answer_investigation_query(case, request.message, history)

    new_history = history + [
        {"role": "analyst", "content": request.message, "timestamp": datetime.now(timezone.utc)},
        {"role": "assistant", "content": answer, "timestamp": datetime.now(timezone.utc)},
    ]

    await get_collection("audit_log").insert_one({
        "event": "investigation_query",
        "case_id": request.case_id,
        "analyst": analyst,
        "question": request.message,
        "timestamp": datetime.now(timezone.utc),
    })

    return {
        "case_id": request.case_id,
        "answer": answer,
        "conversation_history": new_history,
        "suggested_actions": suggested_actions,
    }


async def get_case_summary(case_id: str) -> CaseSummaryResponse:
    case = await get_collection("fraud_cases").find_one({"case_id": case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    similar = await _find_similar_cases(case)

    if case.get("ai_summary"):
        summary_text = case["ai_summary"]
    else:
        summary_text = generate_case_summary(case, similar)
        await get_collection("fraud_cases").update_one(
            {"case_id": case_id}, {"$set": {"ai_summary": summary_text}}
        )

    red_flags = [
        r["feature"].replace("_", " ").title()
        for r in case.get("top_risk_factors", [])
        if r.get("direction") == "increases_risk"
    ]

    prob = case.get("fraud_probability", 0)
    if prob >= 0.85:
        recommended_action = "Immediately block card and initiate fraud investigation. File STR if applicable."
    elif prob >= 0.65:
        recommended_action = "Place temporary card hold and contact cardholder for verification."
    else:
        recommended_action = "Monitor closely. Gather additional evidence before taking action."

    return CaseSummaryResponse(
        case_id=case_id,
        executive_summary=summary_text,
        key_red_flags=red_flags,
        recommended_action=recommended_action,
        similar_cases=[SimilarCase(**s) for s in similar],
    )


async def _find_similar_cases(case: dict) -> list[dict]:
    query = {
        "case_id": {"$ne": case["case_id"]},
        "$or": [
            {"merchant_category_code": case.get("merchant_category_code")},
            {"cardholder_id": case.get("cardholder_id")},
            {"risk_level": case.get("risk_level")},
        ],
        "status": {"$in": ["CONFIRMED_FRAUD", "CLOSED"]},
    }
    cursor = get_collection("fraud_cases").find(query, {"_id": 0}).limit(5)
    docs = await cursor.to_list(length=5)

    results = []
    for d in docs:
        reasons = []
        if d.get("merchant_category_code") == case.get("merchant_category_code"):
            reasons.append("same merchant category")
        if d.get("cardholder_id") == case.get("cardholder_id"):
            reasons.append("same cardholder")
        if d.get("risk_level") == case.get("risk_level"):
            reasons.append("same risk level")
        results.append({
            "case_id": d["case_id"],
            "transaction_id": d["transaction_id"],
            "similarity_reason": ", ".join(reasons),
            "fraud_probability": d.get("fraud_probability", 0),
            "status": d.get("status", ""),
            "amount": d.get("amount", 0),
            "created_at": d.get("created_at", datetime.now(timezone.utc)),
        })
    return results
