from datetime import datetime

from pydantic import BaseModel, Field


class CreditCardResponse(BaseModel):
    id: str
    customer_id: str
    card_type: str
    credit_limit_cents: int
    available_credit_cents: int
    status: str


class CardEligibilityResponse(BaseModel):
    eligible_for_demo_offer: bool
    reason: str
    disclaimer: str


class LimitIncreaseRequest(BaseModel):
    card_id: str = Field(min_length=1, max_length=40)
    requested_limit_cents: int = Field(gt=0, le=100_000_000)


class LimitIncreaseResponse(BaseModel):
    request_id: str
    status: str
    requested_limit_cents: int
    current_limit_cents: int
    requires_human_follow_up: bool
    message: str
    created_at: datetime

