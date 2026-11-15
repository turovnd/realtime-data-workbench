from pathlib import Path

import pytest
from pydantic import ValidationError

from workbench.settings import Settings


@pytest.fixture(autouse=True)
def isolated_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)


def test_call_budget_defaults_remain_finite_and_do_not_enable_live_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WORKBENCH_LIVE_CALL_BUDGET", raising=False)
    monkeypatch.delenv("WORKBENCH_OPENROUTER_CALLS_ENABLED", raising=False)
    settings = Settings()
    assert settings.live_call_budget == 3
    assert settings.openrouter_calls_enabled is False


@pytest.mark.parametrize(
    "value,expected", [("0", 0), ("20", 20), ("100", 100), ("unlimited", None)]
)
def test_call_budget_reads_an_explicit_unlimited_environment_value(
    monkeypatch: pytest.MonkeyPatch, value: str, expected: int | None
) -> None:
    monkeypatch.setenv("WORKBENCH_LIVE_CALL_BUDGET", value)
    assert Settings().live_call_budget == expected


@pytest.mark.parametrize("value", ["-1", "101", "none", "null", "", "unlimted"])
def test_invalid_call_budget_values_are_not_silently_treated_as_unlimited(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("WORKBENCH_LIVE_CALL_BUDGET", value)
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    "mode,provider,model,tokens,enabled",
    [
        ("deterministic", "deterministic-rules/1", None, 0, False),
        ("openrouter", "openrouter/selected/model", "selected/model", 450, True),
        ("deepseek", "deepseek/deepseek-flash", "deepseek-flash", 650, True),
    ],
)
def test_selected_provider_owns_enablement_and_model_configuration(
    mode: str,
    provider: str,
    model: str | None,
    tokens: int,
    enabled: bool,
) -> None:
    settings = Settings.model_validate(
        {
            "provider_mode": mode,
            "openrouter_model": "selected/model",
            "openrouter_max_tokens": 450,
            "openrouter_calls_enabled": True,
            "deepseek_max_tokens": 650,
            "deepseek_calls_enabled": True,
        }
    )
    assert settings.provider_id == provider
    assert settings.live_model == model
    assert settings.live_max_tokens == tokens
    assert settings.live_calls_enabled is enabled
    assert settings.live_api_key is None


def test_other_provider_enablement_does_not_enable_selected_provider() -> None:
    settings = Settings(provider_mode="deepseek", openrouter_calls_enabled=True)
    assert not settings.live_calls_enabled
    assert settings.provider_id == "deepseek/deepseek-flash"
