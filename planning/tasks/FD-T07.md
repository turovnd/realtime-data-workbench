---
id: FD-T07
type: task
is_task_of: FD-S04
status: verified-local
depends_on: ["FD-T05", "FD-T06"]
---

# FD-T07: Feedback browsing and inspection UI

Parent story: [FD-S04](../stories/FD-S04.md).

## Goal

Inspect original text, evidence and versions while keeping selection stable.

## Scope

URL filters, infinite query pages, scroll/manual pagination, record inspector, cross-page ID selection and explicit refresh indicators.

## Dependencies

- [FD-T05](../tasks/FD-T05.md)
- [FD-T06](../tasks/FD-T06.md)

## Acceptance criteria

- [x] Selection persists across pages/filters and stays bounded.
- [x] Stale pages do not append to a reset query/session.
- [x] Inspector shows source, provider, evidence and both immutable versions.

## Tests and verification

- Fixture and connected browser paging/selection/inspection tests.
- Keyboard, narrow viewport and fallback loading without IntersectionObserver.

## Status

**verified-local**.

## Implementation evidence

Fourteen preview and three connected browser tests passed filters, source/version inspection, cross-page selection, automatic/manual paging, new-arrival behavior, keyboard/mobile layout and expiry refresh.

Implementation and verification locations:

- [web/src/pages/feedback-page.tsx](../../web/src/pages/feedback-page.tsx)
- [web/src/hooks/use-infinite-scroll.ts](../../web/src/hooks/use-infinite-scroll.ts)
- [tests/web/src/pages/workbench.spec.ts](../../tests/web/src/pages/workbench.spec.ts)
- [tests/web/src/pages/connected.spec.ts](../../tests/web/src/pages/connected.spec.ts)
