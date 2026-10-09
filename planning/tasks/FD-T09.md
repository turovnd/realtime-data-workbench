---
id: FD-T09
type: task
is_task_of: FD-S05
status: verified-local
depends_on: ["FD-T08"]
---

# FD-T09: Strict bounded enrichment provider

Parent story: [FD-S05](../stories/FD-S05.md).

## Goal

Produce structured feedback labels with inspectable source evidence.

## Scope

Deterministic rules and optional OpenRouter adapter, strict Pydantic models, exact quote validation, transport bounds and durable global attempt reservations.

## Dependencies

- [FD-T08](../tasks/FD-T08.md)

## Acceptance criteria

- [x] Live processing requires explicit switches/key/budget; demo seeds remain deterministic.
- [x] Invalid/disabled/exhausted calls fail visibly with no silent fallback.
- [x] Budget reservations survive concurrent workers and restarts.

## Tests and verification

- Injected HTTP provider cases and database concurrent budget tests.
- Optional separately authorized one-call smoke; no classification benchmark claim.

## Status

**verified-local**.

## Implementation evidence

Current provider units and PostgreSQL budget tests passed strict output/evidence checks, explicit failures and persistent admission bounds. No paid model call was rerun during this refactor; routine verification remained deterministic.

Implementation and verification locations:

- [backend/src/workbench/logic/enrichment.py](../../backend/src/workbench/logic/enrichment.py)
- [backend/src/workbench/infrastructure/providers.py](../../backend/src/workbench/infrastructure/providers.py)
- [tests/backend/src/workbench/infrastructure/test_providers.py](../../tests/backend/src/workbench/infrastructure/test_providers.py)
- [tests/backend/src/workbench/repositories/test_usage.py](../../tests/backend/src/workbench/repositories/test_usage.py)
