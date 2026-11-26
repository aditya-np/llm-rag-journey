"""Small, server-owned tools exposed to the AI banking chat mode."""
import sqlite3

from app.services import account_service, credit_card_service, faq_service, loan_service, payment_service

TOOLS = [
    {"type": "function", "function": {"name": "get_my_profile", "description": "Return only the authenticated customer's full name. Use for questions like 'What is my name?'.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_my_accounts", "description": "Return only account type, currency, and balance for the authenticated customer. Do not fetch or mention loans, cards, payments, or FAQs unless separately requested.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_my_loans", "description": "Get the authenticated customer's existing loans.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "check_loan_eligibility", "description": "Check the demo loan eligibility rule for the authenticated customer.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_my_credit_limits", "description": "Return only each active card's type, currency, and current credit limit. Do not return available credit, loans, recurring payments, or other records.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_my_available_credit", "description": "Return only each active card's type, currency, and available credit. Do not return credit limits or other banking records.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_my_cards", "description": "Get the authenticated customer's card identifiers and details. Use only when preparing a credit-limit request that requires a card ID.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "check_card_eligibility", "description": "Check the demo card eligibility rule for the authenticated customer.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_my_recurring_payments", "description": "Get the authenticated customer's recurring payment schedule.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "search_banking_faqs", "description": "Search public banking FAQs by topic.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "The FAQ topic or question", "maxLength": 200}}, "required": ["query"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "prepare_limit_increase_request", "description": "Prepare a limit-increase proposal for the customer to review. This does not submit it. The customer must explicitly confirm using the UI button.", "parameters": {"type": "object", "properties": {"card_id": {"type": "string", "description": "An active card ID returned by get_my_cards"}, "requested_limit_cents": {"type": "integer", "description": "Requested new limit in cents", "minimum": 1}}, "required": ["card_id", "requested_limit_cents"], "additionalProperties": False}}},
]


def execute_tool(name: str, arguments: dict, connection: sqlite3.Connection, customer_id: str) -> tuple[dict, dict | None]:
    """Execute only allow-listed tools, always scoped by the authenticated ID."""
    if name == "get_my_profile":
        row = connection.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        return ({"name": row["name"]} if row else {"error": "Profile not found."}), None
    if name == "get_my_accounts":
        rows = account_service.list_accounts(connection, customer_id)
        return {"accounts": [{"account_type": row["account_type"], "currency": row["currency"], "balance_cents": row["balance_cents"]} for row in rows]}, None
    if name == "get_my_loans":
        loans = loan_service.list_loans(connection, customer_id)
        return {"loans": [{"loan_type": loan["loan_type"], "outstanding_cents": loan["outstanding_cents"], "status": loan["status"]} for loan in loans]}, None
    if name == "check_loan_eligibility":
        return loan_service.eligibility(connection, customer_id), None
    if name == "get_my_cards":
        cards = credit_card_service.list_cards(connection, customer_id)
        return {"cards": [{
            "id": card["id"], "card_type": card["card_type"],
            "credit_limit_cents": card["credit_limit_cents"],
            "available_credit_cents": card["available_credit_cents"], "status": card["status"],
        } for card in cards]}, None
    if name == "get_my_credit_limits":
        cards = credit_card_service.list_cards(connection, customer_id)
        return {"credit_limits": [{"card_type": card["card_type"], "currency": "EUR", "credit_limit_cents": card["credit_limit_cents"]} for card in cards if card["status"] == "active"]}, None
    if name == "get_my_available_credit":
        cards = credit_card_service.list_cards(connection, customer_id)
        return {"available_credit": [{"card_type": card["card_type"], "currency": "EUR", "available_credit_cents": card["available_credit_cents"]} for card in cards if card["status"] == "active"]}, None
    if name == "check_card_eligibility":
        return credit_card_service.eligibility(connection, customer_id), None
    if name == "get_my_recurring_payments":
        payments = payment_service.list_recurring_payments(connection, customer_id)
        return {"recurring_payments": [{
            "payee": payment["payee"], "amount_cents": payment["amount_cents"],
            "currency": payment["currency"], "cadence": payment["cadence"],
            "next_payment_date": payment["next_payment_date"], "status": payment["status"],
        } for payment in payments]}, None
    if name == "search_banking_faqs":
        query = arguments.get("query", "")
        if not isinstance(query, str) or len(query) > 200:
            raise ValueError("FAQ query must be text up to 200 characters")
        return {"faqs": faq_service.search(connection, query)}, None
    if name == "prepare_limit_increase_request":
        card_id = arguments.get("card_id")
        requested = arguments.get("requested_limit_cents")
        if not isinstance(card_id, str) or not isinstance(requested, int) or isinstance(requested, bool) or requested <= 0:
            raise ValueError("A card ID and positive requested limit in cents are required")
        card = connection.execute("SELECT * FROM cards WHERE id = ? AND customer_id = ? AND status = 'active'", (card_id, customer_id)).fetchone()
        if card is None:
            return {"error": "Active card not found for this profile."}, None
        if requested <= card["credit_limit_cents"]:
            return {"error": "Requested new limit must be higher than the current limit."}, None
        return {
            "proposal": {"card_id": card_id, "requested_limit_cents": requested, "current_limit_cents": card["credit_limit_cents"]},
            "note": "This is only a proposal. Wait for the customer to explicitly confirm before submitting it.",
        }, {"type": "limit_increase", "card_id": card_id, "requested_limit_cents": requested, "current_limit_cents": card["credit_limit_cents"]}
    raise ValueError(f"Tool is not allow-listed: {name}")
