# Chat panels

The dashboard has two independent panels so you can compare behavior side by side.

- **Deterministic banking helper:** `app/web/app.js` uses explicit rules and calls the authenticated banking endpoints. It can fetch account balances, loan and card data, recurring payments, and FAQs.
- **AI banking assistant:** the panel sends requests to the existing `POST /v1/learning/llm` endpoint in `banking_chat` mode. Each request contains only the current message and a narrow allow-list of server tools selected for that task. Private queries are scoped to the active bearer-token identity; customer IDs are never tool arguments. Limit increase requests require a separate explicit confirmation.

The AI panel can answer supported account-specific questions through the allow-listed server tools. The model does not receive a database connection or a customer ID. The server resolves the active profile from its bearer token, scopes each private tool to that profile, and rejects explicit requests for another customer's ID or name before contacting Qwen.

The selected demo profile supplies the bearer token for both panels. The browser never sends a `customer_id` field. The server resolves identity from the bearer token and checks it before accepting a request. See [the comparison walkthrough](dual_chat_comparison.md) for the code path.

