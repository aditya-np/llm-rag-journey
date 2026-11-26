from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.accounts import router as accounts_router
from app.api.auth import router as auth_router
from app.api.cards import router as cards_router
from app.api.faqs import router as faqs_router
from app.api.llm_lesson import router as llm_lesson_router
from app.api.loans import router as loans_router
from app.api.recurring_payments import router as recurring_payments_router
from app.config import get_settings
from app.db.database import connect, initialize
from app.db.seed import seed_demo_data
from app.services.llm_lesson_service import warm_up_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    connection = connect(settings.database_url)
    initialize(connection)
    seed_demo_data(connection)
    app.state.db = connection
    app.state.db_lock = Lock()
    await warm_up_model(settings)
    try:
        yield
    finally:
        connection.close()


app = FastAPI(
    title="Smart Banking Backend",
    description=(
        "A learning backend with deterministic banking routes, an AI chat mode with a bounded "
        "allow-listed tool loop, and a plain LLM lesson mode. No agent framework or RAG is used. "
        "Demo data and rules only."
    ),
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(loans_router)
app.include_router(cards_router)
app.include_router(recurring_payments_router)
app.include_router(faqs_router)
app.include_router(llm_lesson_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")

