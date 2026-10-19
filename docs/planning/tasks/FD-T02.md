---
id: FD-T02
type: task
is_task_of: FD-S01
status: ready-for-review
depends_on: ["FD-T01"]
---

# FD-T02: Deliver the routed review interface

Parent: [FD-S01](../stories/FD-S01.md). Dependencies: [FD-T01](FD-T01.md)

## Scope

Reshape the first MVP around explicit routes and reusable domain components.

## Acceptance

- Page implementations live in pages/<name>/index.tsx; unique page children are adjacent.
- Potentially reusable feedback components use Feed, Filter and Summary through a named public barrel.
- Public imports have at most two segments; route navigation, browser back and direct access work.
- Stable filters, paging, selection, loading, error, empty and offline states remain clear.
- Frontend/backend roots, mirrored tests and generated-client tooling are runnable.

## Tests

Frontend lint, formatting, strict type checks, unit tests, build and desktop/mobile browser journeys.

## Evidence and status

Implemented and verified locally; ready for owner review. Publishing remains a separate, unauthorized step.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
