from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKBENCH_", env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://workbench:workbench@127.0.0.1:15433/workbench"
    allowed_origins: list[str] = ["http://localhost:5174", "http://127.0.0.1:5174"]
    lease_seconds: int = 30
    provider_timeout_seconds: float = 10

    provider_mode: Literal["deterministic", "openrouter"] = "deterministic"
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_api_key: SecretStr | None = None
    openrouter_max_tokens: int = Field(default=800, ge=100, le=1200)
    openrouter_calls_enabled: bool = False
    live_call_budget: int = Field(default=3, ge=0, le=100)

    @property
    def provider_id(self) -> str:
        return (
            f"openrouter/{self.openrouter_model}"
            if self.provider_mode == "openrouter"
            else "deterministic-rules/1"
        )
