# Smart Banking Backend

A backend-first learning project focused on connecting an LLM to banking functions safely and transparently. It compares a deterministic chatbot with an AI chatbot that can request a limited set of Python functions (“tools”). The model never connects directly to SQLite.

All customers, account details, and eligibility outcomes are fictional demo data. This is not a real banking system.

## The core: LLM service + banking tools

The central code is:

- [`app/services/llm_lesson_service.py`](app/services/llm_lesson_service.py) — checks scope, narrows the tools for the current message, calls Ollama/Qwen, runs the bounded function-call loop, and builds the response trace.
- [`app/services/banking_tools.py`](app/services/banking_tools.py) — describes the functions Qwen may request and dispatches each accepted function to a Python banking service.
- [`app/api/llm_lesson.py`](app/api/llm_lesson.py) — the authenticated HTTP route used by the AI panel.

### What “tool” means here

Yes: `get_my_accounts`, `check_loan_eligibility`, `get_my_credit_limits`, and the other named functions are **LLM tools**. Each has a JSON function schema (name, description, and parameters) supplied to the model. Qwen can respond with a structured function call. Python then validates the function name and executes the matching dispatcher branch.

A tool is not the SQL query itself and is not automatically a public HTTP endpoint. The tool calls an internal service; the service applies the rule and queries SQLite. For example:

```text
LLM tool: check_loan_eligibility
    -> execute_tool() in banking_tools.py
    -> loan_service.eligibility(connection, authenticated_customer_id)
    -> SQL checks for an active loan belonging to that customer
    -> Python returns the demo eligibility result
```

### How a user message selects a tool

The backend does a deterministic first pass in `_tools_for_message()`. It uses simple keyword rules to select which tools are relevant and offers Qwen only that subset. Qwen may then choose a function from the supplied subset. The server executes it; Qwen never executes Python or SQL itself.

| Example question | Tool(s) made available | What the tool/service does |
| --- | --- | --- |
| “What is my name?” | `get_my_profile` | Reads only the name for the authenticated customer. Python formats the short answer. |
| “What is my balance?” | `get_my_accounts` | Reads that customer’s account types, currencies, and balances. Qwen may phrase or total the result. |
| “Total balance and loans?” | `get_my_accounts`, `get_my_loans` | Fetches only account and loan fields requested; Qwen can combine them. |
| “I need a loan” | `check_loan_eligibility` | Applies the demo rule based on whether the customer has an active loan. Python formats the verified result without a second model call. |
| “What is my credit limit?” | `get_my_credit_limits` | Returns only active card type, currency, and current limit. Python formats the answer directly. |
| “How much available credit do I have?” | `get_my_available_credit` | Returns only available credit fields. |
| “Do I have recurring payments?” | `get_my_recurring_payments` | Reads the selected customer’s schedule. |
| “How do I report a lost card?” | `search_banking_faqs` | Searches public FAQ rows using SQLite text matching. This is not RAG. |
| “Increase my card limit” | `get_my_cards`, `prepare_limit_increase_request` | Prepares a proposal. It does not write to the database; the customer must confirm in the UI. |

If a question asks about another customer’s ID or name, or is outside the supported banking scope, the backend rejects it before sending it to Qwen. If the model fails to call a required tool, the backend withholds an unverified banking answer.

### End-to-end AI request

```mermaid
sequenceDiagram
    actor Customer
    participant UI as Browser app.js
    participant API as FastAPI POST /v1/learning/llm
    participant Auth as current_customer_id
    participant LLM as llm_lesson_service
    participant Qwen as Ollama / Qwen
    participant Dispatch as banking_tools.execute_tool
    participant Service as Banking service
    participant DB as SQLite

    Customer->>UI: Enter question in AI panel
    UI->>API: JSON message + mode=banking_chat + Bearer token
    API->>Auth: Validate selected profile token
    Auth-->>API: Trusted customer_id
    API->>LLM: Message + trusted ID + database connection
    LLM->>LLM: Check ID/name privacy and supported task
    LLM->>LLM: _tools_for_message selects allowed tools
    LLM->>Qwen: Message + instructions + allowed function schemas
    Qwen-->>LLM: Function call request
    LLM->>Dispatch: Allow-listed tool name + arguments + trusted ID
    Dispatch->>Service: Call matching service function
    Service->>DB: Parameterized SQL scoped to trusted ID
    DB-->>Service: Matching rows
    Service-->>Dispatch: Data or rule result
    Dispatch-->>LLM: Tool result + trace steps
    alt Precise single-tool response
        LLM->>LLM: Python formats verified result; skips another model call
    else Response needs model wording
        LLM->>Qwen: Send tool result for response wording
        Qwen-->>LLM: Final text
    end
    LLM-->>API: answer + model + steps + optional action
    API-->>UI: JSON response
    UI-->>Customer: Answer and expandable Steps
```

The **Steps** shown in the AI panel expose operational events—such as the allowed tool, its result fields, and the tool output—not hidden model reasoning.

### The selected profile is the authorization source

```text
Main-screen customer selector
  -> selects a demo token
  -> app.js api() sends Authorization: Bearer <token>
  -> FastAPI current_customer_id() validates and resolves the token
  -> service receives the trusted customer_id
  -> SQL filters by that customer_id
```

The request body and tool schemas do not accept a customer ID as authority. The tool dispatcher passes the server-resolved ID into services, and those services query only that customer’s records. Demo tokens are public examples, not production authentication.

## Two chat panels

| Panel | Where intent is matched | Model used? | Banking lookup |
| --- | --- | --- | --- |
| Deterministic | JavaScript `answerChat()` rules in `app/web/app.js` | No | Calls ordinary REST endpoints such as `GET /v1/accounts` |
| AI banking | Python `_tools_for_message()` narrows tools; Qwen can select among them | Yes | Python dispatches tools to banking services and SQLite |

Both panels use the active profile token. The deterministic panel follows explicit browser-side rules. The AI panel uses the same authenticated `POST /v1/learning/llm` route with `mode: "banking_chat"`.

The default mode for that endpoint is `lesson`. Lesson mode makes one plain model request with no banking tools or database context. This preserves the original LLM learning API; no separate AI chat endpoint was added.

## HTTP APIs versus LLM tools

An **API route** is an HTTP path called by the browser or another HTTP client. A **tool** is a function schema shown to Qwen and executed by the Python dispatcher. A tool may call a service that is also used by an API route, but the tool itself is not necessarily an HTTP endpoint.

| HTTP API | Purpose |
| --- | --- |
| `GET /health` | Check whether the app is running. |
| `GET /v1/auth/me` | Return the currently selected profile. |
| `GET /v1/auth/demo-profiles` | Return fictional names and IDs for the local profile selector; no account data. |
| `GET /v1/accounts` | Read the selected customer’s accounts and balances. |
| `GET /v1/accounts/{account_id}` | Read one account if it belongs to the selected customer. |
| `GET /v1/accounts/{account_id}/transactions` | Read transactions for an owned account. |
| `GET /v1/loans` | Read the selected customer’s loan records. |
| `GET /v1/loans/eligibility` | Apply the demo loan eligibility rule. |
| `GET /v1/cards` | Read the selected customer’s cards and credit details. |
| `GET /v1/cards/eligibility` | Apply the demo card eligibility rule. |
| `GET /v1/recurring-payments` | Read the selected customer’s recurring schedule. |
| `GET /v1/faqs?q=...` | Search public FAQ rows; no customer financial data is returned. |
| `POST /v1/learning/llm` | Existing authenticated model endpoint; lesson mode by default, AI banking mode when requested. |
| `POST /v1/cards/limit-increase-requests` | The single write: submit a customer-confirmed limit request for review. |

The AI panel calls `POST /v1/learning/llm`. Python tool calls happen inside that request; they do not each make a new HTTP request from the browser.

## The single write operation

The AI may prepare a limit-increase proposal, but preparation does not submit it. The user must click the confirmation button, which calls `POST /v1/cards/limit-increase-requests`. The route validates the body, resolves the active profile, and calls `review_service.create_limit_increase_request()`.

Money is stored as integer cents: `300000` is EUR 3,000.00. The service verifies card ownership, checks that the requested new limit is higher than the current one, calculates the increase, and compares it with `SELF_SERVICE_LIMIT_INCREASE_MAX` (default EUR 1,000). Above the threshold, it records `pending_human_review`. The “bank representative will call” message is demo text: no call or employee notification happens, and the card limit does not change.

## Startup and local setup

Requires Python 3.11+. Python includes SQLite support; SQLite does not need a separate install.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open the dashboard at `http://127.0.0.1:8000/` and the FastAPI docs at `http://127.0.0.1:8000/docs`.

At startup, `app/main.py` loads settings, initializes SQLite with `app/db/database.py`, inserts fictional customers and records with `app/db/seed.py`, then calls `warm_up_model()` with a harmless static prompt. Warm-up failure is logged but does not prevent startup. The default model configuration is local Ollama with `qwen3.5:0.8b`; see `.env.example`.

## Key folders

```text
app/
  api/          FastAPI HTTP routes
  core/         Authentication, ownership checks, exceptions
  db/           SQLite schema, connections, seed data
  models/       TypedDict descriptions of records (not an ORM)
  schemas/      Pydantic request/response validation
  services/     Banking rules, LLM orchestration, tool schemas/dispatch
  web/          HTML, CSS, JavaScript dashboard and chat panels
tests/          Authentication, ownership, tool, seed, and concurrency cases
docs/           Explanations; Markdown is read by people, not executed per request
```

For a file-by-file walkthrough, see [Request lifecycle](docs/request_lifecycle.md), [API design](docs/api_design.md), [business rules](docs/business_rules.md), and [security notes](docs/security.md).

## Tests

Install the test extra with `pip install -e '.[test]'`, then run `pytest`. The suite covers profile authorization, private tool ownership, limit-request behavior, generated profiles, and parallel profile reads. The concurrency case checks correct isolation; it is not a load benchmark.

## Project boundaries

- All data and eligibility rules are fictional.
- The demo bearer-token map is not production authentication.
- This project uses no RAG pipeline, vector database, or agent framework. The AI banking mode does use a small, application-managed function-calling loop.
- Human follow-up is represented by a database status only; no real bank employee is contacted.
