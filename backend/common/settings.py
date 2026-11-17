from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WORKBENCH_", env_file=".env", extra="ignore", populate_by_name=True
    )
    database_url: str = "postgresql+asyncpg://workbench:workbench@127.0.0.1:15433/workbench"
    migration_database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "WORKBENCH_MIGRATION_DATABASE_URL", "WORKBENCH_DATABASE_URL_UNPOOLED"
        ),
    )
    allowed_origins: list[str] = ["http://localhost:5174", "http://127.0.0.1:5174"]
    lease_seconds: int = 30
    provider_timeout_seconds: float = 10
    queue_enabled: bool = False
    queue_region: str = "iad1"

    provider_mode: Literal["deterministic", "openrouter"] = "deterministic"
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_api_key: SecretStr | None = None
    openrouter_max_tokens: int = Field(default=800, ge=100, le=1200)
    openrouter_calls_enabled: bool = False
    live_call_budget: int | None = Field(default=3, ge=0, le=100)

    @field_validator("live_call_budget", mode="before")
    @classmethod
    def unlimited_call_budget(cls, value: object) -> object:
        return None if value == "unlimited" else value

    @property
    def live_model(self) -> str | None:
        if self.provider_mode == "openrouter":
            return self.openrouter_model
        return None

    @property
    def provider_id(self) -> str:
        model = self.live_model
        return f"{self.provider_mode}/{model}" if model is not None else "deterministic-rules/1"

    @property
    def live_calls_enabled(self) -> bool:
        if self.provider_mode == "openrouter":
            return self.openrouter_calls_enabled
        return False

    @property
    def live_api_key(self) -> SecretStr | None:
        if self.provider_mode == "openrouter":
            return self.openrouter_api_key
        return None

    @property
    def live_max_tokens(self) -> int:
        if self.provider_mode == "openrouter":
            return self.openrouter_max_tokens
        return 0
