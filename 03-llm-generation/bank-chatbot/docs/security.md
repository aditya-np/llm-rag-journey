# Security notes

This is a local educational backend, not a production banking service.

- Demo bearer tokens map to customer IDs in `DEMO_TOKENS_JSON`. These tokens are public example credentials. Use a proper identity provider, token validation, expiry, and key management for any real deployment.
- `GET /v1/auth/demo-profiles` is a local-demo-only selector helper. It returns fictional customer IDs and names, but no emails, balances, or other account details. Do not expose a cross-customer directory in a real banking app.
- The API derives the current customer identity from the bearer token. Personal endpoints do not accept a customer ID as authority.
- Database queries for personal data include the resolved customer ID. An account/card ID owned by another customer is indistinguishable from an unknown ID at the API boundary.
- SQLite calls use bound parameters for values. Dynamic table names are restricted to an internal allowlist.
- One shared SQLite connection is guarded by a lock to support this small local demo safely across FastAPI's sync worker threads. A real service should use a managed database and a connection pool.
- Do not log credentials or full financial records. Any future agent/tool trace should carry verified identity context, redact secrets, and minimize sensitive data.
- The active profile's bearer token is checked before either LLM mode. In `banking_chat`, the model receives an allow-list of tools; each private tool is executed with the customer ID resolved server-side, never a model-provided customer ID. The authenticated panel's trace shows tool names, returned fields/counts, and the exact tool output sent to the model. It is not written to application logs.
- The LLM tool loop is bounded to five model rounds. The limit-increase tool only prepares a proposal; a separate customer button invokes the sole write route. This is not an agent framework or RAG implementation. There is no external bank integration, actual human-call integration, or authorization suitable for production.

