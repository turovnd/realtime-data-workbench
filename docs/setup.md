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

Open `http://127.0.0.1:5174`. Without `VITE_API_URL`, the app runs an explicitly labelled browser fixture and disables account sign-in. `VITE_API_URL=same-origin` is used by the local Docker web proxy. Vercel uses the bare HTTPS API origin instead.

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

| Setting                              | Meaning                                                        |
| ------------------------------------ | -------------------------------------------------------------- |
| `POSTGRES_PASSWORD`                  | Compose database credential; replace the example.              |
| `WORKBENCH_DATABASE_URL`             | Native async PostgreSQL connection URL.                        |
| `WORKBENCH_IMAGE`                    | Versioned backend deployment image.                            |
| `WORKBENCH_ALLOWED_ORIGINS`          | JSON array of exact browser origins.                           |
| `FORWARDED_ALLOW_IPS`                | Uvicorn's verified proxy peer; never `*`.                      |
| `VITE_API_URL`                       | Public API origin: `https://realtime-api.b2p.space` on Vercel. |
| `WORKBENCH_PROVIDER_MODE`            | `deterministic` by default; explicit `openrouter` opt-in.      |
| `WORKBENCH_OPENROUTER_CALLS_ENABLED` | Separate live-call switch, default false.                      |
| `WORKBENCH_OPENROUTER_API_KEY`       | Worker-only secret.                                            |
| `WORKBENCH_OPENROUTER_MODEL`         | Baseline default `openai/gpt-4.1-mini`.                        |
| `WORKBENCH_OPENROUTER_MAX_TOKENS`    | Default 800; bounded to 100–1,200.                             |
| `WORKBENCH_LIVE_CALL_BUDGET`         | Persisted attempt ceiling: default 3; 0–100, or `unlimited`.   |

Live processing requires explicit enablement and either available durable budget or the explicit `unlimited` setting. Demo initialization deliberately uses deterministic jobs. Changing the default provider does not overwrite a record's existing immutable configuration result. No model secret belongs in a `VITE_*` value. See [workflows](workflows.md) and [limits](limits.md).

## Live analysis

The demonstration uses `openai/gpt-4.1-mini` through OpenRouter. Check the provider’s [model information and current pricing](https://openrouter.ai/openai/gpt-4.1-mini) before changing the model or enabling a new environment. The adapter requests a strict schema and verifies every evidence quote against the source; an error never falls back to a fixture.

The authorized local settings are:

```dotenv
WORKBENCH_PROVIDER_MODE=openrouter
WORKBENCH_OPENROUTER_CALLS_ENABLED=true
WORKBENCH_OPENROUTER_MODEL=openai/gpt-4.1-mini
WORKBENCH_OPENROUTER_MAX_TOKENS=800
WORKBENCH_LIVE_CALL_BUDGET=unlimited
```

Keep `WORKBENCH_OPENROUTER_API_KEY` in the ignored local `.env`; never put it in frontend variables. Compose passes the enablement flag to API and worker, but the key only to the worker. The shipped example stays disabled for ordinary setup and automated tests. Changing environment values requires recreating the API/worker containers. Inspect queued jobs before enabling a worker; do not bulk-resubmit demo data.

The owner-authorized local configuration has no cumulative call ceiling and no lifetime analysis limit per record. `unlimited` removes only the cumulative ceiling: the durable counter still records every admitted attempt and survives restarts. A finite value remains a total ceiling for the database; zero admits no calls. Failed or timed-out attempts still count. Each job permits at most three attempts; input is capped at 4,000 characters and output at 800 tokens locally. These are attempt/token bounds, not an exact dollar limit or an exactly-once billing guarantee. Provider failures remain visible.

Demo creation seeds sample messages with deterministic jobs so opening a workspace does not generate 24 paid requests. Submitting a new message while live mode is enabled automatically queues real analysis. For an existing sample, choose Analyze with AI on its detail page; existing fixture results are not evidence of an OpenRouter call. Automated regression tests remain isolated from paid calls.
