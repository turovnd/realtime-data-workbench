# API and Swagger

Production API origin: `https://realtime-api.b2p.space`; local origin: `http://127.0.0.1:8002`. Business routes include `/api` in their paths. Set the frontend API variable to the bare origin, not an origin ending in `/api`.

FastAPI exposes generated OpenAPI at `/openapi.json`. Swagger assets are served locally at `/docs`, with explicit operation tags/descriptions, strict request/response models and bearer security. [Public Swagger](https://realtime-api.b2p.space/docs) and [OpenAPI](https://realtime-api.b2p.space/openapi.json) are deployed and verified; release evidence is in [delivery status](delivery-status.md).

| Method/path                                       | Purpose                                                    | Authentication  |
| ------------------------------------------------- | ---------------------------------------------------------- | --------------- |
| `GET /health`                                     | API/database readiness and provider identity.              | Public          |
| `POST /api/auth/demo`                             | Isolated workspace with deterministic seed jobs.           | Public, bounded |
| `POST /api/auth/register`, `POST /api/auth/login` | Independent account/session creation.                      | Public, bounded |
| `GET /api/auth/me`, `POST /api/auth/logout`       | Identity / revocation.                                     | Bearer          |
| `GET /api/feedback`                               | Filtered cursor page of records/results.                   | Bearer          |
| `GET /api/status`                                 | Current counts, sequence, provider and backfill status.    | Bearer          |
| `POST /api/simulations`                           | Finite synthetic batch with idempotent request identity.   | Bearer          |
| `POST /api/backfills`                             | Freeze selected IDs and enqueue a fixed configuration.     | Bearer          |
| `POST /api/backfills/{batch_id}/cancel`           | Cancel unfinished work without removing completed results. | Bearer          |
| `POST /api/jobs/{job_id}/retry`                   | Retry an eligible failed job within its lifetime budget.   | Bearer          |

Use Swagger **Authorize** with a session from this API. Documentation loading must not create synthetic data or invoke a provider. Browser-origin checks and admission limits still apply to interactive mutations.

## Pagination and errors

`GET /api/feedback` accepts `q` (up to 100 characters), `topic`, `status`, `limit` (1–50; default 12) and an opaque cursor. A new view freezes matching IDs. Subsequent pages use descending numeric keysets with SQL limit and hydrate one page. New arrivals and processing do not silently change membership; explicit refresh creates a new view.

A signed cursor binds workspace, filters and retained view. Invalid/tampered/mismatched cursors return 400; a retained expired view returns 410. An evicted view also requires a visible refresh. The client must not decode cursor internals or retry an expired view indefinitely.

Session failures are 401; immutable input/configuration conflicts are 409; admission limits are 429. Invalid request models use FastAPI validation errors. The generated schema and route tests own exact payload shapes. No arbitrary production customer ingestion endpoint is exposed: simulation creates server-authored synthetic messages.

See [auth](auth-tenancy.md), [workflows](workflows.md) and [limits](limits.md).

## Swagger asset maintenance

The API vendors `swagger-ui-dist` 5.33.1 with its upstream license, notice and SHA manifest. `python3 tools/vendor_swagger.py --version 5.33.1` reproduces the pinned assets. Run the API asset/contract tests after an intentional version update; no external CDN is required at runtime.
