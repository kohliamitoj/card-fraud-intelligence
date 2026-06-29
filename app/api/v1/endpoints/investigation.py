from fastapi import APIRouter, Depends
from app.schemas.investigation import InvestigationChatRequest, InvestigationChatResponse, CaseSummaryResponse
from app.services.investigation_service import chat_with_case, get_case_summary
from app.dependencies import require_auth

router = APIRouter(prefix="/investigation", tags=["Investigation"])


@router.post("/chat", response_model=InvestigationChatResponse)
async def investigation_chat(
    request: InvestigationChatRequest,
    current_user: dict = Depends(require_auth),
):
    return await chat_with_case(request, current_user["username"])


@router.get("/cases/{case_id}/summary", response_model=CaseSummaryResponse)
async def case_summary(case_id: str, _: dict = Depends(require_auth)):
    return await get_case_summary(case_id)
