---
id: FD-T01
type: task
is_task_of: FD-S01
status: verified-local
depends_on: []
---

# FD-T01: Runtime boundaries

Parent story: [FD-S01](../stories/FD-S01.md).

## Goal

Make module ownership explicit without changing the product contract.

## Scope

Move entrypoints, UI composition and shared code into the agreed runtime/layer tree; retain actual package exports and locked tools. Do not create a cross-repository dependency.

## Dependencies

No predecessor task. Follow the accepted product/hosting constraints and preserve existing behavior.

## Acceptance criteria

- [x] Application entrypoints contain composition rather than unrelated business operations.
- [x] Imports respect the documented runtime/layer boundary; Docker and frontend builds use the moved paths.

## Tests and verification

- Typecheck and application builds from a clean locked install.
- Import-boundary review and complete regression gate before release.

## Status

**verified-local**.

## Implementation evidence

The Python layers passed Ruff, strict mypy across 77 source/test modules and 40 tests with real PostgreSQL. Root pnpm workspace checks/builds passed. The native local Compose rebuild left API, worker, web and own PostgreSQL healthy.

Implementation and verification locations:

- [package.json](../../package.json)
- [backend/src/workbench/api.py](../../backend/src/workbench/api.py)
- [backend/src/workbench/workers/runner.py](../../backend/src/workbench/workers/runner.py)
- [docs/architecture.md](../../docs/architecture.md)
