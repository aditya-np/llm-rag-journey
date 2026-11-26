# Lesson 1: one plain LLM call

## Goal

Send one general message from FastAPI to Ollama's OpenAI-compatible Responses API and return the text. This lesson has no banking context, database lookup, function calling, or agent loop. The banking chat panel reuses the same endpoint in `banking_chat` mode and sends only the current message to prevent prior bank details from influencing a narrow answer.

## Files to study

- `app/api/llm_lesson.py` is the HTTP boundary. It validates the request and requires the current demo identity.
- `app/schemas/llm_lesson.py` limits the input to a non-empty message of at most 1,000 characters.
- `app/services/llm_lesson_service.py` makes one model request and returns its text plus a small step list.
- `app/config.py` reads the API key and model name from the server environment.

## Request path

```text
Browser/API client
  -> POST /v1/learning/llm
  -> validate request and demo bearer token
  -> prepare instructions + user message
  -> Ollama Responses API (no tools parameter)
  -> return response.output_text
```

The API key stays on the server. The browser never receives it. With the default local Ollama URL, prompts go to your local Ollama server. If you change `LLM_BASE_URL` to a hosted provider, prompts are sent to that provider, so use general, non-sensitive practice prompts in this lesson.

## Try it

1. Configure Ollama and download the model with `ollama pull qwen3.5:0.8b`.
2. In `.env`, set `LLM_API_KEY=ollama`, `LLM_BASE_URL=http://localhost:11434/v1`, and `LLM_MODEL=qwen3.5:0.8b`. The local server ignores the placeholder API key. `LLM_TIMEOUT_SECONDS` defaults to 120; raise it if your computer needs more time for a cold model load.
3. Restart the app after changing `.env`.
4. Open `/docs`, authorize with a demo bearer token, and call `POST /v1/learning/llm` with:

```json
{
  "message": "Explain what a language model is in one short paragraph."
}
```

5. Inspect `answer`, `model`, and `steps` in the response.

## What to notice

- The browser calls your own FastAPI endpoint; FastAPI calls the model provider.
- The API key is needed only on the server.
- The model returns text. It has no account data and no way to call your banking services.
- This is an LLM call, but not yet an agent. The application makes one request and stops.

Next lesson: request a small structured classification result, then compare it with the current deterministic intent rules before allowing any model-selected tool.

