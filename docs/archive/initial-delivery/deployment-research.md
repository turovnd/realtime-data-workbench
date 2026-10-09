# Vercel deployment research

**Historical alternative, superseded on 2026-10-09:** the owner selected Vercel UI and Docker backend/worker/PostgreSQL on their server. The platform facts below are retained as research, not the current implementation target. Follow [the selected hybrid deployment](hybrid-deployment.md).

Verified by opening official documentation on 2026-10-09. This is a planning recommendation, not a deployed or validated topology. No account configuration, purchase, deployment, or repository publication was performed.

## Recommendation

- Keep the two repositories independent. Each contains its own React frontend, backend, domain logic, synthetic fixtures, local database setup, and tests.
- AI Workbench: Fastify/Node handles RAG requests, citations, run events, and approval transitions. Queue-triggered bounded jobs handle ingestion and resumable work. Persist approvals and job state in PostgreSQL; waiting for a person must not hold a request open.
- Data Workbench: FastAPI/Python handles event ingestion, filtering, replay, enrichment versions, and backfill controls. Use native Python queue consumers for bounded enrichment batches; an extra Node orchestration service is unnecessary.
- Hosted target: React assets plus API and queue consumer Functions on Vercel, PostgreSQL in the same region, OpenRouter optional. Use cursor-based, reconnectable SSE for the initial one-way UI event feed. WebSockets are now supported in public beta, but are unnecessary for these initial scenarios.
- Prefer one Vercel project per repository using Services if its beta is acceptable after a small deployment spike. The fallback is two Vercel projects per repository (frontend/API), with explicit preview pairing and CORS or a tested same-origin proxy. Do not assume separate projects are still mandatory.
- Keep queue delivery behind a small adapter. Local deterministic mode uses the same bounded job handlers against a real local PostgreSQL job table; hosted mode uses Vercel Queues push delivery. Queue messages reference persisted jobs; PostgreSQL retains replayable source records and failed-job history. The local adapter is not evidence that the hosted broker has passed integration tests.
- Do not add Kafka to the first release. An optional later Kafka profile is justified only to demonstrate partition ordering, consumer lag, replay, and rebalancing. Run its persistent consumer locally or on a suitable external worker runtime; do not start it in a request handler.

## Verified platform capabilities and constraints

| Area | Verified fact | Planning implication |
| --- | --- | --- |
| Fastify | Zero-configuration deployment; the app becomes one Function on Fluid compute. Standard Node bundle: 250 MB. [Fastify docs](https://vercel.com/docs/frameworks/backend/fastify), updated 2026-08-10. | Thin entrypoint, app factory for tests, no process-lifetime business state. |
| FastAPI | Native Python deployment; the app becomes one Function on Fluid compute. Configure duration against the resolved entrypoint. [FastAPI docs](https://vercel.com/docs/frameworks/backend/fastapi), updated 2026-08-27. | FastAPI does not need a Node proxy service merely to run on Vercel. |
| Python | Streaming supported. Python 3.12 default; 3.13/3.14 available. Standard bundle: 500 MB; no automatic tree shaking. [Python runtime](https://vercel.com/docs/functions/runtimes/python), updated 2026-08-12. | Pin a tested runtime and dependencies; avoid bundling local models or fixtures unnecessarily. |
| Duration | Fluid: Hobby default/max 300s; Pro/Enterprise default 300s, GA max 800s, extended beta 1800s. Includes streaming. Request/response body limit: 4.5 MB. 1024 shared file descriptors. [Function limits](https://vercel.com/docs/functions/limitations), updated 2026-08-24. | Design jobs to finish far below 300s, bound uploads and connections. Larger uploads need a separate object-storage upload flow. |
| Extended duration | Above 800s needs function-level configuration; supported Node 20/22/24 and Python 3.12/3.13/3.14. Unavailable with Secure Compute/Static IPs during beta. [Duration configuration](https://vercel.com/docs/functions/configuring-functions/duration). | Do not require paid-plan extended duration for the demo. |
| Services | Beta on all plans; multiple independently built frontend/backend units share a deployment, routing, and domain. [Services](https://vercel.com/docs/services). | One project per repo is possible, with beta coupling explicitly recorded. |
| WebSockets | Beta on all plans with Fluid. Connections close at Function maximum duration. Reconnection can land on another instance/deployment; durable state and coordination must be external. [WebSockets](https://vercel.com/docs/functions/websockets), updated 2026-08-10. | It is incorrect to state that Vercel categorically cannot host WebSockets. Use reconnect/resume contracts either way. |

## Queues and Workflows

[Vercel Queues](https://vercel.com/docs/queues) is beta on all plans. JavaScript/TypeScript use `@vercel/queue`; Python has an official SDK via `vercel` or the smaller `vercel-queue`. Typed Pydantic payload support has an optional extra. Python subscribers are decorated functions declared in `[[tool.vercel.subscribers]]`, built as private queue-triggered Functions. [Python SDK reference](https://vercel.com/docs/queues/python-sdk), updated 2026-08-24. This eliminates a presumed need for a TypeScript queue bridge.

Delivery is at least once. Ordering is approximate, with no FIFO guarantee even at concurrency 1. There is no built-in DLQ: persist failed jobs before acknowledging poison messages. Explicitly cap concurrency, deliveries, retries, and provider budgets. Messages normally stay pinned to the publishing deployment, so old deployments may continue processing after a rollout. Idempotent database writes and application event versions remain necessary. [Queue concepts](https://vercel.com/docs/queues/concepts), updated 2026-09-10.

Queue retention is 60s–7 days (default 24h); visibility timeout 0–60 minutes (default 60s); receive batches up to 10; message size up to 100 MB. Those broker limits do not override an HTTP Function's body limit. Hobby includes 1M queue API operations; push consumer compute is separately metered. [Queue limits](https://vercel.com/docs/queues/pricing), updated 2026-08-12. Keep actual demo payloads tiny and store durable replay data in PostgreSQL rather than treating finite queue retention as a historical database.

Vercel Workflows became GA on 2026-04-16; its Python SDK remains beta. [GA announcement](https://vercel.com/blog/a-new-programming-model-for-durable-execution), [Python SDK](https://workflow-sdk.dev/docs/getting-started/python). Workflows provides durable steps, sleep, hooks and persisted streams; it can fit human approvals and multi-stage RAG ingestion without a separate orchestration service. It is an optional alternative to explicit database state transitions and queue jobs, not a requirement to add both orchestration systems.

Overall workflow duration/sleep has no limit, but individual steps retain Function duration limits. Limits include 25K events/run, 10K steps/run, 50 MB payload, 2 GB entity storage/run, and 240s replay duration. Completed-run retention: Hobby 1 day, Pro 7 days, Enterprise 30 days. Workflow, queue, storage and compute usage have separate meters. [Workflow limits](https://vercel.com/docs/workflows/pricing), updated 2026-09-16. Keep the demo's audit history in the application database regardless of orchestration choice.

## Region and database connections

Functions default to `iad1`; choose a region close to the actual database after its provider/location is known. Pro/Enterprise can use multiple regions, but a single database-adjacent region is simpler here. [Region configuration](https://vercel.com/docs/functions/configuring-functions/region).

Queue messages persist in the selected region, with possible neighboring-region storage during failover; strict residency is not promised. [Queue concepts](https://vercel.com/docs/queues/concepts). Workflows pins each run and its state/queues/streams to one region; default follows the starting Function, with an explicit region option. [Workflow regions](https://vercel.com/docs/workflows).

For Node, a module-scoped pool with `attachDatabasePool` is the documented Vercel pattern; always release checked-out connections. This helper manages idle connections, not the database's global connection budget. [Connection pooling](https://vercel.com/kb/guide/connection-pooling-with-functions). For Python, do not invent an equivalent Vercel helper. Proposed: use the selected provider's pooled endpoint, then choose a small bounded SQLAlchemy async pool or `NullPool` depending on provider rules and measurements. SQLAlchemy documents both bounded async pools and asyncio-compatible `NullPool`. [SQLAlchemy pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html). Confirm transaction-pooler compatibility, prepared statements, connection ceilings and migration/direct endpoints after credentials/provider details arrive. Avoid holding a database connection while waiting for an LLM or UI stream.

## Background work and Kafka boundary

`waitUntil` extends a request's lifetime for bounded follow-up tasks, but shares its timeout and gets cancelled when the Function times out. It is not durable dispatch for enrichment. [Functions API](https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package). Durable work should be committed to the database and sent through the queue, with reconciliation for the database/publish failure window.

Cron is a trigger: Hobby supports daily schedules with hour-level precision; Pro/Enterprise support minute intervals. All allow 100 jobs/project. [Cron limits](https://vercel.com/docs/cron-jobs/usage-and-pricing), updated 2026-07-15. Delivery is best effort, can be missed or duplicated, and failures are not automatically retried. [Cron management](https://vercel.com/docs/cron-jobs/manage-cron-jobs). Therefore a daily Hobby reconciliation job is suitable; continuous enrichment must be event-triggered, not dependent on minute cron.

Vercel still does not provide an always-running server process through its backend Function model. [Backend adaptation](https://vercel.com/docs/frameworks/backend), updated 2026-08-20. A persistent Kafka consumer can instead run on an explicit continuous-worker service such as [Render Background Workers](https://render.com/docs/background-workers), or use AWS-managed polling with a [Kafka Lambda event-source mapping](https://docs.aws.amazon.com/lambda/latest/dg/with-kafka-configure.html). These are alternative future hosting choices, not approved purchases. AWS Lambda is a specific service; a Vercel Function is sufficient to demonstrate serverless execution without adding AWS.

Browser service workers are a separate browser concern: propose offline application-shell access and a clearly marked last-viewed synthetic snapshot. They must not own enrichment jobs or guarantee processing after the browser closes. Keep approval actions online-only; never silently replay approvals from an offline cache. [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API), [offline/background lifecycle](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation).

## Evidence caveats and implementation gates

- Search snippets were materially stale: some said WebSockets unsupported, Node-only Queues, 24h maximum retention, and 250 MB Python bundles. Directly opened docs superseded them.
- No future-dated source was used as availability evidence relative to 2026-10-09. Dated sources above are from April–September 2026 or earlier. The sources establish documented availability, not availability verified in this user's Vercel account.
- Some official pages are internally inconsistent: the Workflow pricing page's broad platform table says unlimited projects/cron while dedicated plan pages give finite caps, and lists 250 MB generically while Python runtime docs specify 500 MB. Use the dedicated current limits pages for those values.
- Before implementation is called deployable: pin runtime/SDK versions; verify Services routing and streaming under the chosen topology; test native queue build/consumption and preview isolation; test reconnects, duplicate/out-of-order delivery, worker interruption, retry exhaustion, and database/publish reconciliation against real PostgreSQL. No such deployment checks have run at this checkpoint.
