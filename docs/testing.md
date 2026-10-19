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
uv run --directory backend ruff check src tests ../tools
uv run --directory backend ruff format --check src tests ../tools
uv run --directory backend mypy
uv run --directory backend pytest -m 'not integration'
```

Set `TEST_DATABASE_URL` to a **disposable real PostgreSQL database** for `uv run --directory backend pytest`. Fixtures truncate application tables. Skipped integration tests do not prove database behavior.

Controlled Activity/analysis browser tests intercept API and auth; run only those specs when testing against a live-provider development configuration. They make no provider calls.

With the isolated Docker API/worker/database running, use `VITE_API_URL=http://127.0.0.1:8002 PLAYWRIGHT_START_WEB=1 pnpm test:connected`. Never use a deployed database for automated cleanup.

## Acceptance scope

- Frontend: auth races, filters, selection, pagination, direct routes, loading/error/empty/recovery states, keyboard/focus, mobile layout, offline read-only behavior and Activity automatic/manual/grouped run discovery, status transitions, exact result expansion, pagination, cursor recovery and session isolation.
- HTTP and contracts: generated-client compatibility, strict request/response models, workspace isolation and guarded mutations.
- PostgreSQL/worker: immutable input, idempotency, bounded claims, stale-worker fences, crash recovery, retries, cancellation, retained runs and fixed-selection backfill; analysis beyond ten runs, optional unlimited cumulative counting, independently bounded response histories and Activity’s 6,000-item read window.
- Provider: validated structured output and exact source quotes, including Unicode/JSON escaping, rejected translations and punctuation changes, bounded schema limits, safe diagnostics and no automatic retries on invalid output. Normal checks use deterministic or intercepted providers.

Record actual results for this source revision in [delivery status](delivery-status.md). Earlier test counts and screenshots do not establish that a new refactor passes. Hosted CI and deployment remain separate from local verification.

## Live-provider smoke

Keep automated regression tests on isolated deterministic or mocked providers. A separately authorized live smoke may submit two or three bounded synthetic messages through the API, wait for their real worker results and verify OpenRouter provenance and exact evidence against the source. Record the persisted call counter before and after; retries also increment the counter and consume any configured finite ceiling. Do not enable a live worker against an uninspected backlog or reset the usage counter to make a test pass.

HTTP 402, 401, 429, server errors, invalid output and disabled configuration are tested without paid calls. An accepted analysis request does not count as successful model output; live evidence must include the completed persisted result.
