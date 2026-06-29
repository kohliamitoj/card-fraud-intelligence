import uuid
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from app.db.mongodb import get_collection
from app.schemas.case import CaseStatusUpdate, AddNoteRequest

logger = logging.getLogger(__name__)


async def list_cases(status: str | None, risk_level: str | None, limit: int, skip: int) -> list[dict]:
    query: dict = {}
    if status:
        query["status"] = status
    if risk_level:
        query["risk_level"] = risk_level
    cursor = get_collection("fraud_cases").find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def get_case(case_id: str) -> dict:
    doc = await get_collection("fraud_cases").find_one({"case_id": case_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Case not found")
    return doc


async def update_case_status(case_id: str, update: CaseStatusUpdate, analyst: str) -> dict:
    col = get_collection("fraud_cases")
    case = await col.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    await col.update_one(
        {"case_id": case_id},
        {"$set": {"status": update.status, "updated_at": datetime.now(timezone.utc)}},
    )

    await get_collection("audit_log").insert_one({
        "event": "case_status_updated",
        "case_id": case_id,
        "from_status": case["status"],
        "to_status": update.status,
        "reason": update.reason,
        "analyst": analyst,
        "timestamp": datetime.now(timezone.utc),
    })

    logger.info("Case %s status updated to %s by %s", case_id, update.status, analyst)
    return {"message": "Status updated", "case_id": case_id, "new_status": update.status}


async def add_note(case_id: str, request: AddNoteRequest, analyst: str) -> dict:
    case = await get_collection("fraud_cases").find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    note = {
        "note_id": str(uuid.uuid4()),
        "analyst": analyst,
        "content": request.content,
        "created_at": datetime.now(timezone.utc),
    }

    await get_collection("fraud_cases").update_one(
        {"case_id": case_id},
        {"$push": {"notes": note}, "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Note added", "note_id": note["note_id"]}


async def assign_case(case_id: str, analyst: str, assigned_by: str) -> dict:
    case = await get_collection("fraud_cases").find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    await get_collection("fraud_cases").update_one(
        {"case_id": case_id},
        {"$set": {"assigned_to": analyst, "status": "UNDER_INVESTIGATION", "updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": f"Case assigned to {analyst}", "case_id": case_id}
