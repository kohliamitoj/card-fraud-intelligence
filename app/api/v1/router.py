from fastapi import APIRouter
from app.api.v1.endpoints import auth, transactions, cases, investigation, analytics

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(transactions.router)
router.include_router(cases.router)
router.include_router(investigation.router)
router.include_router(analytics.router)
