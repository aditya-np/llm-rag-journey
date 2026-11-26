import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import not_found


def create_limit_increase_request(
    connection: sqlite3.Connection,
    customer_id: str,
    card_id: str,
    requested_limit_cents: int,
    self_service_max_cents: int,
) -> dict:
    card = connection.execute(
        "SELECT * FROM cards WHERE id = ? AND customer_id = ?", (card_id, customer_id)
    ).fetchone()
    if card is None or card["status"] != "active":
        # Same response for foreign, missing, and inactive cards.
        raise not_found("Active card not found")
    if requested_limit_cents <= card["credit_limit_cents"]:
        raise ValueError("Requested limit must be higher than the current limit")

    increase_cents = requested_limit_cents - card["credit_limit_cents"]
    requires_human = increase_cents > self_service_max_cents
    status = "pending_human_review" if requires_human else "submitted_for_review"
    message = (
        "A bank representative will call you to review this request."
        if requires_human
        else "Your request was submitted for review. No limit change has been made."
    )
    request_id = f"LIR-{uuid4().hex[:12].upper()}"
    created_at = datetime.now(UTC)
    try:
        connection.execute(
            """INSERT INTO limit_increase_requests
            (id, customer_id, card_id, requested_limit_cents, current_limit_cents,
             status, requires_human_follow_up, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (request_id, customer_id, card_id, requested_limit_cents,
             card["credit_limit_cents"], status, int(requires_human), created_at.isoformat()),
        )
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise

    return {
        "request_id": request_id,
        "status": status,
        "requested_limit_cents": requested_limit_cents,
        "current_limit_cents": card["credit_limit_cents"],
        "requires_human_follow_up": requires_human,
        "message": message,
        "created_at": created_at,
    }
