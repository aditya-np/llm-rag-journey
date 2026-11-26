import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import current_customer_id
from app.db.database import get_connection
from app.core.exceptions import not_found

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/me")
def get_current_customer(
    customer_id: Annotated[str, Depends(current_customer_id)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> dict:
    row = connection.execute(
        "SELECT id, name, email FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise not_found("Customer not found")
    return dict(row)


@router.get("/demo-profiles")
def list_demo_profiles(
    _customer_id: Annotated[str, Depends(current_customer_id)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> list[dict[str, str]]:
    """Names/IDs for the local profile switcher only; contains no account data."""
    rows = connection.execute("SELECT id, name FROM customers ORDER BY id").fetchall()
    return [dict(row) for row in rows]

