# Implementation record

2026-10-10. The current product is **Feedback Desk**. This file supersedes the executable-scope claims in the historical plan.

## Implemented

Independent email/password accounts, one-click isolated demo, guarded UI, hashed/revocable 24-hour sessions, bounded Argon2id hashing, persisted auth admission limits, exact CORS and workspace-scoped reads/mutations. Account data is excluded from anonymous 24-hour cleanup. Logout clears private caches; delayed old authentication responses cannot overwrite or clear a newer session.

Official shadcn CLI preset `b1Ymqvgiu` supplies Nova / Neutral / Blue / chartBlue / Inter / Lucide. Feature modules compose official components. URL filters, TanStack Infinite Query, automatic intersection-based paging plus a keyboard-accessible Load more button, selection across pages/filters, detail/evidence/version inspection, backfill/cancel/retry and explicit offline snapshots are implemented. Browser-only fixture mode is labelled separately.

Server cursor pagination uses a real sequence keyset and SQL limit, not a full snapshot or offset. Frozen matched IDs make page membership stable while processing and arrivals continue. HMAC cursors bind workspace/filter/view; malformed, cross-workspace, mismatched and expired paths are handled visibly. Views have a ten-minute TTL and a 20-view/workspace cap. Only requested page rows are hydrated. Processing refreshes poll every three seconds; new arrivals enter through explicit refresh.

FastAPI/Pydantic, typed SQLAlchemy async transactions, immutable input/result guards, independent worker, unique record/config effects, leases, fences, bounded retries, provider deadlines, durable call admission and fixed-selection backfill are implemented. Defaults remain keyless/deterministic. The OpenRouter adapter has strict structured JSON, local evidence validation, a configured model, explicit opt-in, bounded transport and no silent fallback.

## Executed locally

- Ruff lint/format and strict mypy passed. 37 Python tests passed, including real PostgreSQL auth, cursor, immutable storage, concurrent claims/budgets, stale completion, lease recovery, retry and cancellation checks.
- 11 Vitest tests passed, including stable fixture pages and deferred old-401/logout/login races. ESLint, TypeScript, Prettier and production build were executed.
- Fourteen Playwright desktop/mobile browser-preview scenarios passed: retry/source evidence, versioned backfill, filters/selection, automatic scroll paging, arrivals without duplicate/skipped rows, offline shell/snapshot reload, logout clearing and keyboard/narrow-screen checks, manual fallback paging without IntersectionObserver, and stopping unfinished work.
- Two connected browser journeys passed against the real FastAPI + separate worker + PostgreSQL 17.11 stack: account registration/re-login with persistent versions, and stable server cursor paging while another API action inserts feedback.
- A third connected UI check passed with an injected HTTP 410 response: the visible expiry error recovered through explicit refresh. Backend expiry itself is covered by real PostgreSQL tests.
- Native and linux/amd64 Docker backend and optional static-web images built. The local API, worker and PostgreSQL have their own Compose project and persistent volume. The local nginx UI on 8082 passed a real auth/feed/automatic-paging smoke with no browser page errors.
- The coordinating operator ran one authorized live OpenRouter call through this app's provider factory and `domain.enrich`: structured result and exact source quote validation passed. Automated tests remain deterministic; no model-quality score is claimed.

CI definitions exist but have not run on GitHub. A build warning about the main frontend chunk exceeding 500 kB remains; it does not prevent the production build.

## Deployment status

The coordinating operator deployed the `linux/amd64` backend image `turovnd-realtime:20261010-feedback` to the owner's Yandex Cloud Linux server in its own Compose project, `turovnd-realtime`. Migrations passed. PostgreSQL stays private and the API binds loopback port 8002. Existing unrelated services were preserved.

`FORWARDED_ALLOW_IPS=172.22.0.1` is configured for the verified gateway of this project's Docker network. The backend image's OCI index is `sha256:41d5fee09850bf612c17846ef7e9673dc5c79e8dfd8d490da0df144b81c5adb8`; its exported amd64 image configuration ID is `sha256:8a3fff7a40fa3f9cb54caace55cf0b0bd22dd905ea87e072a61922d63c40b240`. The operator verified the platform configuration and layers after transfer.

Public backend verification passed on 2026-10-10 at `https://realtime-api.b2p.space`: valid HTTPS, health, exact-origin CORS and authentication; two disjoint 12-record cursor pages; rejection of another workspace's cursor and backfill selection; real worker completion of v1 followed by selected v2 while preserving v1 and original source; persisted 2/2 backfill progress; and session revocation after logout. The local Docker UI on 8082 is healthy after the proxy DNS refresh fix.

The Vercel UI is still not deployed: the requested Vercel MCP is unavailable in the current session. There is no verified public UI URL, and an integrated public UI/API rollout is not yet claimed.

## Remaining scope

Email verification/reset, OAuth, organizations/roles, SSE transport, a labelled classification evaluation, broader accessibility audit, richer observability, tested off-host backups/restoration and automated remote delivery are not implemented. The bounded migration bootstrap includes explicit additive changes but is not a general versioned migration framework.

No general exactly-once provider execution/billing guarantee, Kafka ownership, production-grade tenancy certification, throughput benchmark or high availability claim is made. Browser snapshots are explicit local copies of synthetic data, not a replacement for server persistence.
