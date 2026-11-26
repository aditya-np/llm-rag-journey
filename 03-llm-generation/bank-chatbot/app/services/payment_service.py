import sqlite3


def list_recurring_payments(connection: sqlite3.Connection, customer_id: str) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM recurring_payments WHERE customer_id = ? ORDER BY next_payment_date",
        (customer_id,),
    ).fetchall()
    return [dict(row) for row in rows]

