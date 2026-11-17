"""Typed generation boundary and the OpenRouter response envelope."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from common.schemas.enrichment import MAX_GENERATED_TEXT_LENGTH


@dataclass(frozen=True)
class GenerationRequest:
    instructions: str
    source: str
    schema_name: str
    output_schema: dict[str, Any]


@dataclass(frozen=True)
class GenerationResult:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class Message(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str = Field(max_length=MAX_GENERATED_TEXT_LENGTH)


class Choice(BaseModel):
    model_config = ConfigDict(strict=True)
    message: Message
    finish_reason: str


class TokenUsage(BaseModel):
    model_config = ConfigDict(strict=True)
    prompt_tokens: int | None = Field(default=None, ge=0, le=10_000_000)
    completion_tokens: int | None = Field(default=None, ge=0, le=10_000_000)


class Completion(BaseModel):
    model_config = ConfigDict(strict=True)
    choices: list[Choice] = Field(min_length=1, max_length=1)
    usage: TokenUsage | None = None
