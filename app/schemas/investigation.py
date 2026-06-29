from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InvestigationChatRequest(BaseModel):
    case_id: str
    message: str = Field(..., min_length=2)
    conversation_history: list[ChatMessage] = []


class InvestigationChatResponse(BaseModel):
    case_id: str
    answer: str
    conversation_history: list[ChatMessage]
    suggested_actions: list[str] = []


class SimilarCase(BaseModel):
    case_id: str
    transaction_id: str
    similarity_reason: str
    fraud_probability: float
    status: str
    amount: float
    created_at: datetime


class CaseSummaryResponse(BaseModel):
    case_id: str
    executive_summary: str
    key_red_flags: list[str]
    recommended_action: str
    similar_cases: list[SimilarCase] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)
