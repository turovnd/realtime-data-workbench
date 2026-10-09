# Testing and verification

All application tests live under root `tests/`: Python tests mirror `backend/src/workbench`, frontend units mirror `web/src`, and browser journeys live under `tests/web/src/pages`. Keep fixtures and helpers near the shared test ancestor; do not duplicate suites inside production source folders.

## Commands

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
uv run --directory backend ruff check src ../tests/backend ../tools
uv run --directory backend ruff format --check src ../tests/backend ../tools
uv run --directory backend mypy
uv run --directory backend pytest -m 'not integration'
```

Set `TEST_DATABASE_URL` to a **disposable real PostgreSQL database** before running integration tests with `uv run --directory backend pytest`. Fixtures truncate application tables. Missing connection configuration skips integration tests and is not a passing database check.

With the real Docker API/worker/DB running, `VITE_API_URL=http://127.0.0.1:8002 PLAYWRIGHT_START_WEB=1 pnpm test:connected` starts the connected web test server. Never reuse the deployed database for automated cleanup.

The current command matrix passed locally; counts and scope are recorded in [delivery status](delivery-status.md).

## Coverage responsibilities

| Layer                 | Behavior                                                                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Domain/provider units | Strict structured output, invalid/oversized data, exact evidence and explicit provider failure.                                                         |
| Auth/client units     | Delayed 401, login/logout race and fixture session isolation.                                                                                           |
| Real PostgreSQL       | Immutable/idempotent ingestion, unique/fenced claims, recovery, retry budget, cancellation, fixed-selection backfill and persistent provider admission. |
| Feed/auth PostgreSQL  | Frozen membership, SQL keyset paging, foreign/tampered/expired cursors, retained view bounds, independent accounts and persisted admission.             |
| HTTP/OpenAPI          | Strict request/response contracts, bearer documentation, own Swagger assets and guarded mutations.                                                      |
| Browser fixture       | Filters, selection, automatic/manual paging, inspection, offline read-only reload and keyboard/mobile behavior.                                         |
| Connected browser     | Real account/session persistence, worker versions/backfill, stable paging during insertion and visible refresh after expiry.                            |

The browser fixture includes deliberate inspectable failures; the server does not fabricate provider failures. Runtime browser automation and manual keyboard checks complement screenshots. Hosted GitHub CI and automatic deployment are separate delivery evidence, tracked in [planning](../planning/README.md).
