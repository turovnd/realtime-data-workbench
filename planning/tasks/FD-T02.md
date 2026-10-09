---
id: FD-T02
type: task
is_task_of: FD-S01
status: verified-local
depends_on: ["FD-T01"]
---

# FD-T02: One mirrored test tree

Parent story: [FD-S01](../stories/FD-S01.md).

## Goal

Give every test a discoverable production owner.

## Scope

Move existing automated suites into root tests/ following production paths; update runner, fixture, CI and browser discovery without dropping assertions.

## Dependencies

- [FD-T01](../tasks/FD-T01.md)

## Acceptance criteria

- [x] One root application test tree mirrors the production tree.
- [x] All previously discovered suites are still discovered; source folders contain no duplicated tests.

## Tests and verification

- Compare test discovery before/after the move.
- Run unit, real PostgreSQL and browser suites through their public scripts.

## Status

**verified-local**.

## Implementation evidence

Root mirrored suites discovered and passed 40 Python/PostgreSQL, 11 Vitest, 14 desktop/mobile preview and three connected browser tests. A frozen offline pnpm install also passed.

Implementation and verification locations:

- [vitest.config.ts](../../vitest.config.ts)
- [playwright.config.ts](../../playwright.config.ts)
- [backend/pyproject.toml](../../backend/pyproject.toml)
- [tests/backend/conftest.py](../../tests/backend/conftest.py)
