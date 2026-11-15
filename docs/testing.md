# Testing and verification

Frontend tests live in `frontend/tests/`; backend tests live in `backend/tests/`. Each tree mirrors its source owner. Browser journeys are in `frontend/tests/src/pages`. Keep fixtures near their test owner and do not duplicate suites inside production source.

## Local commands

From the repository root:

```sh
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e
uv sync --directory backend --frozen
pnpm api:check
uv run --directory backend ruff check src tests migrations tools ../tools
uv run --directory backend ruff format --check src tests migrations tools ../tools
uv run --directory backend mypy
uv run --directory backend pytest -m 'not integration'
```

Set `TEST_DATABASE_URL` to a **disposable real PostgreSQL database** for `uv run --directory backend pytest`. Fixtures truncate application tables. Skipped integration tests do not prove database behavior.

Controlled Activity/analysis browser tests intercept API and auth; run only those specs when testing against a live-provider development configuration. They make no provider calls.

With the isolated Docker API/worker/database running, use `VITE_API_URL=http://127.0.0.1:8002 PLAYWRIGHT_START_WEB=1 pnpm test:connected`. Never use a deployed database for automated cleanup.

## Acceptance scope

- Frontend: auth races, filters, selection, pagination, direct routes, loading/error/empty/recovery states, keyboard/focus, mobile layout, lazy-route loading/error recovery, offline reload with cached page chunks, offline read-only behavior and Activity automatic/manual/grouped run discovery, status transitions, exact result expansion, pagination, cursor recovery and session isolation.
- HTTP and contracts: generated-client compatibility, strict request/response models, workspace isolation and guarded mutations.
- PostgreSQL/worker: immutable input, idempotency, bounded claims, stale-worker fences, crash recovery, retries, cancellation, retained runs and fixed-selection backfill; analysis beyond ten runs, optional unlimited cumulative counting, independently bounded response histories and Activity’s 6,000-item read window.
- Migrations: fresh install, known unversioned adoption, older-schema upgrade, preservation of complete rows and usage counters, unknown-schema rejection, safe downgrade guards, and zero Alembic metadata differences. Session tests verify commit, rollback and detached attribute access.
- Provider: validated structured output and exact source quotes, including Unicode/JSON escaping, rejected translations and punctuation changes, bounded schema limits, safe diagnostics and no automatic retries on invalid output. Normal checks use explicitly configured deterministic or intercepted providers. A live job with no matching configured provider must fail without a synthetic fallback or paid reservation.

Record actual results for this source revision in [delivery status](delivery-status.md). Earlier test counts and screenshots do not establish that a new refactor passes. Hosted CI and deployment remain separate from local verification.

## Live-provider smoke

Keep automated regression tests on isolated deterministic or mocked providers. A separately authorized live smoke may submit two or three bounded synthetic messages through the API, wait for their real worker results and verify the selected provider/model and exact evidence against the source. Record persisted call counters before and after; retries also increment the selected provider's counter and consume the shared finite ceiling when configured. Do not enable a live worker against an uninspected backlog or reset usage counters to make a test pass.

HTTP 402, 401, 429, server errors, invalid output and disabled configuration are tested without paid calls. An accepted analysis request does not count as successful model output; live evidence must include the completed persisted result.

## Small real-model evaluation

`backend/evaluation/cases.json` fixes four synthetic cases: the guided monthly-export example, an ambiguous observation, a billing message in Russian and a message containing an injected instruction. Each case states allowed labels and semantic review criteria before the call.

From the repository root, with the ignored server-side environment configured:

```sh
uv run --project backend python backend/tools/evaluate_ai.py --live --output .local/ai-evaluation.json
```

This command makes one real request per case to the selected, explicitly enabled provider, up to six cases, with no retries and at most 800 output tokens per request. It uses the production prompt, transport and output validator directly. It does not test the worker or database, and it does not increment the application's durable usage counters. Keep it outside normal CI. Use a distinct output filename when evaluating another provider so the earlier evidence remains attributable to its original model.

The report records the case and instruction hashes, model, request count, latency, tokens when available, structured outputs and automatic checks. Exact quotes and allowed labels are machine-checked. Summary usefulness, unsupported claims and treatment of uncertainty require a separate qualitative review. Record who performed that review; an AI-assisted review is not independent human validation. Four passing examples are not an accuracy benchmark or evidence of time saved for customers. The full browser-to-worker smoke is a separate check.
