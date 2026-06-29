from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


class InvestigationNote(BaseModel):
    note_id: str
    analyst: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CaseStatusUpdate(BaseModel):
    status: Literal["OPEN", "UNDER_INVESTIGATION", "CONFIRMED_FRAUD", "FALSE_POSITIVE", "CLOSED"]
    reason: str


class CaseResponse(BaseModel):
    case_id: str
    transaction_id: str
    cardholder_id: str
    amount: float
    currency: str
    merchant_name: str
    merchant_category_code: str
    fraud_probability: float
    risk_level: str
    fraud_explanation: str
    top_risk_factors: list[dict]
    status: str
    assigned_to: Optional[str] = None
    notes: list[InvestigationNote] = []
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CaseListItem(BaseModel):
    case_id: str
    transaction_id: str
    cardholder_id: str
    amount: float
    risk_level: str
    status: str
    created_at: datetime


class AddNoteRequest(BaseModel):
    content: str = Field(..., min_length=5)
