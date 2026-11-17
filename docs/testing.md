# Tests

Tests live with their application and mirror source ownership. Automated tests use controlled provider responses; they do not spend model credits.

## Frontend

From the repository root:

```sh
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm api:check
pnpm test:e2e
```

Unit tests cover API boundaries, session races, cursor views and provider provenance. Browser preview tests cover routes, keyboard navigation and offline behavior. For the connected suite, start the local Docker stack and run:

```sh
VITE_API_URL=http://127.0.0.1:8002 PLAYWRIGHT_START_WEB=1 pnpm test:connected
```

Connected tests include real API/workspace checks and controlled-response cases for failures, progress and recovery. Traces are written to `frontend/test-results/`.

## Backend

Use a disposable PostgreSQL database: these tests truncate application tables.

```sh
uv run --directory backend ruff check common modules tests migrations tools
uv run --directory backend ruff format --check common modules tests migrations tools
uv run --directory backend mypy
TEST_DATABASE_URL=postgresql+asyncpg://user:password@127.0.0.1:5432/disposable uv run --directory backend pytest -q
```

Database tests cover idempotent input, concurrent admission, lease expiry, stale completion, immutable history, cursor isolation and migration/adoption. Transport tests cover provider errors, deadlines, output bounds and exact evidence validation.

The demo corpus test checks unique messages, useful compression, exact quotes and parity between the backend and browser preview data.

## Real AI

Open a fresh demo, compare a detailed message with its sample takeaway, then run one real AI analysis. Follow progress, verify the source quotes, inspect the same run in Activity, and reload. Also check pagination and retry after a failed update.

A passing automated suite does not establish model quality or hosted provider access. Real-model checks are separate, bounded and recorded in [AI evaluation](ai-evaluation.md). GitHub Actions runs the frontend, backend and Docker/browser checks on each code change.
