---
id: FD-T06
type: task
is_task_of: FD-S04
status: implemented
depends_on: ["FD-T04"]
---

# FD-T06: Reanalyze selected feedback and recover failures

Parent: [FD-S04](../stories/FD-S04.md). Dependencies: [FD-T04](FD-T04.md)

## Scope

Run real AI analysis again for an existing record, or reprocess a bounded selection, while keeping original messages and prior results.

## Acceptance

- Explicit record analysis uses an idempotent request identity and creates a new run after earlier work finishes.
- One run per record may be in flight; repeated analysis has no lifetime run cap. The cumulative provider ceiling is configurable, including explicit `unlimited`, while each job retains its attempt/token bounds.
- Fixed selections freeze at admission; completed results are immutable.
- Progress is persisted; cancellation preserves completed results.
- Activity includes automatic, single-record and grouped analyses; cards expand to exact historical results with cursor pagination, automatic status updates and visible recovery states.
- Retry is bounded and stale leases cannot overwrite accepted output.

## Tests

Real PostgreSQL analysis admission/replay/concurrency and backfill/recovery tests; browser analysis and Activity expansion/pagination/recovery checks; separately bounded live-provider smoke.

## Evidence and status

Implemented. Current real PostgreSQL tests cover analysis admission, idempotent replay, concurrency, fixed selection, cancellation and recovery. Controlled browser cases cover the interactive states; two real OpenRouter UI actions verified repeated analysis and retained results. The record page presents the latest result. Activity exposes the exact result from each listed run, including older jobs outside the record response’s recent-history window.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
