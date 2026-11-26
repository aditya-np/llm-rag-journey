import sqlite3


def list_cards(connection: sqlite3.Connection, customer_id: str) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM cards WHERE customer_id = ? ORDER BY id", (customer_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def eligibility(connection: sqlite3.Connection, customer_id: str) -> dict:
    active = connection.execute(
        "SELECT 1 FROM cards WHERE customer_id = ? AND status = 'active' LIMIT 1",
        (customer_id,),
    ).fetchone() is not None
    return {
        "eligible_for_demo_offer": not active,
        "reason": "A demo card is already active." if active else "No active card is recorded in this demo profile.",
        "disclaimer": "Demo rule only; a real application is subject to bank checks.",
    }


