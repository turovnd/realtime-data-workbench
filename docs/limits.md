# Limits and unsupported guarantees

These are enforced demo bounds, not throughput measurements.

| Boundary                | Implemented baseline                                                                                     |
| ----------------------- | -------------------------------------------------------------------------------------------------------- |
| Request body            | 16 KiB API/proxy limit.                                                                                  |
| Input text              | 4,000 characters; simulation batches contain 1–12 synthetic messages.                                    |
| Structured result       | Summary 240 characters; 1–3 source quotes of up to 200 characters.                                       |
| Stored records          | 500/workspace and 5,000 globally.                                                                        |
| Workspace admission     | 1,000 workspaces; bounded anonymous cleanup.                                                             |
| Sessions/demo retention | 24 hours; account data excluded from demo cleanup.                                                       |
| Authentication          | Persisted admission buckets; bounded Argon2id concurrency.                                               |
| Cursor page/view        | 1–50 rows; feed default 12, Activity/run-details default 10; 10-minute views; 20 shared views/workspace. |
| Response history        | Latest ten jobs and ten successful outputs per record; older history remains stored.                     |
| Activity read window    | Latest 6,000 activities per view; `has_older` reports truncation. No analysis admission cap.             |
| Search                  | Up to 100 characters.                                                                                    |
| Backfill                | At most 100 selected IDs; atomic fixed selection.                                                        |
| Explicit analysis       | No lifetime run cap; one unfinished run per record; idempotent request identity.                         |
| Worker                  | Two global leases; 30-second lease; three lifetime attempts/job.                                         |
| Hosted dispatch         | Three-second post-commit handoff; failure leaves durable work queued.                                    |
| Queue delivery          | At least once; 20 analysis deliveries per message, distinct from the three admitted AI attempts/job.     |
| Scheduled recovery      | Every 30 minutes, up to one minute jitter; at most 100 IDs/page; 45-second handler deadline.             |
| Provider                | 10-second deadline; default 800 output tokens, permitted 100–1,200.                                      |
| Global live budget      | Durable attempt counter; default ceiling 3, configurable 0–100 or `unlimited`.                           |
| Refresh transport       | Three-second polling; explicit list membership refresh.                                                  |

Immutable inputs/results, fences, unique record/run effects and exact source checks protect stored behavior. The advisory-lock design deliberately serializes bounded mutations; no scalability benchmark is claimed.

Not implemented: real customer ingestion, Kafka/Redis, SSE, organizations/roles, OAuth, email verification/reset, a representative independently reviewed AI-quality benchmark, production-grade observability or high availability. Browser fixtures and snapshots are local synthetic copies. They do not establish worker durability, live provider quality or server persistence. Idempotent storage does not guarantee exactly-once provider calls or charges.

Production uses `unlimited` cumulative attempts, at most three attempts per job and 800 output tokens per attempt. Shipped local defaults stay disabled with a budget of three; reservations persist across restarts and are not refunded after failed or uncertain calls. See [live setup](setup.md#live-analysis).

The database can suspend between requests; cold starts add latency. Missed publication or an expired lease may wait roughly thirty-one minutes for scheduled redispatch with healthy infrastructure. This is not a completion guarantee: outages, backlog or retries can extend it. Queue message exhaustion does not discard the PostgreSQL job; recovery can republish due work. Neon Free quotas, Vercel usage and provider billing are separate limits; see [deployment](vercel.md#database-and-idle-cost).
