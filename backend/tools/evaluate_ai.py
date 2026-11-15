"""Run a small, explicit live evaluation using the production prompt and validator."""

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

import httpx
from pydantic import Field, TypeAdapter

from workbench.infrastructure.deepseek import system_instructions
from workbench.logic.enrichment import ModelClient, enrich
from workbench.logic.errors import RetryableProviderError, TerminalProviderError
from workbench.logic.prompts import feedback_request
from workbench.schemas.common import Config, StrictModel, Topic
from workbench.schemas.enrichment import Enrichment
from workbench.schemas.feedback import MAX_FEEDBACK_LENGTH
from workbench.schemas.providers import GenerationResult
from workbench.settings import Settings
from workbench.workers.providers import build_model_client

MAX_CASES = 6
MAX_TOKENS = 800
DEFAULT_CASES = Path(__file__).resolve().parents[1] / "evaluation" / "cases.json"


class EvaluationCase(StrictModel):
    id: str = Field(min_length=1)
    config: Config
    text: str = Field(min_length=1, max_length=MAX_FEEDBACK_LENGTH)
    topics: list[Topic] = Field(min_length=1)
    intents: list[str] = Field(min_length=1)
    forbidden_summary_terms: list[str]
    review_criteria: list[str] = Field(min_length=1)


class CaseResult(StrictModel):
    id: str
    config: Config
    instructions_sha256: str
    instructions: str
    elapsed_ms: int
    output: Enrichment | None = None
    checks: dict[str, bool] = Field(default_factory=dict)
    failure: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    review_criteria: list[str]
    qualitative_review: str | None = None


class EvaluationReport(StrictModel):
    started_at: str
    model: str
    provider: str
    cases_sha256: str
    max_output_tokens: int
    request_count: int = 0
    retries_per_case: int = 0
    scope: str = (
        "Small synthetic regression sample, not a classification-accuracy benchmark. "
        "Automated checks cover schema, source quotes and declared labels. "
        "Semantic usefulness and unsupported claims require qualitative review. "
        "Requests use the production transport, prompt and validator directly; "
        "they do not exercise the database, worker or application usage counter."
    )
    results: list[CaseResult] = Field(default_factory=list)


def load_cases(path: Path) -> list[EvaluationCase]:
    cases = TypeAdapter(list[EvaluationCase]).validate_json(path.read_bytes())
    if not 1 <= len(cases) <= MAX_CASES:
        raise ValueError(f"Choose between one and {MAX_CASES} cases")
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Case IDs must be unique")
    return cases


async def evaluate_case(client: ModelClient, case: EvaluationCase, provider: str) -> CaseResult:
    started = monotonic()
    request = feedback_request(case.text, case.config)
    instructions = system_instructions(request) if provider == "deepseek" else request.instructions
    result = CaseResult(
        id=case.id,
        config=case.config,
        instructions_sha256=hashlib.sha256(instructions.encode()).hexdigest(),
        instructions=instructions,
        elapsed_ms=0,
        review_criteria=case.review_criteria,
    )
    completion: GenerationResult | None = None

    async def generate(source: str, config: Config) -> str:
        nonlocal completion
        completion = await client.complete(feedback_request(source, config))
        return completion.content

    try:
        output = await enrich(case.text, case.config, generate=generate)
        result.output = output
        result.checks = {
            "schema_and_exact_source_quotes": True,
            "expected_topic": output.topic in case.topics,
            "expected_intent": output.intent in case.intents,
            "no_forbidden_summary_terms": not any(
                term.casefold() in output.summary.casefold()
                for term in case.forbidden_summary_terms
            ),
        }
    except (RetryableProviderError, TerminalProviderError) as exc:
        result.failure = str(exc)
        result.checks = {"schema_and_exact_source_quotes": False}
    finally:
        result.elapsed_ms = round((monotonic() - started) * 1000)
        if completion is not None:
            result.prompt_tokens = completion.prompt_tokens
            result.completion_tokens = completion.completion_tokens
    return result


async def evaluate(settings: Settings, cases_path: Path, output_path: Path) -> bool:
    cases = await asyncio.to_thread(load_cases, cases_path)
    if not settings.live_calls_enabled or not settings.live_api_key or settings.live_model is None:
        raise ValueError("Enable the selected server-side provider before a live evaluation")
    report = EvaluationReport(
        started_at=datetime.now(UTC).isoformat(),
        model=settings.live_model,
        provider=settings.provider_mode,
        cases_sha256=hashlib.sha256(await asyncio.to_thread(cases_path.read_bytes)).hexdigest(),
        max_output_tokens=min(settings.live_max_tokens, MAX_TOKENS),
    )
    await asyncio.to_thread(output_path.parent.mkdir, parents=True, exist_ok=True)

    async with httpx.AsyncClient() as transport:
        client = build_model_client(settings, transport, max_tokens=report.max_output_tokens)
        for case in cases:
            report.request_count += 1
            result = await evaluate_case(client, case, settings.provider_mode)
            report.results.append(result)
            await asyncio.to_thread(output_path.write_text, report.model_dump_json(indent=2) + "\n")
            outcome = "passed" if all(result.checks.values()) else "failed"
            print(json.dumps({"case": case.id, "checks": outcome, "elapsed_ms": result.elapsed_ms}))

    return all(all(result.checks.values()) for result in report.results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Authorize at most six paid requests")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error(
            "Pass --live explicitly; this command sends synthetic inputs to the selected provider"
        )
    settings = Settings()
    try:
        passed = asyncio.run(evaluate(settings, args.cases, args.output))
    except ValueError as exc:
        parser.error(str(exc))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
