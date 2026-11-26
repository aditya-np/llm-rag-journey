import sqlite3

from app.core.exceptions import not_found


def require_owned_record(
    connection: sqlite3.Connection,
    table: str,
    record_id: str,
    customer_id: str,
) -> sqlite3.Row:
    # Restrict identifiers to known tables; values remain SQL parameters.
    if table not in {"accounts", "loans", "cards", "recurring_payments"}:
        raise ValueError("Unsupported customer-owned resource")
    row = connection.execute(
        f"SELECT * FROM {table} WHERE id = ? AND customer_id = ?",
        (record_id, customer_id),
    ).fetchone()
    if row is None:
        raise not_found("Record not found")
    return row

