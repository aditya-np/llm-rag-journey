from typing import TypedDict


class Account(TypedDict):
    id: str
    customer_id: str
    account_type: str
    currency: str
    balance_cents: int

