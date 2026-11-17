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

- A small explicit live-model evaluation reports schema, quote and scenario checks separately from deterministic regression tests; it makes no production accuracy claim.
- Input and initial work commit together; idempotent retries cannot change original text.
- Worker claims, retry budgets and stale completions are bounded and tested.
- Structured results include exact source quotes and do not silently fall back after provider failure.
- Alembic owns schema changes; API and worker startup do not mutate the schema. Existing unversioned data is adopted only after structural validation.
- Prompt policy, typed provider transport and worker composition are separate; retry ownership stays in the durable worker.

## Tests

Provider/schema units and real PostgreSQL ingestion, claims, recovery, fencing and budget tests.

## Evidence and status

Implemented in `backend/modules/worker`, `backend/common/repositories`, provider infrastructure and Alembic migrations. Real PostgreSQL tests cover claims, idempotency, recovery and stale completion; provider contracts cover structured output and source validation.
