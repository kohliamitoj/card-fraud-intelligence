from fastapi import APIRouter
from app.db.mongodb import get_database

router = APIRouter(prefix="/admin", tags=["Admin"])

COLLECTIONS = ["transactions", "fraud_cases", "users", "audit_log"]


@router.delete("/reset-db")
async def reset_db():
    db = get_database()
    dropped = []
    for name in COLLECTIONS:
        await db[name].drop()
        dropped.append(name)
    return {"status": "ok", "dropped": dropped}
