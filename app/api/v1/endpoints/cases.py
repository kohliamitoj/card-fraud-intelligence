from fastapi import APIRouter, Depends, Query
from app.schemas.case import CaseStatusUpdate, AddNoteRequest, CaseResponse, CaseListItem
from app.services.case_service import list_cases, get_case, update_case_status, add_note, assign_case
from app.dependencies import require_auth

router = APIRouter(prefix="/cases", tags=["Fraud Cases"])


@router.get("/", response_model=list[CaseListItem])
async def list_fraud_cases(
    status: str | None = Query(None),
    risk_level: str | None = Query(None),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    _: dict = Depends(require_auth),
):
    return await list_cases(status, risk_level, limit, skip)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_fraud_case(case_id: str, _: dict = Depends(require_auth)):
    return await get_case(case_id)


@router.patch("/{case_id}/status")
async def update_status(
    case_id: str,
    update: CaseStatusUpdate,
    current_user: dict = Depends(require_auth),
):
    return await update_case_status(case_id, update, current_user["username"])


@router.post("/{case_id}/notes", status_code=201)
async def add_investigation_note(
    case_id: str,
    request: AddNoteRequest,
    current_user: dict = Depends(require_auth),
):
    return await add_note(case_id, request, current_user["username"])


@router.patch("/{case_id}/assign")
async def assign_to_analyst(
    case_id: str,
    analyst: str = Query(...),
    current_user: dict = Depends(require_auth),
):
    return await assign_case(case_id, analyst, current_user["username"])
