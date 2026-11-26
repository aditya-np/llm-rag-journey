from typing import TypedDict


class RecurringPayment(TypedDict):
    id: str
    customer_id: str
    payee: str
    amount_cents: int
    currency: str
    cadence: str
    next_payment_date: str
    status: str

