---
id: FD-T11
type: task
is_task_of: FD-S06
status: verified-local
depends_on: ["FD-T07", "FD-T10"]
---

# FD-T11: Fixed-selection versioned backfill

Parent story: [FD-S06](../stories/FD-S06.md).

## Goal

Reprocess exactly the selected records while preserving earlier output.

## Scope

Freeze up to 100 IDs, atomic bounded enqueue, immutable v1/v2 results, persisted progress and cancellation of unfinished work.

## Dependencies

- [FD-T07](../tasks/FD-T07.md)
- [FD-T10](../tasks/FD-T10.md)

## Acceptance criteria

- [x] Another workspace cannot backfill or retry selected objects.
- [x] Changing filters after start cannot change the batch membership.
- [x] Completed v1 remains after v2; cancellation preserves already completed effects.

## Tests and verification

- Fixed selection, uniqueness, cancellation/fencing and cross-workspace database cases.
- Public selected two-record v2 flow with persisted progress and unchanged v1/source.

## Status

**verified-local**.

## Implementation evidence

Current PostgreSQL fixed-selection/backfill/cancellation tests and connected v1-to-v2 browser journey passed, preserving earlier output and source while reporting persisted progress.

Implementation and verification locations:

- [backend/src/workbench/logic/backfills.py](../../backend/src/workbench/logic/backfills.py)
- [backend/src/workbench/repositories/backfills.py](../../backend/src/workbench/repositories/backfills.py)
- [tests/backend/src/workbench/logic/test_backfills.py](../../tests/backend/src/workbench/logic/test_backfills.py)
- [tests/web/src/pages/connected.spec.ts](../../tests/web/src/pages/connected.spec.ts)
