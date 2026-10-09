# Feedback Desk · Realtime Data Workbench

A product feedback desk with independent accounts, an isolated demo, incoming synthetic feedback, structured topic/intent/summary results, source evidence and versioned reprocessing. React runs on Vercel; FastAPI, the durable Python worker and PostgreSQL run in a separate Docker stack.

This is a new AI-assisted reference implementation using synthetic data. It does not reuse client code or claim production scale. The backend has been deployed to the owner's Yandex Cloud server and its public HTTPS/API workflow was verified on 2026-10-10. The Vercel UI has not been deployed and no public UI URL is verified. See [the implementation record](docs/implementation-status.md).

## Run the complete app locally

Requires Docker Compose v2. This repository has its own network, database, credentials and volume; it does not depend on the other portfolio application.

```sh
cp .env.example .env
# Replace POSTGRES_PASSWORD with a random URL-safe password.
docker compose --profile local-web up --build -d
```

Open `http://127.0.0.1:8082`. Create an account, or choose **Try an isolated demo** for a new workspace with 24 synthetic messages. Account workspaces start empty; **Add 12 live records** creates a finite batch. PostgreSQL and the worker have no public ports; the API binds loopback port 8002. The optional local web container proxies to its own API. Production UI deployment uses Vercel instead of that container.

For frontend development, use Node 24 and pnpm 11.20.0:

```sh
cd web
pnpm install --frozen-lockfile
VITE_API_URL=http://127.0.0.1:8002 pnpm dev
```

Open `http://127.0.0.1:5174`. Without `VITE_API_URL`, the UI offers a clearly labelled **deterministic browser demo**; account sign-in is disabled. That fixture makes no API/model calls and resets on reload. Two seeded fixture failures make retry easy to inspect; the server does not invent provider failures.

## Explore the workflow

1. Browse feedback with search, topic and status filters in the URL. Scrolling loads the next page automatically; **Load more feedback** is also keyboard accessible.
2. Open a record to inspect the original message, topic, intent, summary, exact evidence quotes, provider and version history.
3. Select up to 100 records across pages and filters. Run v2 on that fixed selection, track progress, stop unfinished work, or retry an eligible failed version.
4. Existing pages stay stable when messages arrive or processing status changes. **Show new feedback** / **Refresh view** opens a current view without losing the selection.
5. Save the currently loaded records for offline, read-only inspection. Logout revokes the session and clears private query/snapshot data.

The UI uses official shadcn Radix components and preset [b1Ymqvgiu](https://ui.shadcn.com/create?preset=b1Ymqvgiu): Nova, Neutral, Blue/chartBlue, Inter and Lucide. Domain features, hooks, API contracts and generated components are separate modules.

## Authentication and pagination

Email/password accounts are local to this app. Argon2id hashes use bounded memory and two concurrent hash slots. Opaque 24-hour bearer sessions are hashed in PostgreSQL, revocable, workspace scoped, and stored in browser session storage. Login/demo admission has persisted per-IP limits; login/register also have per-email limits. Exact CORS origins are separate from authentication. There is no OAuth, email verification, password reset, organization or role management in this slice.

`GET /api/feedback` accepts `q`, `topic`, `status`, `limit` (1–50), and an opaque cursor. The server freezes matching IDs in a bounded view, then uses descending sequence keyset queries with SQL `LIMIT`; it only hydrates one page. Cursors are signed and bound to the workspace and filters. Invalid/tampered/mismatched cursors return 400; retained expired views return 410. Evicted views also require a visible refresh. Views expire after ten minutes and are capped at 20 per workspace. TanStack Infinite Query refreshes the same view; explicit refresh opens a new one. Processing updates use three-second polling, not SSE.

## Durable processing and providers

Inputs and jobs commit together. Duplicate input identities are idempotent; conflicting content is rejected. PostgreSQL protects immutable input/result rows. The separate worker claims expiring leases, performs provider work outside the transaction, and uses fencing to reject stale/cancelled completions. Unique `(record, config)` keys prevent duplicate stored versions. v1/v2 are fixed processing configurations; reusing a configuration is idempotent, including after an operator changes the default provider.

Backfill freezes at most 100 IDs and atomically enqueues the whole bounded selection. Persisted per-job status supplies restart checkpoints. At most two leases are admitted globally, each job has three lifetime attempts, provider work has a ten-second deadline and leases last thirty seconds. Stored-effect idempotency does not guarantee exactly-once provider calls or charges.

Deterministic rules are the default. The OpenRouter adapter uses `openai/gpt-4.1-mini`, strict structured JSON, required provider parameters, `data_collection: deny`, local Pydantic validation and exact source evidence checks. It bounds input, response size, output tokens, timeouts, retries and a durable global call budget. Disabled/unavailable/invalid provider calls remain visible failures; there is no silent fallback. Live processing needs explicit server-only settings; demo startup is always deterministic. No model key belongs in `VITE_*` values. See [operations](docs/operations.md) for the opt-in controls.

## Verification

```sh
cd web
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm exec playwright install chromium
pnpm test:e2e
pnpm build
# With the connected dev UI and Docker API/worker/DB already running:
pnpm test:connected
```

```sh
cd backend
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -m 'not integration'
TEST_DATABASE_URL=postgresql+asyncpg://workbench:workbench@127.0.0.1:15433/workbench uv run pytest
```

`TEST_DATABASE_URL` must point to a **disposable real PostgreSQL database**: integration fixtures truncate this application's tables. Never use the running app's database for those tests. Integration tests explicitly skip when the variable is absent.

[GitHub Actions](.github/workflows/ci.yml) defines static checks, unit tests, real PostgreSQL tests, browser preview tests, image building and connected browser journeys against Compose. The release workflow only packages an image artifact; it does not deploy remotely. Remote CI has not run because this repository has not been published.

## Boundaries and further work

Resources are capped at 500 records/workspace, 5,000 records globally and 1,000 workspaces. Temporary demo data expires after 24 hours; bounded cleanup excludes account workspaces. One PostgreSQL advisory lock deliberately serializes demo writes/view creation. This favors simple correctness at bounded size, not throughput. No Kafka, Redis, managed queues, SSE, quality benchmark or high availability is claimed.

- [Implementation record and actual checks](docs/implementation-status.md)
- [Hybrid deployment and proxy configuration](docs/hybrid-deployment.md)
- [Operations and recovery](docs/operations.md)
- [Historical contract plan](docs/implementation-plan.md)
- [Original style checkpoint and preserved samples](docs/style-checkpoint.md)
