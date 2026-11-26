import sqlite3

from app.core.permissions import require_owned_record


def list_accounts(connection: sqlite3.Connection, customer_id: str) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM accounts WHERE customer_id = ? ORDER BY id", (customer_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def get_account(connection: sqlite3.Connection, customer_id: str, account_id: str) -> dict:
    return dict(require_owned_record(connection, "accounts", account_id, customer_id))


def list_transactions(
    connection: sqlite3.Connection, customer_id: str, account_id: str
) -> list[dict]:
    # Join to the owning account so a foreign account ID can never expose rows.
    rows = connection.execute(
        """SELECT t.* FROM transactions AS t
        JOIN accounts AS a ON a.id = t.account_id
        WHERE t.account_id = ? AND a.customer_id = ? ORDER BY t.posted_at DESC""",
        (account_id, customer_id),
    ).fetchall()
    if not rows and connection.execute(
        "SELECT 1 FROM accounts WHERE id = ? AND customer_id = ?", (account_id, customer_id)
    ).fetchone() is None:
        from app.core.exceptions import not_found
        raise not_found("Account not found")
    return [dict(row) for row in rows]

