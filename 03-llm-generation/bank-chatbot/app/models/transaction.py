from typing import TypedDict


class Transaction(TypedDict):
    id: str
    account_id: str
    description: str
    amount_cents: int
    currency: str
    posted_at: str

