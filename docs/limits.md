# Limits and unsupported guarantees

These are enforced demo bounds, not throughput measurements.

| Boundary                | Implemented baseline                                                  |
| ----------------------- | --------------------------------------------------------------------- |
| Request body            | 16 KiB API/proxy limit.                                               |
| Input text              | 4,000 characters; simulation batches contain 1–12 synthetic messages. |
| Structured result       | Summary 240 characters; 1–3 source quotes of up to 200 characters.    |
| Stored records          | 500/workspace and 5,000 globally.                                     |
| Workspace admission     | 1,000 workspaces; bounded anonymous cleanup.                          |
| Sessions/demo retention | 24 hours; account data excluded from demo cleanup.                    |
| Authentication          | Persisted admission buckets; bounded Argon2id concurrency.            |
| Cursor page/view        | 1–50 rows, default 12; 10-minute views; 20 views/workspace.           |
| Search                  | Up to 100 characters.                                                 |
| Backfill                | At most 100 selected IDs; atomic fixed selection.                     |
| Worker                  | Two global leases; 30-second lease; three lifetime attempts/job.      |
| Provider                | 10-second deadline; default 800 output tokens, permitted 100–1,200.   |
| Global live budget      | Durable attempt reservations; default 3, configurable 0–100.          |
| Refresh transport       | Three-second polling; explicit list membership refresh.               |

Immutable inputs/results, fences, unique record/configuration effects and exact source checks protect stored behavior. The advisory-lock design deliberately serializes bounded mutations; no scalability benchmark is claimed.

Not implemented: real customer ingestion, Kafka/Redis, SSE, organizations/roles, OAuth, email verification/reset, classification quality evaluation, general migration framework, production-grade observability or high availability. Browser fixtures and snapshots are local synthetic copies. They do not establish worker durability, live provider quality or server persistence. Idempotent storage does not guarantee exactly-once provider calls or charges.
