from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    cardholder_id: str
    card_last4: str = Field(..., min_length=4, max_length=4)
    card_type: Literal["VISA", "MASTERCARD", "AMEX", "RUPAY"]
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    merchant_id: str
    merchant_name: str
    merchant_category_code: str = Field(..., description="4-digit MCC code")
    channel: Literal["POS", "ONLINE", "ATM", "CONTACTLESS"]
    location_city: str
    location_country: str = Field(default="IN")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TransactionScoreResponse(BaseModel):
    transaction_id: str
    fraud_probability: float
    is_flagged: bool
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    fraud_explanation: str
    top_risk_factors: list[dict]
    case_id: Optional[str] = None
    scored_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionRecord(BaseModel):
    transaction_id: str
    cardholder_id: str
    card_last4: str
    card_type: str
    amount: float
    currency: str
    merchant_id: str
    merchant_name: str
    merchant_category_code: str
    channel: str
    location_city: str
    location_country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    timestamp: datetime
    fraud_probability: float
    is_flagged: bool
    risk_level: str
    fraud_explanation: str
    top_risk_factors: list[dict]
    case_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
