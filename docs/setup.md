# Local setup

## Complete Docker stack

Use Docker Compose v2. Preserve an existing `.env`; otherwise copy `.env.example` and replace the database password.

```sh
cp -n .env.example .env
docker compose --profile local-web up --build -d --wait
```

Open `http://127.0.0.1:8082`. The optional web container proxies `/api` to this app's API. The API is loopback-only on `8002`; PostgreSQL has no public port. The migration service must succeed before API/worker startup. Stop this project with `docker compose --profile local-web down`, without `-v` when preserving data.

## Frontend development

Use Node 24 and pnpm 11.20.0. The repository has one pnpm workspace and lockfile at the root; app scripts remain in `web/package.json`.

```sh
pnpm install --frozen-lockfile
VITE_API_URL=http://127.0.0.1:8002 pnpm --dir web dev
```

Open `http://127.0.0.1:5174`. Without `VITE_API_URL`, the app runs an explicitly labelled browser fixture and disables account sign-in. `VITE_API_URL=same-origin` is used by the local Docker web proxy. Vercel uses the bare HTTPS API origin instead.

## Python development

Use the supported Python range and pinned dependencies from `backend/pyproject.toml` / `uv.lock`; Docker pins Python 3.13 and uv. Install from the root with `uv sync --directory backend --frozen`. Supply `WORKBENCH_DATABASE_URL` for an isolated PostgreSQL database. The app's Python settings load `.env` relative to the process working directory; the root Compose `.env` uses Compose variables, so do not assume it is interchangeable with native settings.

Run the migration once, then start API and worker in separate terminals:

```sh
uv run --directory backend python -m workbench.db
uv run --directory backend uvicorn workbench.api:app --host 127.0.0.1 --port 8002
uv run --directory backend python -m workbench.worker
```

The thin entrypoints delegate to the shared package layers. See [testing](testing.md) for verification commands.

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
| `WORKBENCH_LIVE_CALL_BUDGET`         | Persisted global attempt ceiling, default 3; 0–100.            |

Live processing requires explicit enablement and available durable budget. Demo initialization deliberately uses deterministic jobs. Changing the default provider does not overwrite a record's existing immutable configuration result. No model secret belongs in a `VITE_*` value. See [workflows](workflows.md) and [limits](limits.md).
