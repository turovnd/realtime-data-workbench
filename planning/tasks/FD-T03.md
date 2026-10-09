---
id: FD-T03
type: task
is_task_of: FD-S02
status: verified-local
depends_on: ["FD-T01"]
---

# FD-T03: Generated API contract and Swagger

Parent story: [FD-S02](../stories/FD-S02.md).

## Goal

Let a reviewer inspect and exercise the real API contract.

## Scope

Generate OpenAPI from actual request/response schemas; group operations, document bearer security/errors/examples and serve Swagger assets locally.

## Dependencies

- [FD-T01](../tasks/FD-T01.md)

## Acceptance criteria

- [x] GET /openapi.json describes all public application routes and exact auth requirements.
- [x] /docs loads its own assets; opening documentation creates no session and makes no provider call.
- [x] Examples use synthetic values and contain no credentials.

## Tests and verification

- Contract tests compare route paths/security/models to the generated document.
- HTTP/browser check for Swagger assets, authorizing and one deterministic request.

## Status

**verified-local**.

## Implementation evidence

OpenAPI tests passed for all 12 application paths, models, bearer security and local asset checksums. Real-PostgreSQL same-origin Swagger auth/feed/logout passed. Browser inspection rendered all operations and Try it out GET /health returned 200; external validation is disabled.

Implementation and verification locations:

- [backend/src/workbench/api.py](../../backend/src/workbench/api.py)
- [tests/backend/src/workbench/test_api.py](../../tests/backend/src/workbench/test_api.py)
- [backend/src/workbench/static/swagger/manifest.json](../../backend/src/workbench/static/swagger/manifest.json)
- [docs/api.md](../../docs/api.md)
