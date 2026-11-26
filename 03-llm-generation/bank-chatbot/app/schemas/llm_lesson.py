from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class LLMMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatHistoryTurn] = Field(default_factory=list, max_length=10)
    mode: Literal["lesson", "banking_chat"] = "lesson"


class LLMMessageResponse(BaseModel):
    answer: str
    model: str
    steps: list[str]
    action: dict | None = None
