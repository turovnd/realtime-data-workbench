"""Compose the worker's allowed generators from deployment settings."""

import httpx

from workbench.infrastructure.deterministic import generate_demo
from workbench.infrastructure.openrouter import OpenRouterClient
from workbench.logic.enrichment import FeedbackGenerator, Generate
from workbench.logic.errors import TerminalProviderError
from workbench.settings import Settings


def openrouter_generator(settings: Settings, client: httpx.AsyncClient) -> FeedbackGenerator:
    if not settings.openrouter_calls_enabled or not settings.openrouter_api_key:
        raise TerminalProviderError("Live provider calls are disabled or not configured")
    return FeedbackGenerator(
        OpenRouterClient(
            client,
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            timeout_seconds=settings.provider_timeout_seconds,
            max_tokens=settings.openrouter_max_tokens,
        )
    )


def build_generators(settings: Settings, client: httpx.AsyncClient) -> dict[str, Generate]:
    generators: dict[str, Generate] = {"deterministic-rules/1": generate_demo}
    if settings.openrouter_calls_enabled and settings.openrouter_api_key:
        generators[f"openrouter/{settings.openrouter_model}"] = openrouter_generator(
            settings, client
        )
    return generators
