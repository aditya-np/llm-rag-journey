# Smart Banking Chatbot — Learning Reflection

## Concept

I wanted to understand how a language model can be connected to a real application without giving it direct access to private data or letting it perform arbitrary actions.

This project uses a fictional banking system to explore that boundary. A customer asks a question in a chat panel. The application checks which customer is signed in, decides which banking functions are relevant, and lets the language model request one of those functions. Python runs the function, checks the data against the selected customer, and returns a result. The model can help interpret the request and phrase an answer, but the application remains responsible for identity, database access, and banking rules.

## What we built

- A FastAPI backend with SQLite tables for customers, accounts, transactions, loans, credit cards, recurring payments, FAQs, and limit-increase review requests.
- A demo profile selector. Each profile uses a demo bearer token; the server maps that token to a customer ID for private lookups.
- Two separate chat panels:
  - A deterministic panel that matches simple rules in the browser and calls banking HTTP APIs.
  - An AI panel that sends questions to the existing `/v1/learning/llm` endpoint in `banking_chat` mode.
- A plain LLM lesson mode on that same endpoint. It makes a general model request without banking tools; it remains the default mode.
- A small set of LLM tools for profile name, account balances, loans and demo eligibility, cards and limits, recurring payments, FAQ search, and preparing a limit-increase request.
- Server-side tool dispatch. Each tool calls Python service code, and private banking services use the customer ID resolved from the bearer token.
- A confirmation step for the only write operation. The AI can prepare a limit-increase proposal, but the customer must click to submit it. Larger increases are marked for human review; the demo does not contact a bank employee or change the card limit.
- Startup model warm-up and visible chat steps showing the route and tool activity.

## What I learned

I learned how an HTTP request travels through a browser, FastAPI route, authentication dependency, Python service, and SQLite query. I also learned how a model can request a function call and how the application can execute that function itself instead of giving the model a database connection.

The current tool routing is basic. `_tools_for_message()` uses keyword rules to narrow the tools available for a message. Qwen can request a function from that limited set. Some simple answers are formatted directly by Python from verified data; other answers may go back to the model for wording.

This is an early, small-scale LLM integration:

- It uses one local model, `qwen3.5:0.8b`, through Ollama.
- Its scope and tool selection rely on simple rules, so different wording can be misunderstood or rejected.
- It has one manually written, bounded function-calling loop, not an agent framework or a collection of specialist agents.
- It has no RAG pipeline, embeddings, vector database, document chunking, or cited policy documents. FAQ search is basic SQLite text matching.

The main achievement is learning the basic boundary between an LLM and application code: the model can request a limited operation, while the backend decides whether it is allowed and performs it.

## Future scopes (CODEX GENERATED)

These are possible next lessons, best tackled one at a time:

1. **Improve intent and tool selection.** Replace the current keyword checks with a structured intent result, then compare its accuracy with the existing rules.
2. **Add evaluations.** Create representative banking questions, expected tools, expected answers, and privacy cases; measure regressions when prompts or models change.
3. **Make multi-tool answers more controlled.** Define how to combine results for requests such as “total balance and loans,” and verify the answer against the returned data.
4. **Add conversation persistence carefully.** Store only the context needed for follow-up questions and ensure old customer data cannot leak between profile changes.
5. **Learn RAG as a separate topic.** Add fictional bank policy documents, retrieve relevant passages, show their sources, and compare those answers with the current FAQ text search.
6. **Learn agent orchestration after the basics.** Study planning, tool choice, stopping conditions, retries, and human approval using this simple dispatcher as the starting point.
7. **Improve operations.** Add structured request IDs, latency and failure metrics, streaming responses, cancellation, and clear handling for slow or unavailable models.
8. **Explore production architecture separately.** Replace demo tokens with real identity, use a managed database and connection pool, and add operational controls before considering any real financial data.

The project is a learning sandbox, not a production banking service. The next scope should be chosen deliberately so each new LLM concept can be understood and compared with the simpler version already here.
