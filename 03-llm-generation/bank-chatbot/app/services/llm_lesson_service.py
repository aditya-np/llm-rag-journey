import logging
import json
import re

from fastapi import HTTPException
from openai import AsyncOpenAI, OpenAIError

from app.config import Settings
from app.services.banking_tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)


async def answer_without_tools(message: str, settings: Settings, history: list[dict] | None = None) -> dict:
    """One model request with short chat context, no banking data, and no tools."""
    if not settings.llm_api_key.get_secret_value():
        raise HTTPException(
            status_code=503,
            detail="Set LLM_API_KEY in .env, then restart the app to use this lesson endpoint.",
        )

    steps = [
        "Validated message length",
        f"Provider endpoint: {settings.llm_base_url}",
        f"Request timeout: {settings.llm_timeout_seconds}s",
        f"Included {len(history or [])} prior chat messages",
        "Prepared one Responses API request; no tools provided",
    ]
    client = AsyncOpenAI(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        timeout=float(settings.llm_timeout_seconds),
        max_retries=0,
    )
    try:
        response = await client.responses.create(
            model=settings.llm_model,
            instructions=(
                "You are a beginner-friendly AI learning assistant. Answer the user's general "
                "question clearly and briefly. You have no access to banking records or tools. "
                "Do not claim to know any customer's financial information."
            ),
            input=[
                *[{"role": turn["role"], "content": turn["content"]} for turn in (history or [])],
                {"role": "user", "content": message},
            ],
        )
    except OpenAIError as exc:
        logger.exception(
            "LLM provider request failed (model=%s, base_url=%s)",
            settings.llm_model,
            settings.llm_base_url,
        )
        raise HTTPException(
            status_code=502,
            detail="The model API request failed. Check the API key, model name, network, and provider status.",
        ) from exc
    finally:
        await client.close()

    answer = response.output_text.strip()
    if not answer:
        raise HTTPException(status_code=502, detail="The model returned no text output.")
    steps.extend([f"Received model response ({settings.llm_model})", "Returned response text to caller"])
    return {"answer": answer, "model": settings.llm_model, "steps": steps}


async def warm_up_model(settings: Settings) -> bool:
    """Load the configured model with a tiny, non-banking request during startup."""
    if not settings.llm_warmup_enabled:
        logger.info("LLM warm-up disabled")
        return False
    client = None
    try:
        client = AsyncOpenAI(
            api_key=settings.llm_api_key.get_secret_value(),
            base_url=settings.llm_base_url,
            timeout=float(settings.llm_warmup_timeout_seconds),
            max_retries=0,
        )
        await client.responses.create(
            model=settings.llm_model,
            input="Reply with OK.",
            max_output_tokens=8,
        )
        logger.info("LLM warm-up succeeded (model=%s)", settings.llm_model)
        return True
    except Exception:
        # Startup must remain usable if Ollama is stopped or unavailable.
        logger.warning("LLM warm-up failed; the app will start and retry on first chat", exc_info=True)
        return False
    finally:
        if client is not None:
            await client.close()


def _tool_result_trace(name: str, result: dict) -> str:
    """Describe fetched record types/counts without copying private values to the trace."""
    collection_keys = {
        "get_my_profile": ("name", "full name"),
        "get_my_accounts": ("accounts", "account_type, currency, balance_cents"),
        "get_my_loans": ("loans", "loan_type, outstanding_cents, status"),
        "get_my_cards": ("cards", "card_type, credit_limit_cents, available_credit_cents, status"),
        "get_my_credit_limits": ("credit_limits", "card_type, currency, credit_limit_cents"),
        "get_my_available_credit": ("available_credit", "card_type, currency, available_credit_cents"),
        "get_my_recurring_payments": ("recurring_payments", "payee, amount_cents, cadence, next_payment_date, status"),
        "search_banking_faqs": ("faqs", "question, answer, category"),
    }
    if name in collection_keys:
        key, fields = collection_keys[name]
        if key == "name":
            return "Fetched the authenticated customer's full name"
        return f"Fetched {len(result.get(key, []))} {key.replace('_', ' ')} record(s); fields: {fields}"
    return f"Fetched result fields: {', '.join(sorted(result))}"


def _tools_for_message(message: str) -> list[str]:
    text = message.lower()
    names = bool(re.search(r"\b(name|who am i|profile)\b", text))
    accounts = bool(re.search(r"\b(balance|balances|account|accounts|money)\b", text))
    loans = bool(re.search(r"\b(loan|loans|borrow)\b", text))
    loan_application_intent = bool(re.search(r"\b(need|want|apply|looking for|avail|get)\b", text))
    cards = bool(re.search(r"\b(card|cards|credit|limit)\b", text))
    eligibility = bool(re.search(r"\b(eligible|eligibility|avail|available|qualify|offer)\b", text))
    recurring = bool(re.search(r"\b(recurring|schedule|scheduled|subscription|autopay|automatic payment)\b", text))
    faq = bool(re.search(r"\b(faq|help|lost|fraud|transfer|contact|support)\b", text)) or ("payment" in text and not recurring)
    increase = bool(re.search(r"\b(increase|raise|higher|upgrade)\b.{0,30}\b(limit|credit)\b|\b(limit|credit)\b.{0,30}\b(increase|raise|higher|upgrade)\b", text))
    tools: list[str] = []
    if names:
        tools.append("get_my_profile")
    if accounts:
        tools.append("get_my_accounts")
    if loans:
        if eligibility or loan_application_intent:
            tools.append("check_loan_eligibility")
        if not (eligibility or loan_application_intent) or re.search(r"\b(and|also|plus|existing|have)\b", text):
            tools.append("get_my_loans")
    if cards:
        if increase:
            tools.extend(["get_my_cards", "prepare_limit_increase_request"])
        else:
            if re.search(r"\bavailable credit\b", text):
                tools.append("get_my_available_credit")
            elif re.search(r"\blimit\b", text):
                tools.append("get_my_credit_limits")
            elif eligibility:
                tools.append("check_card_eligibility")
            else:
                tools.append("get_my_cards")
            if eligibility and re.search(r"\blimit\b", text):
                tools.append("check_card_eligibility")
    if recurring:
        tools.append("get_my_recurring_payments")
    if faq:
        tools.append("search_banking_faqs")
    return list(dict.fromkeys(tools))


def _foreign_customer_name(connection, customer_id: str, message: str) -> str | None:
    rows = connection.execute("SELECT id, name FROM customers WHERE id != ?", (customer_id,)).fetchall()
    for row in rows:
        name = row["name"]
        if name and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", message, re.IGNORECASE):
            return name
        first_name = name.split()[0] if name else ""
        if first_name and len(first_name) >= 4 and re.search(rf"\b{re.escape(first_name)}\b", message, re.IGNORECASE):
            return name
    return None


def _required_tools_for_message(message: str) -> list[str]:
    """Every inferred banking request must be supported by its narrow tool call."""
    return _tools_for_message(message)


def _format_verified_answer(tool_name: str, result: dict) -> str | None:
    """Format concise banking answers from verified data, not free-form model text."""
    if tool_name == "get_my_profile" and isinstance(result.get("name"), str):
        return f"Your name is {result['name']}."
    if tool_name in {"get_my_credit_limits", "get_my_available_credit"}:
        key = "credit_limits" if tool_name == "get_my_credit_limits" else "available_credit"
        label = "current credit limit" if tool_name == "get_my_credit_limits" else "available credit"
        rows = result.get(key)
        if isinstance(rows, list):
            if not rows:
                return "There is no active credit card on your selected profile."
            amounts = [
                f"{row['card_type'].capitalize()} card: {label} {row['currency']} {row['credit_limit_cents' if tool_name == 'get_my_credit_limits' else 'available_credit_cents'] / 100:,.2f}."
                for row in rows
            ]
            return " ".join(amounts)
    if tool_name == "check_loan_eligibility" and "eligible_for_demo_offer" in result:
        if result["eligible_for_demo_offer"]:
            amount = result.get("indicative_max_amount_cents", 0)
            offer = f" The indicative demo amount is EUR {amount / 100:,.2f}." if amount else ""
            return f"You may be eligible for a demo loan under the basic rule.{offer} This is not a loan approval or credit decision."
        return "You are not eligible for the demo loan offer under the basic rule because an active loan is recorded. This is not a credit decision."
    if tool_name == "get_my_loans":
        loans = result.get("loans")
        if isinstance(loans, list):
            if not loans:
                return "No loans are recorded for your selected profile."
            return "Your recorded loans: " + "; ".join(
                f"{loan['loan_type'].capitalize()} loan, EUR {loan['outstanding_cents'] / 100:,.2f} outstanding ({loan['status'].replace('_', ' ')})"
                for loan in loans
            ) + "."
    return None


async def answer_banking_chat(
    message: str, settings: Settings, connection, customer_id: str,
    history: list[dict] | None = None,
) -> dict:
    """Tool-calling chat. All private tools receive identity from FastAPI auth."""
    if not settings.llm_api_key.get_secret_value():
        raise HTTPException(status_code=503, detail="Set LLM_API_KEY in .env to use AI banking chat.")
    steps = [
        "Authenticated active profile with its bearer token",
        "Prepared banking-only tool list; customer_id is not a model argument",
        "Used only the current message as model context to prevent unrelated prior account details from leaking into this answer",
        f"Provider endpoint: {settings.llm_base_url}",
    ]
    if re.search(r"\bCUST-\d+\b", message, re.IGNORECASE):
        steps.append("Privacy guard rejected a customer-ID lookup before contacting the model")
        return {"answer": "For your security, I can only access the customer profile currently selected on this screen. I can’t look up another customer’s information.", "model": settings.llm_model, "steps": steps}
    foreign_name = _foreign_customer_name(connection, customer_id, message)
    if foreign_name:
        own = connection.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        own_name = own["name"] if own else "the selected customer"
        steps.append("Privacy guard matched another customer's name; request rejected before contacting the model")
        return {"answer": f"For your security, I can only access {own_name}’s profile, which is selected on this screen. I can’t access {foreign_name}’s account.", "model": settings.llm_model, "steps": steps}
    supported_scope = re.compile(
        r"\b(hi|hello|hey|good morning|good afternoon|good evening|name|who am i|profile|balance|account|loan|borrow|"
        r"card|credit|limit|recurring|schedule|scheduled|payment|faq|help|lost|fraud|transfer|"
        r"contact|support|bank|increase|raise|eligible|eligibility)\b",
        re.IGNORECASE,
    )
    if not supported_scope.search(message):
        steps.append("Banking task boundary rejected the request before contacting the model")
        return {
            "answer": "That is not my job. I can help with your accounts, loans, cards, recurring payments, and banking FAQs.",
            "model": settings.llm_model,
            "steps": steps,
        }
    required_tools = _required_tools_for_message(message)
    allowed_tools = [tool for tool in TOOLS if tool["function"]["name"] in required_tools]
    called_tools: set[str] = set()
    tool_failures: set[str] = set()

    client = AsyncOpenAI(
        api_key=settings.llm_api_key.get_secret_value(), base_url=settings.llm_base_url,
        timeout=float(settings.llm_timeout_seconds), max_retries=0,
    )
    messages = [
        {"role": "system", "content": (
            "You are Smart Bank's assistant. Use only tools supplied for this request and use them before stating "
            "banking facts. Be concise and answer only what was asked; do not add unrelated account details. "
            "A name question gets only the authenticated customer's name. A credit-limit question gets only the "
            "current limit and currency. Never access another customer's records. Eligibility is a demo estimate, "
            "not approval. A limit request is not submitted until the customer confirms it in the UI."
        )},
        {"role": "user", "content": message},
    ]
    action = None
    tool_results: dict[str, dict] = {}
    try:
        for round_number in range(5):
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                tools=allowed_tools or None,
                tool_choice="auto",
                temperature=0,
                max_tokens=192,
            )
            choice = response.choices[0].message
            calls = choice.tool_calls or []
            if not calls:
                answer = (choice.content or "").strip()
                if not answer:
                    raise HTTPException(status_code=502, detail="The model returned no text output.")
                missing_tools = set(required_tools) - called_tools
                if missing_tools or tool_failures:
                    steps.append(f"Required tools missing or failed: {', '.join(sorted(missing_tools | tool_failures))}; withheld unverified model answer")
                    return {
                        "answer": "I couldn’t verify that from your banking records just now. Please try again, or use the deterministic banking panel.",
                        "model": settings.llm_model,
                        "steps": steps,
                    }
                steps.append(f"Model response received after {round_number + 1} call(s)")
                return {"answer": answer, "model": settings.llm_model, "steps": steps, "action": action}
            messages.append(choice.model_dump(exclude_none=True))
            for call in calls:
                name = call.function.name
                called_tools.add(name)
                try:
                    if name not in required_tools:
                        raise ValueError(f"Tool is outside the request scope: {name}")
                    args = json.loads(call.function.arguments or "{}")
                    if not isinstance(args, dict):
                        raise ValueError("Tool arguments must be a JSON object")
                    result, proposed_action = execute_tool(name, args, connection, customer_id)
                    tool_results[name] = result
                    if proposed_action:
                        action = proposed_action
                    steps.append(f"Model selected tool: {name}")
                    steps.append(_tool_result_trace(name, result))
                    steps.append(f"Tool output returned by backend: {json.dumps(result, default=str, ensure_ascii=False)}")
                except (ValueError, json.JSONDecodeError) as exc:
                    result = {"error": str(exc)}
                    tool_failures.add(name)
                    steps.append(f"Tool called: {name} · rejected invalid arguments")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)})
            if len(required_tools) == 1 and required_tools[0] in tool_results:
                exact_answer = _format_verified_answer(required_tools[0], tool_results[required_tools[0]])
                if exact_answer:
                    steps.append("Server formatted the verified result directly; skipped the second model request and omitted unrelated fields")
                    return {"answer": exact_answer, "model": settings.llm_model, "steps": steps}
        raise HTTPException(status_code=502, detail="The model exceeded the maximum banking tool-call rounds.")
    except OpenAIError as exc:
        logger.exception("AI banking request failed (model=%s, base_url=%s)", settings.llm_model, settings.llm_base_url)
        raise HTTPException(status_code=502, detail="The model API request failed. Check Ollama, model availability, and tool-calling support.") from exc
    finally:
        await client.close()
