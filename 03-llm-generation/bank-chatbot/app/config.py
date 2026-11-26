from functools import lru_cache
import json

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Banking Backend"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/banking.sqlite3"
    self_service_limit_increase_max: int = Field(default=1000, ge=0)
    llm_api_key: SecretStr = SecretStr("ollama")
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen3.5:0.8b"
    llm_timeout_seconds: int = Field(default=120, ge=10, le=600)
    llm_warmup_enabled: bool = True
    llm_warmup_timeout_seconds: int = Field(default=45, ge=5, le=180)
    # Demo-only authentication. Replace with verified identity before real use.
    demo_tokens_json: str = '{}'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def demo_tokens(self) -> dict[str, str]:
        try:
            parsed = json.loads(self.demo_tokens_json)
        except json.JSONDecodeError as exc:
            raise ValueError("DEMO_TOKENS_JSON must be valid JSON") from exc
        if not isinstance(parsed, dict) or not all(
            isinstance(token, str) and isinstance(customer_id, str)
            for token, customer_id in parsed.items()
        ):
            raise ValueError("DEMO_TOKENS_JSON must map string tokens to customer IDs")
        # Keep the extra test profiles available even when .env only overrides
        # the original demo identities.
        defaults = {"demo-token-alex": "CUST-1001", "demo-token-jamie": "CUST-1002"}
        defaults.update({f"demo-token-customer-{number}": f"CUST-{number}" for number in range(1003, 1053)})
        defaults.update(parsed)
        return defaults


@lru_cache
def get_settings() -> Settings:
    return Settings()

