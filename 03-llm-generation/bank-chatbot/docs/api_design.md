# API design

The API is split by banking capability. Routes validate HTTP input, services apply business rules, and database access stays customer-scoped.

## Endpoints

| Method | Path | Auth | Operation |
| --- | --- | --- | --- |
| GET | `/health` | No | Health check |
| GET | `/v1/auth/me` | Yes | Resolve the authenticated demo customer |
| GET | `/v1/auth/demo-profiles` | Yes | List synthetic profile names/IDs for the local profile selector; no account data |
| GET | `/v1/accounts` | Yes | List own accounts and balances |
| GET | `/v1/accounts/{account_id}` | Yes | Read one owned account |
| GET | `/v1/accounts/{account_id}/transactions` | Yes | Read transactions for an owned account |
| GET | `/v1/loans` | Yes | List own loans |
| GET | `/v1/loans/eligibility` | Yes | Demo eligibility result |
| GET | `/v1/cards` | Yes | Read own cards and credit limits |
| GET | `/v1/cards/eligibility` | Yes | Demo eligibility result |
| POST | `/v1/cards/limit-increase-requests` | Yes | The only write operation; creates a review request |
| GET | `/v1/recurring-payments` | Yes | List own scheduled payments |
| GET | `/v1/faqs?q=...` | No | Search public FAQs |
| POST | `/v1/learning/llm` | Yes | Plain LLM lesson by default; optional `banking_chat` mode with scoped read tools |

The AI panel uses the same LLM route with `mode: "banking_chat"`. The default mode remains `lesson`. Its limit-request tool only prepares a proposal; explicit customer confirmation calls the existing POST route above.

Personal routes derive `customer_id` from the authenticated bearer token. They do not accept a caller-supplied customer ID. Account and card IDs are checked together with the resolved customer ID. Missing and foreign-owned IDs return the same `404` response.

Money amounts are integer minor units. `300000` means EUR 3,000.00. The limit-increase request body is:

```json
{
  "card_id": "CARD-1001-01",
  "requested_limit_cents": 400000
}
```

Successful submissions return `202 Accepted` and a request ID. They do not modify a card's actual limit.

