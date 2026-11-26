from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.core.security import current_customer_id
from app.db.database import connect
from app.schemas.llm_lesson import LLMMessageRequest, LLMMessageResponse
from app.services.llm_lesson_service import answer_banking_chat, answer_without_tools

router = APIRouter(prefix="/v1/learning", tags=["LLM learning"])


@router.post("/llm", response_model=LLMMessageResponse)
async def ask_model_without_tools(
    payload: LLMMessageRequest,
    customer_id: Annotated[str, Depends(current_customer_id)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Keep the lesson mode and optionally enable authenticated banking tools."""
    history = [turn.model_dump() for turn in payload.history]
    if payload.mode == "banking_chat":
        # Do not hold the dashboard's shared SQLite lock while the model runs.
        connection = connect(settings.database_url)
        try:
            return await answer_banking_chat(payload.message, settings, connection, customer_id, history)
        finally:
            connection.close()
    return await answer_without_tools(
        payload.message,
        settings,
        history,
    )
