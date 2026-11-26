import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.security import current_customer_id
from app.db.database import get_connection
from app.schemas.card import (
    CardEligibilityResponse,
    CreditCardResponse,
    LimitIncreaseRequest,
    LimitIncreaseResponse,
)
from app.services import credit_card_service, review_service

router = APIRouter(prefix="/v1/cards", tags=["cards"])
Customer = Annotated[str, Depends(current_customer_id)]
Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("", response_model=list[CreditCardResponse])
def list_cards(connection: Connection, customer_id: Customer) -> list[dict]:
    return credit_card_service.list_cards(connection, customer_id)


@router.get("/eligibility", response_model=CardEligibilityResponse)
def get_eligibility(connection: Connection, customer_id: Customer) -> dict:
    return credit_card_service.eligibility(connection, customer_id)


@router.post("/limit-increase-requests", response_model=LimitIncreaseResponse, status_code=202)
def request_limit_increase(
    payload: LimitIncreaseRequest,
    connection: Connection,
    customer_id: Customer,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    try:
        return review_service.create_limit_increase_request(
            connection,
            customer_id,
            payload.card_id,
            payload.requested_limit_cents,
            settings.self_service_limit_increase_max * 100,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

