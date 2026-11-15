"""Compose only the selected live provider; queued jobs are never silently rerouted."""

import httpx

from workbench.infrastructure.deepseek import DeepSeekClient
from workbench.infrastructure.deterministic import generate_demo
from workbench.infrastructure.openrouter import OpenRouterClient
from workbench.logic.enrichment import FeedbackGenerator, Generate, ModelClient
from workbench.logic.errors import TerminalProviderError
from workbench.settings import Settings


def build_model_client(
    settings: Settings, client: httpx.AsyncClient, *, max_tokens: int | None = None
) -> ModelClient:
    key = settings.live_api_key
    model = settings.live_model
    if not settings.live_calls_enabled or not key or not key.get_secret_value() or model is None:
        raise TerminalProviderError("Live provider calls are disabled or not configured")
    tokens = (
        settings.live_max_tokens
        if max_tokens is None
        else min(settings.live_max_tokens, max_tokens)
    )
    if settings.provider_mode == "deepseek":
        return DeepSeekClient(
            client,
            api_key=key,
            model=model,
            timeout_seconds=settings.provider_timeout_seconds,
            max_tokens=tokens,
        )
    return OpenRouterClient(
        client,
        api_key=key,
        model=model,
        timeout_seconds=settings.provider_timeout_seconds,
        max_tokens=tokens,
    )


def openrouter_generator(settings: Settings, client: httpx.AsyncClient) -> FeedbackGenerator:
    """Explicit OpenRouter composition retained for callers of the original adapter."""
    if settings.provider_mode != "openrouter":
        raise TerminalProviderError("OpenRouter is not the selected provider")
    return FeedbackGenerator(build_model_client(settings, client))


def build_generators(settings: Settings, client: httpx.AsyncClient) -> dict[str, Generate]:
    generators: dict[str, Generate] = {"deterministic-rules/1": generate_demo}
    key = settings.live_api_key
    if settings.live_calls_enabled and key and key.get_secret_value():
        generators[settings.provider_id] = FeedbackGenerator(build_model_client(settings, client))
    return generators
