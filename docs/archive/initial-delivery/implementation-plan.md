# Implementation plan: live and historical enrichment

> Current executable scope and verified checks are tracked in [implementation-status.md](implementation-status.md). The detailed future contracts below are not all implemented.

Updated 2026-10-09. **Hosting, scenario and Python style checkpoint accepted; implementation authorized.** This supersedes telemetry-only v1 and optional-LLM scope. Structured LLM enrichment is a core capability.

## Product and first vertical slice

The user is a product operations analyst watching synthetic feedback. The main screen is a filterable table with raw text, topic, intent, processing status and provenance. A detail panel shows evidence and previous enrichment revisions; a job panel controls backfill and selective retry. This is not a chat interface.

Deterministic generator -> validated ingestion -> immutable raw rows and jobs -> bounded enrichment -> validated structured output -> PostgreSQL -> snapshot/cursor events -> React table. Add a backfill selection using a new prompt/schema version after live processing and reconnect work.

The same synthetic seed and configured clock produce repeatable inputs. Keyless enrichment is deterministic and clearly labelled. Optional OpenRouter structured generation shares the same output validation path. No social-network credentials, real devices, client data, scraped material or fabricated model-quality numbers.

## Proposed contracts

- Raw identity is workspace/source/epoch/sequence, with event time separate from server ingestion time. Identical duplicate input is acknowledged once; the same identity with different content is a conflict. Late events remain inspectable and do not roll back the current source view.
- Validate raw text length and schema before persistence. Raw rows are immutable; a corrected input is a new revision.
- Enrichment key includes raw revision, prompt version, schema version and provider configuration. Live ingestion and backfill use the same work item. Explicit reprocessing creates a new output revision rather than silently replacing provenance.
- Outputs contain allowlisted topic/intent, bounded summary and evidence copied from the raw record. Validate schema and evidence; do not treat substring validity as proof that the entire classification is correct. Include a small synthetic labelled set to inspect quality and abstention, with no preclaimed scores. Do not expose model confidence as calibrated probability.
- Job states: queued -> leased -> succeeded, retryable -> queued, or terminal failed/cancelled. Claims have lease expiry, fencing version and bounded attempts. Provider work happens outside the transaction; completion is conditional on current lease and configuration.
- Two workers may call the provider after a crash; unique keys and compare-and-set completion prevent duplicate stored results. Do not promise exactly-once requests or spending.
- Backfill freezes input selection, upper watermark and target configuration. Keyset checkpoints cannot skip rows after restart. Report selected/succeeded/failed/cancelled counts; live jobs receive reserved capacity so backfill cannot starve them.
- Cancellation stops scheduling new items; stored completed results remain visible. Retries are selective and bounded; exhausted failures are durable and inspectable.
- Snapshot includes a server event cursor. Apply later events once; a late snapshot cannot replace newer state. Selection changes abort the old request and guard against late completions. Cursor expiry returns a resync signal.

## Execution and proposed layout

Use React/Vite plus a modular FastAPI service with explicit Pydantic schemas, application operations, repositories and bounded job handlers. Proposed folders: `web/src/{features,api,components}`, `backend/src/workbench/{api,domain,db,jobs,providers}`, `backend/tests`, `db/migrations`. Keep Python code idiomatic and concise; no class hierarchy without a concrete need.

Use SQLAlchemy async sessions per task, never one session shared across concurrent workers. Local and hosted modes run a separate Python worker process and PostgreSQL through Docker Compose. Commit job rows with business state; the worker polls eligible jobs and recovers expired claims. FastAPI BackgroundTasks and request-lifetime tasks do not provide durability. Fence stale completions. Only the React UI runs on Vercel.

Hosted simulation is user-triggered and bounded: enqueue a finite seeded run and process small batches. Continuous worker polling is appropriate in its dedicated server container; unbounded user simulation is not. Kafka remains deferred. Browser requests and SSE connect directly to the server API over HTTPS. See [the selected hybrid deployment](hybrid-deployment.md).

Initial design budgets, not measured performance: 500 records per interactive simulation; 4,000 characters per raw record; 10 items per claimed batch; at most 2 admitted provider attempts per workspace; 60s provider timeout; 120s execution slices; bounded retries with backoff/jitter; a 500-event UI ring buffer; paginated history and server downsampling for charts. Budget reservations must survive process restart and concurrent instances. Larger 100k/1M input experiments are separate reproducible benchmarks after correctness.

### Worker deadlines, recovery and cursors

Each claimed item receives one bounded provider attempt; retries persist a next-attempt time and return to the eligible queue. Claim only immediately serviceable items, up to 2 at once; a batch of 10 is a fetch ceiling, not permission to lease 10 idle jobs. Keep the 120s application slice and a 15s commit/cleanup margin as design budgets; they are no longer Vercel Function limits. Cap provider time by the remaining slice budget, persist continuation and renew leases safely with fencing. On shutdown, stop claiming new work, allow a bounded drain and let unfinished claims expire. Admission limits do not guarantee remote provider cancellation after a worker crash.

Commit a job row with business state; worker polling removes the database-to-external-broker publish gap. A worker crash after commit is recovered by another poll; expired leases are retried according to persisted attempt limits. Optional notifications can reduce latency but never replace polling. Show queued, leased/running, retryable and terminal states explicitly. Test crash after job creation, after provider response and before result commit, plus expired leases and stale completion. No Vercel Queue visibility, TTL or cron dependency remains.

Event sequence is a commit-consistent cursor, not a plain PostgreSQL sequence or timestamp. Serialize each workspace's event append with a locked counter row in the same mutation transaction; read snapshot data and watermark from one consistent DB snapshot. Test reversed transaction completion and concurrent snapshot/append so a higher cursor cannot hide a lower unseen event. This deliberately trades per-workspace write parallelism for a simple, testable demo contract.

## UX, accessibility and offline behavior

Use official shadcn Table, Tabs, Sheet, Badge, Alert, Empty, Skeleton and form controls. Sort/filter state belongs in the URL; TanStack Query owns fetched data. Virtualize only when measured row volume warrants it; preserve keyboard navigation and accessible table semantics.

Separate connection state, data age and enrichment backlog. Distinguish no rows, filtered-empty, waiting, provider-limited, invalid output, exhausted retry and offline stale view. Retain selection through updates and expose version differences without losing the original text. Reconnect/resync must not silently discard a backfill selection.

A browser service worker can cache the versioned shell. Save only an explicitly selected bounded synthetic snapshot for read-only offline inspection, with age and configuration displayed; never cache live streams or mutation responses. Pause ingestion/backfill controls while offline. On reconnect, fetch a current snapshot before resuming the feed. Test cache upgrades and reset cleanup.

## Verification and delivery

| Layer | Required evidence before release |
| --- | --- |
| Static | Frontend ESLint, Prettier, strict TypeScript and build; Python Ruff lint/format and strict mypy. |
| Unit | Merge/order policy, stale selection protection, output validation, quote provenance, retry classification, bounded batching and deterministic generator. |
| Real PostgreSQL | Fresh migrations; duplicate/conflicting ingestion; concurrent claims; lease expiry and stale completion; restart after provider response; immutable revisions; backfill checkpoints; cancellation and recovery after committed jobs or expired leases. |
| API/worker integration | FastAPI lifespan plus HTTPX/AnyIO, provider 429/timeouts/malformed output, worker polling/lease contract and retry exhaustion. |
| E2E | Playwright live stream -> filter -> inspect evidence -> change config -> backfill -> reconnect/retry; keyboard/focus and accessibility checks; offline stale view and recovery. |
| CI/CD | GitHub Actions with real PostgreSQL, locked Python/frontend installs and build/test artifacts. Vercel UI previews, versioned backend images, isolated staging data, migration gate, server/API/UI smoke tests and rollback plan. Deployment destinations are selected; readiness and access details remain required. |

HTTPX async clients do not run lifespan automatically; tests must initialize and close resources explicitly. Browser streams require real transport tests. Deterministic mode is the default CI path; live provider checks require separate authorized credentials and budgets. Sample-only checks are not application readiness.

## Sequence and acceptance

1. Completed: the owner accepted the Python sample and scenario.
2. Complete keyless live ingestion + enrichment + snapshot/reconnect using a real DB.
3. Add checkpointed backfill and prove crash, duplicate and stale-worker behavior.
4. Polish UI, accessibility, offline inspection and observability; measure only the implemented version.
5. Verify optional live providers and the Docker backend with the Vercel UI; document the deployed result. Public GitHub publication remains separate.

Kafka is deferred. Add it only for a distinct experiment requiring independent consumers/partition ordering/rebalancing, with an explicitly suitable external worker runtime. It is not necessary to prove these application contracts.

## Library evidence

- [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/) and [background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/).
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/): reject unexpected/coerced LLM output deliberately.
- [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html): one session per concurrent task and explicit I/O.
- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs): provider capability checks plus local validation.

- [TanStack Query cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation): pass the signal to the actual transport and still guard stale selections.
- [Vite static deployment](https://vite.dev/guide/static-deploy.html): production build assets are the frontend deployable; the preview server is not a production server.
