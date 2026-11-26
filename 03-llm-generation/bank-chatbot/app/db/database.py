import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request


def connect(database_url: str) -> sqlite3.Connection:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("This educational backend currently supports SQLite URLs only")
    path = database_url[len(prefix) :]
    if path != ":memory:":
        db_path = Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    lock = request.app.state.db_lock
    lock.acquire()
    try:
        yield request.app.state.db
    finally:
        lock.release()


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(id),
            account_type TEXT NOT NULL, currency TEXT NOT NULL, balance_cents INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
            description TEXT NOT NULL, amount_cents INTEGER NOT NULL,
            currency TEXT NOT NULL, posted_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS loans (
            id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(id),
            loan_type TEXT NOT NULL, original_amount_cents INTEGER NOT NULL,
            outstanding_cents INTEGER NOT NULL, monthly_payment_cents INTEGER NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(id),
            card_type TEXT NOT NULL, credit_limit_cents INTEGER NOT NULL,
            available_credit_cents INTEGER NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS recurring_payments (
            id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(id),
            payee TEXT NOT NULL, amount_cents INTEGER NOT NULL, currency TEXT NOT NULL,
            cadence TEXT NOT NULL, next_payment_date TEXT NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS faqs (
            id TEXT PRIMARY KEY, question TEXT NOT NULL, answer TEXT NOT NULL,
            category TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS limit_increase_requests (
            id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(id),
            card_id TEXT NOT NULL REFERENCES cards(id), requested_limit_cents INTEGER NOT NULL,
            current_limit_cents INTEGER NOT NULL, status TEXT NOT NULL,
            requires_human_follow_up INTEGER NOT NULL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
        CREATE INDEX IF NOT EXISTS idx_loans_customer ON loans(customer_id);
        CREATE INDEX IF NOT EXISTS idx_cards_customer ON cards(customer_id);
        CREATE INDEX IF NOT EXISTS idx_recurring_customer ON recurring_payments(customer_id);
        """
    )
    connection.commit()

