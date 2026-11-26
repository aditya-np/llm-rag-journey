from app.services.banking_tools import execute_tool
from app.services.review_service import create_limit_increase_request


def test_account_tool_is_scoped_to_authenticated_customer(demo_db):
    result, action = execute_tool("get_my_accounts", {}, demo_db, "CUST-1001")
    assert action is None
    assert result["accounts"]
    assert {account["customer_id"] for account in result["accounts"]} == {"CUST-1001"}


def test_limit_tool_prepares_but_does_not_submit(demo_db):
    before = demo_db.execute("SELECT count(*) FROM limit_increase_requests").fetchone()[0]
    result, action = execute_tool(
        "prepare_limit_increase_request",
        {"card_id": "CARD-1001-01", "requested_limit_cents": 500_000},
        demo_db,
        "CUST-1001",
    )
    after = demo_db.execute("SELECT count(*) FROM limit_increase_requests").fetchone()[0]
    assert result["proposal"]["current_limit_cents"] == 300_000
    assert action["type"] == "limit_increase"
    assert after == before


def test_limit_tool_rejects_foreign_card(demo_db):
    result, action = execute_tool(
        "prepare_limit_increase_request",
        {"card_id": "CARD-1001-01", "requested_limit_cents": 500_000},
        demo_db,
        "CUST-1002",
    )
    assert result == {"error": "Active card not found for this profile."}
    assert action is None


def test_seed_adds_fifty_distinct_customers(demo_db):
    count = demo_db.execute("SELECT count(*) FROM customers").fetchone()[0]
    assert count == 52
    assert demo_db.execute("SELECT count(*) FROM accounts WHERE customer_id LIKE 'CUST-10%' ").fetchone()[0] >= 51
    names = [row[0] for row in demo_db.execute("SELECT name FROM customers")]
    assert len(set(names)) == 52
    assert not any(name.startswith("Demo Customer") for name in names)


def test_large_limit_increase_is_flagged_for_human(demo_db):
    result = create_limit_increase_request(
        demo_db, "CUST-1001", "CARD-1001-01", 500_001, self_service_max_cents=100_000
    )
    assert result["requires_human_follow_up"] is True
    assert result["status"] == "pending_human_review"
    assert "call" in result["message"]
