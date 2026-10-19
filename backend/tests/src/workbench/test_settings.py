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
