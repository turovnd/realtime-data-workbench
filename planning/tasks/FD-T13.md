---
id: FD-T13
type: task
is_task_of: FD-S07
status: verified-local
depends_on: ["FD-T01", "FD-T02", "FD-T03", "FD-T12"]
---

# FD-T13: Regression and release evidence

Parent story: [FD-S07](../stories/FD-S07.md).

## Goal

Prove the reorganized application still works as a complete system.

## Scope

Execute static checks, units, real PostgreSQL integration, browser journeys and container builds; distinguish local results from hosted CI and deployed smoke.

## Dependencies

- [FD-T01](../tasks/FD-T01.md)
- [FD-T02](../tasks/FD-T02.md)
- [FD-T03](../tasks/FD-T03.md)
- [FD-T12](../tasks/FD-T12.md)

## Acceptance criteria

- [x] Every required command is recorded with actual outcome and scope.
- [x] Database checks run against disposable real PostgreSQL, not only mocks.
- [x] Connected browser journey passes through API, separate worker and persistence.

## Tests and verification

- Full command matrix in docs/testing.md.
- Review failure artifacts and rerun affected checks after fixes.

## Status

**verified-local**.

## Implementation evidence

Final local gate passed: Ruff lint/format, mypy across 77 source/test modules, 40 Python/PostgreSQL tests, frontend lint/typecheck/format/build, 11 Vitest, 14 desktop/mobile preview and three connected browser tests. Native Compose API/worker/web/PG were healthy; Swagger browser health request and frozen offline pnpm install passed. Hosted CI and the new public release remain separate tasks.

Implementation and verification locations:

- [package.json](../../package.json)
- [backend/pyproject.toml](../../backend/pyproject.toml)
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml)
- [docs/testing.md](../../docs/testing.md)
