from pydantic import BaseModel


class RecurringPaymentResponse(BaseModel):
    id: str
    customer_id: str
    payee: str
    amount_cents: int
    currency: str
    cadence: str
    next_payment_date: str
    status: str

