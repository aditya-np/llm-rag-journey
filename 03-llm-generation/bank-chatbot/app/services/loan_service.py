import sqlite3


def list_loans(connection: sqlite3.Connection, customer_id: str) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM loans WHERE customer_id = ? ORDER BY id", (customer_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def eligibility(connection: sqlite3.Connection, customer_id: str) -> dict:
    active = connection.execute(
        "SELECT 1 FROM loans WHERE customer_id = ? AND status = 'active' LIMIT 1",
        (customer_id,),
    ).fetchone() is not None
    return {
        "eligible_for_demo_offer": not active,
        "indicative_max_amount_cents": 500_000 if not active else 0,
        "currency": "EUR",
        "reason": "No active loan is recorded in this demo profile." if not active else "An active loan is recorded; a real offer requires a bank assessment.",
        "disclaimer": "Demo rule only; this is not a credit decision or loan offer.",
    }

