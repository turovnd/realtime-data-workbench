# Local setup

## Complete Docker stack

Use Docker Compose v2. Preserve an existing `.env`; otherwise copy `.env.example` and replace the database password.

```sh
cp -n .env.example .env
docker compose --profile local-web up --build -d --wait
```

Open `http://127.0.0.1:8082`. The optional web container proxies `/api` to this app's API. The API is loopback-only on `8002`; PostgreSQL has no public port. The migration service must succeed before API/worker startup. For an existing unversioned database, follow the explicit adoption procedure below before running the normal stack update. Stop this project with `docker compose --profile local-web down`, without `-v` when preserving data.

## Frontend development

Use Node 24 and pnpm 11.20.0. The repository has one pnpm workspace and lockfile at the root; app scripts remain in `frontend/package.json`.

```sh
pnpm install --frozen-lockfile
VITE_API_URL=http://127.0.0.1:8002 pnpm --dir frontend dev
```

Open `http://127.0.0.1:5174`. Without `VITE_API_URL`, the app runs an explicitly labelled browser fixture and disables account sign-in. `VITE_API_URL=same-origin` is used by the local Docker web proxy and the hosted [Vercel Services configuration](vercel.md). The public UI, API and Swagger share [one origin](https://turovnd-feedback-desk.vercel.app); local development remains independent of Vercel and Neon.

## Regenerate the API client

```sh
pnpm api:generate
pnpm api:check
```

The check regenerates the two artifacts and fails if either differs from the saved version.

Generation exports the actual FastAPI schema to `openapi.json` and generates the fetch client in `frontend/src/api/generated.ts` with the pinned generator. It does not start the API or connect to PostgreSQL. Do not edit generated output manually. Python dependencies must already be installed with the following setup.

## Python development

Use the supported Python range and pinned dependencies from `backend/pyproject.toml` / `uv.lock`; Docker pins Python 3.13 and uv. Install from the root with `uv sync --directory backend --frozen`. Supply `WORKBENCH_DATABASE_URL` for an isolated PostgreSQL database. The app's Python settings load `.env` relative to the process working directory; the root Compose `.env` uses Compose variables, so do not assume it is interchangeable with native settings.

For a fresh database, apply Alembic migrations, then start API and worker in separate terminals:

```sh
uv run --directory backend alembic upgrade head
uv run --directory backend uvicorn workbench.api:app --host 127.0.0.1 --port 8002
uv run --directory backend python -m workbench.worker
```

The thin entrypoints delegate to the shared package layers. `python -m workbench.db` remains a compatibility entrypoint for the same Alembic upgrade, used by Compose. It does not contain schema mutation SQL.

### Existing unversioned database

An existing application database created before Alembic must be adopted once. First back up it and verify the operation against an isolated restore. Use the reviewed source/image, pause only this application's writers, and run:

```sh
uv run --directory backend alembic -x adopt=true upgrade head
uv run --directory backend alembic current
uv run --directory backend alembic check
```

Adoption validates the complete known schema and only then records its revision. Unknown tables, partial changes, missing columns, incompatible constraints or triggers cause a failure; investigate them rather than stamping manually. Normal `upgrade head` intentionally refuses a nonempty unversioned database. No command should delete an existing volume to make startup succeed.

### Author a schema change

```sh
uv run --directory backend alembic revision --autogenerate -m "describe the schema change"
uv run --directory backend alembic upgrade head
uv run --directory backend alembic check
uv run --directory backend alembic history
```

Review generated revisions before applying them. Data changes, PostgreSQL functions and immutable-record triggers need explicit migration code; autogeneration does not infer those policies. Frozen revisions do not import changing application models. See [testing](testing.md) for fresh-install, upgrade and data-preservation checks.

## Environment

| Setting                              | Meaning                                                                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `POSTGRES_PASSWORD`                  | Compose database credential; replace the example.                                                                   |
| `WORKBENCH_DATABASE_URL`             | Runtime PostgreSQL connection URL.                                                                                  |
| `WORKBENCH_MIGRATION_DATABASE_URL`   | Optional direct migration connection; falls back to Neon's `WORKBENCH_DATABASE_URL_UNPOOLED`, then the runtime URL. |
| `WORKBENCH_QUEUE_ENABLED`            | Enable Vercel publication; false for the local polling worker.                                                      |
| `WORKBENCH_QUEUE_REGION`             | Vercel queue region; default `iad1`.                                                                                |
| `WORKBENCH_IMAGE`                    | Versioned backend deployment image.                                                                                 |
| `WORKBENCH_ALLOWED_ORIGINS`          | JSON array of exact browser origins.                                                                                |
| `FORWARDED_ALLOW_IPS`                | Uvicorn's verified proxy peer; never `*`.                                                                           |
| `VITE_API_URL`                       | Public API origin or `same-origin` when frontend and API share routing.                                             |
| `WORKBENCH_PROVIDER_MODE`            | `deterministic` by default; explicit `openrouter` or `deepseek` opt-in.                                             |
| `WORKBENCH_OPENROUTER_CALLS_ENABLED` | Separate live-call switch, default false.                                                                           |
| `WORKBENCH_OPENROUTER_API_KEY`       | Server-side provider secret.                                                                                        |
| `WORKBENCH_OPENROUTER_MODEL`         | Baseline default `openai/gpt-4.1-mini`.                                                                             |
| `WORKBENCH_OPENROUTER_MAX_TOKENS`    | Default 800; bounded to 100–1,200.                                                                                  |
| `WORKBENCH_DEEPSEEK_CALLS_ENABLED`   | Separate DeepSeek live-call switch, default false.                                                                  |
| `WORKBENCH_DEEPSEEK_API_KEY`         | Server-side DeepSeek secret.                                                                                        |
| `WORKBENCH_DEEPSEEK_MODEL`           | Default `deepseek-flash`.                                                                                           |
| `WORKBENCH_DEEPSEEK_MAX_TOKENS`      | Default 800; bounded to 100–1,200.                                                                                  |
| `WORKBENCH_LIVE_CALL_BUDGET`         | Persisted attempt ceiling: default 3; 0–100, or `unlimited`.                                                        |

Live processing requires explicit enablement and either available durable budget or the explicit `unlimited` setting. Demo initialization deliberately uses deterministic jobs. Changing the default provider does not overwrite a record's existing immutable configuration result. No model secret belongs in a `VITE_*` value. See [workflows](workflows.md) and [limits](limits.md).

## Live analysis

The worker supports direct DeepSeek and OpenRouter through separate adapters. Select one provider for new work. Provider availability depends on the deployment network and account: an HTTP 401 from a public probe proves that the API is reachable, not that generation works. The [release ledger](delivery-status.md) records the actual deployed provider and its verification.

For direct DeepSeek, obtain an API key from the [official console](https://platform.deepseek.com/api_keys) and keep it in the ignored `.env` as `WORKBENCH_DEEPSEEK_API_KEY`. Configure:

```dotenv
WORKBENCH_PROVIDER_MODE=deepseek
WORKBENCH_DEEPSEEK_CALLS_ENABLED=true
WORKBENCH_DEEPSEEK_MODEL=deepseek-flash
WORKBENCH_DEEPSEEK_MAX_TOKENS=800
WORKBENCH_LIVE_CALL_BUDGET=unlimited
```

The adapter uses [DeepSeek Chat Completions](https://api-docs.deepseek.com/) with thinking disabled, a bounded output and [JSON-object mode](https://api-docs.deepseek.com/guides/json_mode/). It includes the domain schema in the system instructions. JSON-object mode does not enforce that schema at the provider; the application validates every field and every exact source quote before saving a result. Empty, truncated or invalid answers fail explicitly. No model response is replaced with a fixture.

OpenRouter remains available with `WORKBENCH_PROVIDER_MODE=openrouter`, `WORKBENCH_OPENROUTER_CALLS_ENABLED=true` and its own worker-only key. Its adapter requests strict JSON Schema and disables provider data collection. These OpenRouter-specific controls are not forwarded to DeepSeek; do not assume the providers have identical retention policies. Use synthetic or non-sensitive feedback in the public demo.

Compose passes the selected mode, model and enablement flags to API and worker, but secrets only to the worker. Never put a model key in frontend variables. The shipped example stays disabled for ordinary setup and automated tests. Changing environment values requires recreating the API/worker containers. Inspect queued jobs before switching: jobs retain their original provider, and work for an unconfigured provider fails explicitly instead of being silently rerouted. Use a new analysis run to process an existing message with the new provider; do not bulk-resubmit demo data.

The owner-authorized live configuration has no cumulative call ceiling and no lifetime analysis limit per record. `unlimited` removes only the cumulative ceiling: durable counters still record every admitted attempt and survive restarts. A finite value remains a total ceiling across providers in the database; switching providers does not reset it. Zero admits no calls. Failed or timed-out attempts still count. Each job permits at most three attempts; input is capped at 4,000 characters and configured output at 800 tokens. These are attempt/token bounds, not an exact dollar limit or an exactly-once billing guarantee. Provider failures remain visible.

Demo creation seeds sample messages with deterministic jobs so opening a workspace does not generate 24 paid requests. Submitting a new message while live mode is enabled automatically queues real analysis. For an existing sample, choose Analyze with AI on its detail page; existing fixture results are not evidence of a live model call. Automated regression tests remain isolated from paid calls.
