import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import current_customer_id
from app.db.database import get_connection
from app.schemas.account import AccountResponse, TransactionResponse
from app.services import account_service

router = APIRouter(prefix="/v1/accounts", tags=["accounts"])
Customer = Annotated[str, Depends(current_customer_id)]
Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("", response_model=list[AccountResponse])
def list_accounts(connection: Connection, customer_id: Customer) -> list[dict]:
    return account_service.list_accounts(connection, customer_id)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, connection: Connection, customer_id: Customer) -> dict:
    return account_service.get_account(connection, customer_id, account_id)


@router.get("/{account_id}/transactions", response_model=list[TransactionResponse])
def list_transactions(account_id: str, connection: Connection, customer_id: Customer) -> list[dict]:
    return account_service.list_transactions(connection, customer_id, account_id)

