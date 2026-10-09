from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Config = Literal["v1", "v2"]


Topic = Literal["reliability", "usability", "billing", "performance", "other"]


Status = Literal["queued", "leased", "succeeded", "failed", "cancelled"]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class EmptyRequest(StrictModel):
    """An explicit empty JSON request body."""


class ErrorResponse(StrictModel):
    detail: str = Field(
        description="Safe explanation; never includes credentials or provider bodies"
    )


class OkResponse(StrictModel):
    ok: bool = True


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    provider: str = Field(description="Configured provider identifier, not a secret")
