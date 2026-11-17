# API and Swagger

Production API origin: `https://turovnd-feedback-desk.vercel.app`; local origin: `http://127.0.0.1:8002`. Business routes include `/api` in their paths. Hosted frontend builds use `VITE_API_URL=same-origin`. For a separate local API, use its bare origin without an `/api` suffix.

FastAPI exposes generated OpenAPI at `/openapi.json`. Swagger assets are served locally at `/docs`, with explicit operation tags/descriptions, strict request/response models and bearer security. [Public Swagger](https://turovnd-feedback-desk.vercel.app/docs) and [OpenAPI](https://turovnd-feedback-desk.vercel.app/openapi.json) describe the published application. The table below describes the source contract; [delivery status](delivery-status.md) identifies the published revision.

| Method/path                                       | Purpose                                                                  | Authentication  |
| ------------------------------------------------- | ------------------------------------------------------------------------ | --------------- |
| `GET /health`                                     | API/database readiness and provider identity.                            | Public          |
| `POST /api/auth/demo`                             | Isolated workspace with deterministic seed jobs.                         | Public, bounded |
| `POST /api/auth/register`, `POST /api/auth/login` | Independent account/session creation.                                    | Public, bounded |
| `GET /api/auth/me`, `POST /api/auth/logout`       | Identity / revocation.                                                   | Bearer          |
| `GET /api/feedback`                               | Filtered cursor page of records/results.                                 | Bearer          |
| `GET /api/feedback/{record_id}`                   | Original message, runs and results for one record.                       | Bearer          |
| `POST /api/feedback`                              | Add one bounded message with idempotent identity.                        | Bearer          |
| `POST /api/feedback/{record_id}/analysis`         | Explicitly request a new real-AI analysis run.                           | Bearer          |
| `GET /api/activity`                               | Paginated automatic, individual and grouped analyses with exact results. | Bearer          |
| `GET /api/status`                                 | Current counts, sequence, provider and backfill status.                  | Bearer          |
| `POST /api/simulations`                           | Finite synthetic batch with idempotent request identity.                 | Bearer          |
| `POST /api/backfills`                             | Freeze selected IDs and enqueue a fixed configuration.                   | Bearer          |
| `GET /api/backfills/{batch_id}`                   | Read a paginated selection and results from one run.                     | Bearer          |
| `POST /api/backfills/{batch_id}/cancel`           | Cancel unfinished work without removing completed results.               | Bearer          |
| `POST /api/jobs/{job_id}/retry`                   | Retry an eligible failed job within its lifetime budget.                 | Bearer          |

Use Swagger **Authorize** with a session from this API. Documentation loading must not create synthetic data or invoke a provider. Browser-origin checks and admission limits still apply to interactive mutations.

## Generated client and message submission

`pnpm api:generate` exports the actual FastAPI schema to `openapi.json` and runs pinned `swagger-typescript-api` 13.2.18 to create `frontend/src/api/generated.ts`. It uses fetch and extracts request parameters, request bodies and response bodies. `pnpm api:check` verifies reproducible output. Session races, error mapping and Zod runtime validation remain in the application boundary; generated types are not runtime validation.

Authenticated detail returns 200 or workspace-scoped 404. Submission takes strict `FeedbackInput`: a nonblank identity of 1–100 characters, nonblank text of 1–4,000 characters and channel `Support`, `In-app` or `Community`; unknown fields are rejected. It returns `RecordView`: 201 for a new identity, 200 for an identical replay and 409 for conflicting content. Authentication and validation failures remain 401 and 422. Existing workspace/global record bounds still apply.

## Explicit AI analysis

`POST /api/feedback/{record_id}/analysis` accepts only `{ "identity": "a-new-request-identity" }`. Identity is nonblank, contains no NUL and is at most 100 characters. Reuse it when retrying an uncertain submission; a new deliberate analysis uses a new identity.

The route returns `RecordView`: 202 for a new run or 200 for a replay of the same identity. It returns 401 for authentication failure, workspace-scoped 404 for a missing record, 409 for an active run, 422 for invalid input and 503 when real analysis is not enabled. Readiness requires an explicitly selected live provider and its enablement flag; production uses `provider_mode=openrouter` and `openrouter_calls_enabled=true`. Upstream availability and credit can still fail during processing.

Hosted writes publish pending job IDs only after commit. A publication failure does not turn an accepted write into an HTTP failure or lose its job: replaying the same request can notify it again, and scheduled recovery repairs the publication gap. Private subscribers have no public HTTP mutation endpoint.

Each job/result includes its numeric `run`; jobs include provider and origin. There is no lifetime run cap; only one unfinished run per record is allowed. `RecordView` independently returns the latest ten jobs and ten successful outputs, ordered by run. Earlier jobs/results remain stored. Activity and batch details read the exact historical run directly. API acceptance is not completed analysis: poll the record to observe `queued`, `leased`, `succeeded`, `failed` or `cancelled` state. A failed provider call never creates a fixture result.

## Activity list

`GET /api/activity` accepts `limit` (1–50, default 10) and an opaque `cursor`. It returns `{ items, next_cursor, refresh_cursor, total, has_older, revision }`. Items discriminate on `kind`: `feedback` contains one automatic or manual job with its exact result, while `batch` contains a group summary. Bulk child jobs are not duplicated as standalone activity.

The first page freezes membership and order in a workspace-owned view. Current scheduling availability and an ID tie-breaker determine order; scheduling availability is not exposed as a creation timestamp. Continuations page persisted positions with SQL limits; `refresh_cursor` refreshes the same membership and omitting the cursor discovers new runs. Views expire after ten minutes and share the twenty-view workspace bound. Invalid, pruned or cross-scope cursors return 400; expired cursors return 410. Reading Activity does not queue work or call AI.

Each view contains at most the latest 6,000 activities. `total` counts that read window and `has_older` reports older stored activity, remaining fixed across its pages. This read bound never rejects a new analysis or removes history.

## Activity group details

`GET /api/backfills/{batch_id}` reads the selected messages and historical results for one workspace-owned run. It accepts `limit` (1–50, default 10) and an opaque `cursor`, returning `{ batch, items, next_cursor }`. Each item includes record ID, sequence, original text, channel, the selected historical job or `null`, and its exact output or `null`.

The result is tied to that batch's selected processing version, including a completed version reused by a later batch. A newer per-record AI analysis cannot replace the historical result or status shown here. Failed or cancelled work never substitutes an unrelated newer result.

Selection membership stays fixed while current status can update. Pages use descending sequence keysets with SQL limits. Cursors bind workspace and batch, expire after ten minutes and share the 20-view workspace bound. Authentication failures return 401; missing or foreign batches return 404; invalid, pruned or cross-scope cursors return 400; expired cursors return 410; invalid limits return 422. Reading details never queues work or calls a model.

## Pagination and errors

`GET /api/feedback` accepts `q` (up to 100 characters), `topic`, `status`, `limit` (1–50; default 12) and an opaque cursor. A new view freezes matching IDs. Subsequent pages use descending numeric keysets with SQL limit and hydrate one page. New arrivals and processing do not silently change membership; explicit refresh creates a new view.

A signed cursor binds workspace, filters and retained view. Invalid/tampered/mismatched cursors return 400; a retained expired view returns 410. An evicted view also requires a visible refresh. The client must not decode cursor internals or retry an expired view indefinitely.

Session failures are 401; immutable input/configuration conflicts are 409; admission limits are 429. Invalid request models use FastAPI validation errors. The generated schema and route tests own exact payload shapes. Manual submission is bounded text entry; simulation remains server-authored synthetic input. Neither implies integration with an external customer system.

See [auth](auth-tenancy.md), [workflows](workflows.md) and [limits](limits.md).

## Swagger asset maintenance

The API vendors `swagger-ui-dist` 5.33.1 with its upstream license, notice and SHA manifest. `python3 tools/vendor_swagger.py --version 5.33.1` reproduces the pinned assets. Run the API asset/contract tests after an intentional version update; no external CDN is required at runtime.
