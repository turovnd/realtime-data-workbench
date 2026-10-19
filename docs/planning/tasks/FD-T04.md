---
id: FD-T04
type: task
is_task_of: FD-S03
status: implemented
depends_on: []
---

# FD-T04: Durable enrichment foundation

Parent: [FD-S03](../stories/FD-S03.md). Dependencies: None.

## Scope

Preserve immutable ingestion, bounded processing and inspectable failures.

## Acceptance

- Input and initial work commit together; idempotent retries cannot change original text.
- Worker claims, retry budgets and stale completions are bounded and tested.
- Structured results include exact source quotes and do not silently fall back after provider failure.

## Tests

Provider/schema units and real PostgreSQL ingestion, claims, recovery, fencing and budget tests.

## Evidence and status

Implemented. Provider/schema tests and real PostgreSQL processing checks pass locally. Two separately authorized OpenRouter analyses also completed through the local UI with persisted results and verified source evidence.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
