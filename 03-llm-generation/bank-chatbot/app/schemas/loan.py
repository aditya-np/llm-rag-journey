from pydantic import BaseModel


class LoanResponse(BaseModel):
    id: str
    customer_id: str
    loan_type: str
    original_amount_cents: int
    outstanding_cents: int
    monthly_payment_cents: int
    status: str


class LoanEligibilityResponse(BaseModel):
    eligible_for_demo_offer: bool
    indicative_max_amount_cents: int
    currency: str
    reason: str
    disclaimer: str

