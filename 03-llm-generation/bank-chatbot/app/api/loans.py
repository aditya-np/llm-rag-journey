import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import current_customer_id
from app.db.database import get_connection
from app.schemas.loan import LoanEligibilityResponse, LoanResponse
from app.services import loan_service

router = APIRouter(prefix="/v1/loans", tags=["loans"])
Customer = Annotated[str, Depends(current_customer_id)]
Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("", response_model=list[LoanResponse])
def list_loans(connection: Connection, customer_id: Customer) -> list[dict]:
    return loan_service.list_loans(connection, customer_id)


@router.get("/eligibility", response_model=LoanEligibilityResponse)
def get_eligibility(connection: Connection, customer_id: Customer) -> dict:
    return loan_service.eligibility(connection, customer_id)

