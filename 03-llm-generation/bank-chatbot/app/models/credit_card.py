from typing import TypedDict


class CreditCard(TypedDict):
    id: str
    customer_id: str
    card_type: str
    credit_limit_cents: int
    available_credit_cents: int
    status: str

