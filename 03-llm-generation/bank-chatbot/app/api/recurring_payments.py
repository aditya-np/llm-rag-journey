import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import current_customer_id
from app.db.database import get_connection
from app.schemas.payment import RecurringPaymentResponse
from app.services import payment_service

router = APIRouter(prefix="/v1/recurring-payments", tags=["recurring payments"])


@router.get("", response_model=list[RecurringPaymentResponse])
def list_recurring_payments(
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    customer_id: Annotated[str, Depends(current_customer_id)],
) -> list[dict]:
    return payment_service.list_recurring_payments(connection, customer_id)

