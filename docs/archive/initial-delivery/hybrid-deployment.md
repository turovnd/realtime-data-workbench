# Vercel UI and Docker backend

2026-10-10. This is the accepted hosting arrangement for **Feedback Desk**. The complete stack is verified locally. The coordinating operator has deployed the backend to the owner's Yandex Cloud server, completed migrations and verified the public HTTPS/API workflow on 2026-10-10. The Vercel UI is not deployed because the requested Vercel MCP is unavailable in the current session; no public UI URL is verified.

## Independent application

```text
Browser → Vercel static React UI
Browser → HTTPS realtime-api.b2p.space → existing host nginx → loopback:8002 FastAPI
                                                                        │
                                                               private PostgreSQL
                                                                        │
                                                              separate Python worker
```

This repository owns its Compose project (`turovnd-realtime`), credentials, network, database volume, authentication and application data. It has no runtime dependency on the other portfolio application. Existing services on the owner's Linux server must remain untouched. The API publishes only `127.0.0.1:8002`; PostgreSQL and workers have no host ports.

PostgreSQL durably stores both application data and job state. The API commits immutable input and work together. The separate worker polls, claims bounded leases, performs provider work outside transactions and commits through fencing checks. No Vercel Services/Queues, Redis or Kafka is needed for this bounded workflow. A request-lifetime background task is not used for durable execution.

## UI and API connection

Vercel builds the `web` directory with `pnpm build` and serves `dist`. Set the public build variable `VITE_API_URL` to the verified API URL. It contains no credentials. API/database/OpenRouter secrets remain server-side. With no API URL, the UI exposes a clearly labelled browser-only deterministic preview and disables account sign-in.

The UI uses independent email/password accounts or a one-click temporary demo. The API returns opaque workspace-scoped bearer sessions; hashed tokens are stored in PostgreSQL and the browser keeps the token in session storage. Logout revokes it and clears private cached data. Cross-site cookie behavior is not a dependency of this design.

Set `WORKBENCH_ALLOWED_ORIGINS` to the exact intended Vercel/custom UI origins. Do not allow all `vercel.app` origins. CORS is separate from session validation. An integration preview must be explicitly allowlisted; ordinary preview builds can keep browser-demo mode. Preview access must not silently enable paid provider processing.

The feed uses three-second polling and server-side keyset pagination. Signed cursors bind workspace, filters and a frozen view. Automatic scrolling and the accessible Load more button fetch bounded pages. Processing refreshes keep existing membership stable; an explicit refresh admits new matches. There is no SSE transport in this release.

## Existing host nginx

Add only this API hostname to the existing nginx configuration after checking current routes and resource headroom. Preserve unrelated applications and their ports. Terminate HTTPS at nginx, enforce request-size and admission limits, and proxy to loopback port 8002.

Set `FORWARDED_ALLOW_IPS` to the exact verified proxy peer seen by Uvicorn. With host nginx forwarding through Docker, that may be the Docker bridge gateway. The safe default is `127.0.0.1`; do not use wildcard trust. Incorrect proxy trust can merge visitors into a shared API authentication rate bucket. The deployed project uses its verified gateway `172.22.0.1` for this setting. The public auth/CORS smoke passed with this deployment configuration.

The API independently validates body bounds, exact mutation origins, session ownership, selection size and provider limits. Demo startup always seeds deterministic jobs. Live OpenRouter requests require explicit opt-in, a server-only key and durable bounded admission; they do not start just because a key exists.

## Local and server operation

`docker compose --profile local-web up --build -d` also starts a non-root static nginx UI on `127.0.0.1:8082` with its own `/api` proxy. This is an optional local convenience. Production uses the Vercel UI, so omit the `local-web` profile on the server. The development UI can run separately on 5174.

Container images pin Python, uv, PostgreSQL and the optional Node/nginx build/runtime images. Production uses a versioned backend image through `WORKBENCH_IMAGE`; the deployment operator builds or loads the server's `linux/amd64` artifact, runs the bounded additive migration and updates only this Compose project. Resource limits, health checks, capped logs, read-only application filesystems and graceful worker shutdown are supplied.

The public backend at `https://realtime-api.b2p.space` passed HTTPS, health/CORS/auth, disjoint 12+12 cursor pages, cross-workspace rejection, real worker v1/v2 preservation, persisted backfill progress and logout-revocation checks. Vercel UI integration remains pending; repeat the browser journey against its actual origin after publication. Current checks and deployment evidence are in [implementation-status.md](implementation-status.md).

Named volumes survive container replacement but are not backups. External backups, tested restore and high availability remain outside the implemented slice. The server is a common failure domain. See [operations and recovery](operations.md) for secrets, proxy trust, rollback and live-provider smoke controls.

## Delivery status

The GitHub workflows define static, unit, real PostgreSQL, browser and connected Compose checks, plus a manually packaged backend image artifact. They have not run remotely because the repository has not been published. Automatic remote CD is not configured. The owner authorized Vercel UI and Docker backend deployment; public Git pushes and unrelated server changes remain separate scope.
