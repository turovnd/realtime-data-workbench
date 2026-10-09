# Operations and deployment

## Current topology

| Surface              | Destination                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| UI                   | [https://turovnd-feedback-desk.vercel.app](https://turovnd-feedback-desk.vercel.app) on Vercel |
| API                  | [https://realtime-api.b2p.space](https://realtime-api.b2p.space)                               |
| Docker project       | `turovnd-realtime`                                                                             |
| Published API socket | `127.0.0.1:8002` behind the existing HTTPS proxy                                               |
| PostgreSQL           | Private named volume and private network in this project's stack                               |
| Worker               | Separate process/container using the same app database                                         |

The current two portfolio stacks retain separate PostgreSQL instances. Consolidation is an unselected operational option; this repository does not depend on a shared database service or the other application. Existing unrelated server services must remain unchanged.

## Frontend build and Git delivery

Vercel uses root directory `web`, runs `pnpm build` and publishes `dist`. Set `ENABLE_EXPERIMENTAL_COREPACK=1` to honor the pinned pnpm version.

Set `VITE_API_URL=https://realtime-api.b2p.space` at frontend build time, with no `/api` suffix. It is a public origin, never a credential. Missing this variable selects the labelled browser fixture; `same-origin` is reserved for the optional local Docker web proxy.

Production delivery tracks `main`. `VITE_API_URL` and exact API CORS currently cover the stable production alias only. Feature-branch previews are not promised a working API connection; if used, configure their environment and deliberately allow each exact origin with appropriate data isolation.

The authorized public repository is `turovnd/realtime-data-workbench`. Git-connected automatic Vercel delivery is requested. Confirm repository linkage, build root, environment target and a successful deployment from an actual push before marking integration complete. Backend delivery is a separate pipeline: a UI deployment does not update the API, worker or schema. Current integration evidence is in [delivery status](delivery-status.md).

## Server configuration and rollout

Keep server secrets in the deployment environment, outside Git and Vercel public variables. Preserve the existing image tag and environment when changing CORS. `WORKBENCH_ALLOWED_ORIGINS` is a JSON array; `FORWARDED_ALLOW_IPS` must contain the verified proxy peer, which may be the Docker bridge gateway.

Allow the exact production UI origin. Do not allow `*.vercel.app` or automatically trust every preview URL. A preview needs its own deliberate API/data access decision. Default operation is deterministic with live provider calls disabled. Optional provider controls are documented in [setup](setup.md) and [limits](limits.md).

For each release: verify image architecture/digest and compatibility; retain the previous image; run the app's migration deliberately; start only the named app project; wait for readiness; then run the complete synthetic workflow. Configuration-only API changes should recreate only `api` with `--no-deps --no-build --pull never`, preserving DB/worker IDs. Application releases may need both API and worker updated after schema compatibility review. Never use global prune/stop commands or remove volumes as part of rollout.

The HTTPS proxy enforces 16 KiB request bodies. Feedback refresh uses polling, so no SSE proxy configuration is required. API auth/rate limits remain enforced behind the proxy. Scoped certificate renewal and proxy validation belong to the deployment operator; repository source alone does not establish renewal success.

## Health, smoke and rollback

`GET /health` checks API/database readiness, not worker progress. Create a disposable demo and verify 12+12 cursor paging, worker v1 completion, selected v2 backfill, unchanged source/v1 history and logout revocation. Confirm another workspace cannot use its cursor or mutate its objects. Keep smoke bounded and deterministic.

Record image identity, application health and container state before a change. Afterward compare existing non-target containers and configuration. Monitor restarts, failed/old jobs, disk space and private volume growth. Do not log bearer tokens, passwords, full provider responses or raw Compose configuration.

Rollback to the preceding compatible API/worker image within this project. A schema rollback is separate; restoring an old image does not undo a migration. Do not run `down -v`. Keep data volumes and backups intact.

## Backup and restore

A persistent Docker volume is not a backup. Arrange encrypted off-host exports, a retention policy and a restoration test into a new isolated database. Verify roles, schema, row counts and a full synthetic workflow before relying on the backup. No successful off-host restore is currently claimed. PostgreSQL's [SQL dump documentation](https://www.postgresql.org/docs/current/backup-dump.html) explains per-database dumps and separately handled cluster roles.

One host remains a shared failure domain. No high availability or measured throughput guarantee is claimed.
