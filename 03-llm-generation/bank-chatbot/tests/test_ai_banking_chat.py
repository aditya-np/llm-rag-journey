import asyncio
from types import SimpleNamespace

from app.config import Settings
from app.services import llm_lesson_service
from app.services.banking_tools import execute_tool


class ModelMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []

    def model_dump(self, exclude_none=True):
        return {"role": "assistant", "content": self.content, "tool_calls": self.tool_calls}


def test_ai_chat_calls_allowlisted_tool_then_answers(monkeypatch, demo_db):
    card = SimpleNamespace(function=SimpleNamespace(name="get_my_accounts", arguments="{}"), id="call-1")
    responses = [
        SimpleNamespace(choices=[SimpleNamespace(message=ModelMessage(tool_calls=[card]))]),
        SimpleNamespace(choices=[SimpleNamespace(message=ModelMessage(content="Your account balance is available."))]),
    ]

    class FakeCompletions:
        async def create(self, **kwargs):
            assert kwargs["tools"]
            return responses.pop(0)

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

        async def close(self):
            return None

    monkeypatch.setattr(llm_lesson_service, "AsyncOpenAI", lambda **kwargs: FakeClient())
    result = asyncio.run(llm_lesson_service.answer_banking_chat(
        "What is my balance?", Settings(), demo_db, "CUST-1001"
    ))
    assert result["answer"] == "Your account balance is available."
    assert any("Model selected tool: get_my_accounts" in step for step in result["steps"])


def test_ai_chat_rejects_customer_id_before_model_call(monkeypatch, demo_db):
    def should_not_create_client(**kwargs):
        raise AssertionError("customer ID privacy guard should run before the model")

    monkeypatch.setattr(llm_lesson_service, "AsyncOpenAI", should_not_create_client)
    result = asyncio.run(llm_lesson_service.answer_banking_chat(
        "Show CUST-1002 balance", Settings(), demo_db, "CUST-1001"
    ))
    assert "can't look up another customer" in result["answer"].lower()


def test_ai_chat_rejects_other_customer_by_name(monkeypatch, demo_db):
    def should_not_create_client(**kwargs):
        raise AssertionError("foreign customer names should be rejected before the model")

    monkeypatch.setattr(llm_lesson_service, "AsyncOpenAI", should_not_create_client)
    result = asyncio.run(llm_lesson_service.answer_banking_chat(
        "Can you access Jamie's account for me?", Settings(), demo_db, "CUST-1001"
    ))
    assert "only access Alex Morgan" in result["answer"]
    assert "can't access Jamie Lee's account" in result["answer"]


def test_name_and_credit_limit_tools_return_only_requested_fields(demo_db):
    profile, _ = execute_tool("get_my_profile", {}, demo_db, "CUST-1001")
    limits, _ = execute_tool("get_my_credit_limits", {}, demo_db, "CUST-1001")
    assert profile == {"name": "Alex Morgan"}
    assert limits == {"credit_limits": [{"card_type": "standard", "currency": "EUR", "credit_limit_cents": 300_000}]}


def test_credit_limit_answer_is_exact_and_model_cannot_add_other_details(monkeypatch, demo_db):
    call = SimpleNamespace(function=SimpleNamespace(name="get_my_credit_limits", arguments="{}"), id="call-limit")

    class FakeCompletions:
        count = 0

        async def create(self, **kwargs):
            self.count += 1
            assert [tool["function"]["name"] for tool in kwargs["tools"]] == ["get_my_credit_limits"]
            return SimpleNamespace(choices=[SimpleNamespace(message=ModelMessage(tool_calls=[call]))])

    completions = FakeCompletions()

    class FakeClient:
        chat = SimpleNamespace(completions=completions)

        async def close(self):
            return None

    monkeypatch.setattr(llm_lesson_service, "AsyncOpenAI", lambda **kwargs: FakeClient())
    result = asyncio.run(llm_lesson_service.answer_banking_chat(
        "Tell me about my credit limit", Settings(), demo_db, "CUST-1001"
    ))
    assert result["answer"] == "Standard card: current credit limit EUR 3,000.00."
    assert completions.count == 1


def test_current_limit_question_only_offers_credit_limit_tool():
    assert llm_lesson_service._tools_for_message("Tell me about my credit limit") == ["get_my_credit_limits"]


def test_compound_question_only_offers_asked_tools():
    assert llm_lesson_service._tools_for_message("Total balance and Loans?") == ["get_my_accounts", "get_my_loans"]


def test_name_question_only_offers_profile_tool():
    assert llm_lesson_service._tools_for_message("My name?") == ["get_my_profile"]


def test_ai_chat_withholds_unverified_balance_answer(monkeypatch, demo_db):
    class FakeCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=ModelMessage(content="You have EUR 1,000."))])

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

        async def close(self):
            return None

    monkeypatch.setattr(llm_lesson_service, "AsyncOpenAI", lambda **kwargs: FakeClient())
    result = asyncio.run(llm_lesson_service.answer_banking_chat(
        "What is my balance?", Settings(), demo_db, "CUST-1001"
    ))
    assert "couldn’t verify" in result["answer"]
    assert any("withheld unverified model answer" in step for step in result["steps"])


def test_warmup_failure_is_nonfatal(monkeypatch):
    class FakeClient:
        responses = SimpleNamespace(create=None)

        def __init__(self):
            async def fail(**kwargs):
                raise RuntimeError("Ollama is offline")
            self.responses.create = fail

        async def close(self):
            return None

    monkeypatch.setattr(llm_lesson_service, "AsyncOpenAI", lambda **kwargs: FakeClient())
    assert asyncio.run(llm_lesson_service.warm_up_model(Settings())) is False
