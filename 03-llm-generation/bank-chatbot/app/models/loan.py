from typing import TypedDict


class Loan(TypedDict):
    id: str
    customer_id: str
    loan_type: str
    original_amount_cents: int
    outstanding_cents: int
    monthly_payment_cents: int
    status: str

