---
id: FD-T02
type: task
is_task_of: FD-S01
status: implemented
depends_on: ["FD-T01"]
---

# FD-T02: Deliver the routed review interface

Parent: [FD-S01](../stories/FD-S01.md). Dependencies: [FD-T01](FD-T01.md)

## Scope

Reshape the first MVP around explicit routes and reusable domain components.

## Acceptance

- The inbox offers an editable realistic example and a short route to analysis without a separate tutorial or technical controls.
- Page implementations live in pages/<name>/index.tsx; unique page children are adjacent.
- Potentially reusable feedback components use Feed, Filter and Summary through a named public barrel.
- Public imports have at most two segments; route navigation, browser back and direct access work.
- Stable filters, paging, selection, loading, error, empty and offline states remain clear.
- Frontend/backend roots, mirrored tests and generated-client tooling are runnable.
- Route groups use typed route objects, shared paths and lazy page imports through a stable data router.
- Routing, page composition, API query hooks and reusable domain behavior have explicit owners. No catch-all hook combines feed queries, selection, mutations and offline persistence.
- Authentication and selection mutations cannot leak into a different session or workspace.

## Tests

Frontend lint, formatting, strict type checks, unit tests, build and desktop/mobile browser journeys.

## Evidence and status

Route groups, page ownership, public exports and API hooks now follow the agreed structure. Static checks, unit tests and desktop/mobile journeys passed, including lazy-route offline recovery. The guided example and actual loading/error states are part of the same browser acceptance flow.

See [delivery status](../../delivery-status.md) for actual verification and release scope.
