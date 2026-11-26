from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: str
    customer_id: str
    account_type: str
    currency: str
    balance_cents: int


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    description: str
    amount_cents: int
    currency: str
    posted_at: str

