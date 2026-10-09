# Operations and recovery

## Isolation and rollout

Each repository owns its Compose project, private network and named PostgreSQL volume. The default project is `turovnd-realtime`; never run global cleanup commands. The API is loopback-only on 8002. Add a route to the existing server proxy only after inspecting its current configuration. PostgreSQL stays private.

Build an image for the target architecture with a stable tag. The supplied Dockerfile pins Python 3.13.16 and uv 0.12.2 by digest; Compose pins PostgreSQL 17.11 by digest. These official image manifests were checked on 2026-10-09. Review security updates deliberately and rerun verification before changing them.

```sh
docker build --platform linux/amd64 -t turovnd-realtime:RELEASE backend
WORKBENCH_IMAGE=turovnd-realtime:RELEASE docker compose up -d --no-build
```

Supply a server-only `.env` with a URL-safe database password and an exact JSON list of allowed UI origins. The Vercel root directory is `web`; `VITE_API_URL` points to the verified HTTPS API. Deterministic mode needs no provider secret. OpenRouter settings and secrets are supplied only to the worker; public frontend variables contain no credentials. Never expose database credentials or bearer tokens through public environment settings or logs.

The reverse proxy must terminate HTTPS, enforce request-size and per-IP/session issuance limits, and forward only this API hostname. The API independently validates Origin, request shape, bearer ownership and bounded selection sizes. Only synthetic server-authored inputs can be ingested through the public simulation endpoint.

Set `FORWARDED_ALLOW_IPS` to the exact observed reverse-proxy peer before public auth testing. Uvicorn defaults to loopback trust. A host nginx proxy forwarding through Docker may appear as the Docker bridge gateway; verify it rather than trusting every address. Otherwise all visitors can share one API auth bucket. Never use `*` to work around the issue. The local optional web profile also needs its actual origin (default `http://127.0.0.1:8082`) in `WORKBENCH_ALLOWED_ORIGINS`.

The backend at `https://realtime-api.b2p.space` passed public HTTPS, health/CORS/auth, pagination, workspace-isolation, durable worker/version and logout checks on 2026-10-10. The Vercel UI remains unpublished; its build will use `VITE_API_URL=https://realtime-api.b2p.space` with its exact UI origin allowlisted. Local Docker web builds use `VITE_API_URL=same-origin` and a private proxy to this stack's API.

## Health and smoke checks

`GET /health` checks a database connection. It does not prove the worker is progressing. After rollout create a new demo session (`POST /api/auth/demo` with `{}`), request a small simulation, poll for `succeeded`, backfill its IDs to v2 and inspect both result versions. Monitor container restarts, worker logs, queue age, failed jobs and volume usage. Logs identify jobs/fences, not raw bearer tokens.

Worker shutdown stops new claims and permits a bounded drain. A crash leaves persisted claims; after lease expiry a worker retries the same operation key. The result commit checks fencing and deadline. `failed` jobs retain an inspectable error category. Invalid output becomes terminal until a bounded manual retry; exhausted jobs require diagnosis, not an unlimited retry button.

## Backup and restore

A Docker volume is not a backup. Before retaining meaningful data, arrange encrypted `pg_dump` exports outside the server and document the retention policy. Test restoration into a **new isolated database** before relying on a backup. No external backup destination has been configured or restore test executed by this repository implementation.

Temporary demo workspaces expire and are removed after 24 hours in bounded batches of 20. Account workspaces are explicitly excluded from this cleanup. Account sessions still expire after 24 hours; login issues a new token without deleting account data. Preservation of anonymous data across its TTL is intentionally unsupported. An operator can stop new admission and inspect counts before maintenance. Avoid deleting another stack's volume or stopping a shared reverse proxy.

## Rollback and migration

Keep the previous image tag. Application rollback is `WORKBENCH_IMAGE=<previous> docker compose up -d --no-build` in this repository's dedicated deployment directory/project. Do not run `down -v`; it deletes this project's database volume. Schema rollback is separate and may need restoration. The initial migration is idempotent but future schema upgrades require explicit versioned scripts and compatibility checks.

The release workflow packages a versioned image and Compose file; it performs no external push or remote operation. Once GitHub publication, environment protection and server delivery credentials are configured, add and test remote deployment as a separate delivery step. Frontend Vercel previews and manual operator rollout do not establish automatic CD.


## Authorized live-provider smoke

Default `WORKBENCH_PROVIDER_MODE=deterministic` and `WORKBENCH_OPENROUTER_CALLS_ENABLED=false` make no paid calls, even if a key exists. A live test requires all of: provider mode `openrouter`, calls enabled, a worker-only `WORKBENCH_OPENROUTER_API_KEY`, a configured model (`openai/gpt-4.1-mini` by default), and a positive `WORKBENCH_LIVE_CALL_BUDGET`. Keep the budget small; the global `provider_usage` reservation is committed before each request, survives restarts, and counts failed attempts too. The 800-token default has a hard settings cap. Never expose secrets through Compose config output or raw upstream errors.

Use a fresh record/config for the live smoke: `(record, config)` is immutable/idempotent, so changing the default provider does not overwrite an earlier deterministic version. `POST /api/auth/demo` seeds 24 deterministic jobs even when a live test is configured. Do not trigger a 12-item simulation for a one-call smoke. A bounded operator script can call `openrouter_generator(settings, client)` through `domain.enrich`, or enqueue one synthetic item through the repository operation. Restore deterministic/disabled settings after the authorized test; do not reset durable usage silently to bypass the cap.

If a provider is disabled, a response is invalid, or the budget is exhausted, jobs fail explicitly. Retry does not change the job's original provider/configuration. Evidence validation confirms source substrings, not factual classification accuracy.
