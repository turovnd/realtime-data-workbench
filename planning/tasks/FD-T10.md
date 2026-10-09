---
id: FD-T10
type: task
is_task_of: FD-S06
status: verified-local
depends_on: ["FD-T08", "FD-T09"]
---

# FD-T10: Fenced worker recovery and retries

Parent story: [FD-S06](../stories/FD-S06.md).

## Goal

Recover durable jobs without stale stored effects or unlimited retry.

## Scope

Global lease admission, 30-second claims, 10-second provider deadline, fencing, three lifetime attempts and persisted terminal states.

## Dependencies

- [FD-T08](../tasks/FD-T08.md)
- [FD-T09](../tasks/FD-T09.md)

## Acceptance criteria

- [x] No more than the configured global claims execute concurrently.
- [x] Expired/stale claims cannot commit over current work.
- [x] Manual retry preserves lifetime attempts and original configuration/provider.

## Tests and verification

- Concurrent claims, crash-after-response, lease expiry, retry exhaustion and cancellation database tests.
- Real separate worker completion smoke.

## Status

**verified-local**.

## Implementation evidence

Current real PostgreSQL tests passed bounded concurrent claims, expired-lease fencing, crash recovery, cancellation and lifetime retry budgets. The rebuilt separate worker completed connected processing.

Implementation and verification locations:

- [backend/src/workbench/repositories/jobs.py](../../backend/src/workbench/repositories/jobs.py)
- [backend/src/workbench/workers/processing.py](../../backend/src/workbench/workers/processing.py)
- [tests/backend/src/workbench/repositories/test_jobs.py](../../tests/backend/src/workbench/repositories/test_jobs.py)
- [tests/backend/src/workbench/workers/test_processing.py](../../tests/backend/src/workbench/workers/test_processing.py)
