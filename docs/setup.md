# Local setup

## Docker

Copy `.env.example` only if `.env` does not already exist, then set `POSTGRES_PASSWORD`.

```sh
docker compose --profile local-web up --build -d --wait
```

- Web: `http://127.0.0.1:8082`
- API: `http://127.0.0.1:8002`
- Swagger: `http://127.0.0.1:8002/docs`

Compose runs migrations before API and worker startup. It uses a dedicated PostgreSQL volume. Do not delete an existing volume to fix a failed migration.

The frontend container uses one `frontend/nginx.conf`: static files, SPA fallback and an `/api` proxy. It runs as a non-root user on port 8080 with temporary files under `/tmp`. Nginx is only needed for local Docker; Vercel handles hosted routing.

Base images include a version and digest so rebuilding uses the same reviewed image. A floating tag can change underneath the same source. Update the tag and digest together and run container checks to pick up new patches; see [Docker's guidance](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions).

## Frontend development

```sh
pnpm install --frozen-lockfile
VITE_API_URL=http://127.0.0.1:8002 pnpm dev
```

Open `http://127.0.0.1:5174`. Without `VITE_API_URL`, the frontend runs its labelled browser preview. The hosted build and Docker web container use `VITE_API_URL=same-origin`.

Frontend package scripts, ESLint, Vitest, Playwright and TypeScript test configuration live in `frontend/`. Root scripts forward to that package; the pnpm lockfile and workspace remain shared.

## Backend development

```sh
uv sync --directory backend --frozen
uv run --directory backend alembic upgrade head
uv run --directory backend uvicorn modules.api.app:app --host 127.0.0.1 --port 8002
uv run --directory backend python -m modules.worker
```

Run API and worker in separate terminals. Supply `WORKBENCH_DATABASE_URL` for an isolated PostgreSQL database. Native settings read `.env` relative to the process working directory; root Compose variables are not automatically native backend settings.

`WORKBENCH_` remains the environment prefix for compatibility with existing installations. It is unrelated to Python package nesting.

## OpenRouter

Store the key server-side as `WORKBENCH_OPENROUTER_API_KEY`, then configure:

```dotenv
WORKBENCH_PROVIDER_MODE=openrouter
WORKBENCH_OPENROUTER_CALLS_ENABLED=true
WORKBENCH_OPENROUTER_MODEL=openai/gpt-4.1-mini
WORKBENCH_OPENROUTER_MAX_TOKENS=800
WORKBENCH_LIVE_CALL_BUDGET=unlimited
```

Compose passes the key only to the worker. Hosted settings belong to server environment variables; never use `VITE_*` for a secret. Recreate local API/worker containers after changing their environment.

Opening a demo prepares sample data without calling OpenRouter. New feedback and explicit analysis use the live model when enabled. The cumulative limit can be `0`–`100` or `unlimited`; counters persist, failed attempts count, and the three-attempt limit per job always applies.

## Schema changes

```sh
uv run --directory backend alembic revision --autogenerate -m "describe the change"
uv run --directory backend alembic upgrade head
uv run --directory backend alembic check
```

Review generated migrations. Data transformations and immutable-history triggers require explicit migration code. Use `WORKBENCH_MIGRATION_DATABASE_URL` for a direct connection; hosted settings also accept `WORKBENCH_DATABASE_URL_UNPOOLED`.

For an existing database created before Alembic, back it up and rehearse on an isolated restore. Then pause only this application's writers and run `alembic -x adopt=true upgrade head`. Adoption validates the known schema before recording a revision; do not bypass a mismatch with `stamp head`.

See [API client generation](api.md#generate-the-client) and [tests](testing.md).
