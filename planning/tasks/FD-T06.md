---
id: FD-T06
type: task
is_task_of: FD-S04
status: verified-local
depends_on: ["FD-T04"]
---

# FD-T06: Stable filtered feed cursors

Parent story: [FD-S04](../stories/FD-S04.md).

## Goal

Browse a stable bounded membership while arrivals and processing continue.

## Scope

Freeze matching IDs in retained views; use signed workspace/filter/view cursors, numeric keysets, SQL limit and per-page hydration.

## Dependencies

- [FD-T04](../tasks/FD-T04.md)

## Acceptance criteria

- [x] New arrivals/status changes do not duplicate or skip members of the current view.
- [x] Foreign/tampered/mismatched cursors fail; expired views visibly refresh.
- [x] View TTL/count and page/search limits are enforced.

## Tests and verification

- Real PostgreSQL stable membership, cursor scope, expiry and caps.
- Connected insertion-during-paging and expiry recovery browser tests.

## Status

**verified-local**.

## Implementation evidence

Current PostgreSQL feed tests passed frozen membership, signed cursor scope, expiry and view bounds. Connected browser tests verified 12+12 disjoint pages during arrivals and visible refresh after a 410 response.

Implementation and verification locations:

- [backend/src/workbench/logic/feed.py](../../backend/src/workbench/logic/feed.py)
- [backend/src/workbench/logic/cursors.py](../../backend/src/workbench/logic/cursors.py)
- [backend/src/workbench/repositories/views.py](../../backend/src/workbench/repositories/views.py)
- [tests/backend/src/workbench/logic/test_feed.py](../../tests/backend/src/workbench/logic/test_feed.py)
