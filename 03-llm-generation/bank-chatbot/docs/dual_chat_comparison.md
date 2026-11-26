# Comparing the deterministic and AI panels

## What changed

The dashboard has two chat panels. The deterministic helper remains the rule-based banking assistant. The AI assistant calls the existing `POST /v1/learning/llm` endpoint with `mode: "banking_chat"`; no second chat API was added. Omitting `mode` keeps the original plain-LLM lesson behavior.

The backend first narrows the allowed tool list based on the current message. Qwen can then request only one of those functions. For a single-field name, credit limit, or loan result, Python formats the verified data directly and skips another model request. For other questions, tool results can be sent back for Qwen to phrase the answer. Each request contains only the current message, so details from earlier replies cannot bleed into a narrow follow-up. UI **Steps** records model/tool calls, returned fields, and tool outputs, not hidden reasoning. The proposal tool cannot write to the database; a visible customer confirmation button invokes the existing limit request endpoint.

## Active-profile authorization path

```text
Main-screen customer selector
  -> selects that demo customer's bearer token
  -> api() in app/web/app.js adds Authorization: Bearer <selected token>
  -> POST /v1/learning/llm with mode=banking_chat
  -> current_customer_id in app/core/security.py validates the token
  -> app/config.py maps the token to its customer ID
  -> route opens a request-local database connection
  -> allow-listed tools query using the server-resolved customer ID
  -> tool names/statuses appear in response steps
  -> Ollama receives the message, tool definitions, and results
```

The token is checked by FastAPI, not sent as model input. The customer ID is resolved by the server and never appears in tool schemas or model-selected arguments. Queries are scoped in SQL by the resolved identity, and card proposals also verify ownership. Mentioning a `CUST-...` ID is rejected before contacting the model. Changing the main-screen profile resets both chat transcripts; all later requests use the newly selected token.

## Files to compare

- `app/web/index.html`: separate transcript and input form for each panel.
- `app/web/app.js`: `submitChat()` handles deterministic behavior; `submitAiChat()` handles the AI panel. Both use the selected profile token through `api()`.
- `app/api/llm_lesson.py`: existing authenticated endpoint used by the AI panel.
- `app/core/security.py`: validates the active bearer token and resolves the customer identity.

Try the same account-balance question in both panels. Both use the selected demo profile, but one follows browser-side rules while the other asks Qwen to select a server tool. Ask for a limit increase: the AI panel may prepare a proposal; only pressing its confirmation button submits it. For the warm start, app startup sends one static prompt to the configured model and logs whether it succeeded. Warm-up failure is non-fatal.
