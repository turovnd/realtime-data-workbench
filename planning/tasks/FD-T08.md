---
id: FD-T08
type: task
is_task_of: FD-S05
status: verified-local
depends_on: ["FD-T01"]
---

# FD-T08: Immutable ingestion and results

Parent story: [FD-S05](../stories/FD-S05.md).

## Goal

Keep source messages and versioned output inspectable and reproducible.

## Scope

Atomic input/job insertion, unique workspace input identity, conflict detection, immutable input/result storage and record/configuration uniqueness.

## Dependencies

- [FD-T01](../tasks/FD-T01.md)

## Acceptance criteria

- [x] Same identity/same text is idempotent; changed text conflicts.
- [x] Input and job commit together; rollback leaves neither half.
- [x] Existing result versions cannot be overwritten by changing provider defaults.

## Tests and verification

- Real PostgreSQL immutable/idempotent input and result guards.
- Worker flow inspecting original source and old/new versions.

## Status

**verified-local**.

## Implementation evidence

Current real PostgreSQL tests passed atomic idempotent ingestion, changed-content conflicts and immutable input/result protections. Connected worker v1-to-v2 history preserved original source and prior output.

Implementation and verification locations:

- [backend/src/workbench/logic/ingestion.py](../../backend/src/workbench/logic/ingestion.py)
- [backend/src/workbench/repositories/ingestion.py](../../backend/src/workbench/repositories/ingestion.py)
- [backend/src/workbench/infrastructure/tables.py](../../backend/src/workbench/infrastructure/tables.py)
- [tests/backend/src/workbench/logic/test_ingestion.py](../../tests/backend/src/workbench/logic/test_ingestion.py)
