import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db.database import get_connection
from app.services import faq_service

router = APIRouter(prefix="/v1/faqs", tags=["FAQs"])


@router.get("")
def search_faqs(
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> list[dict]:
    return faq_service.search(connection, q)

