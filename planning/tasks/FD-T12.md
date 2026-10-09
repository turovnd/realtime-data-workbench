---
id: FD-T12
type: task
is_task_of: FD-S06
status: verified-local
depends_on: ["FD-T06", "FD-T07", "FD-T11"]
---

# FD-T12: Live refresh and honest preview modes

Parent story: [FD-S06](../stories/FD-S06.md).

## Goal

Show actual processing state without replacing a stable view or hiding API errors.

## Scope

Three-second polling, explicit new-record refresh, progress/retry/cancel controls, separate labelled browser fixture and offline shell-only service worker.

## Dependencies

- [FD-T06](../tasks/FD-T06.md)
- [FD-T07](../tasks/FD-T07.md)
- [FD-T11](../tasks/FD-T11.md)

## Acceptance criteria

- [x] Connected API failure stays an error, never a fallback to fake data.
- [x] Polling updates visible results without changing frozen membership.
- [x] Service worker ignores cross-origin/API/non-GET traffic; offline mutations stay disabled.

## Tests and verification

- Browser arrival/status/refresh, failure, cancel and offline reload checks.
- Client adapter and service-worker review with connected workflow smoke.

## Status

**verified-local**.

## Implementation evidence

Current preview and connected tests passed polling updates, stable page membership, explicit arrivals/expiry refresh, bounded controls and offline read-only behavior. Adapter and service-worker review confirms that connected errors do not select the browser fixture and API traffic is not shell-cached.

Implementation and verification locations:

- [web/src/hooks/use-workbench.ts](../../web/src/hooks/use-workbench.ts)
- [web/src/lib/api/client.ts](../../web/src/lib/api/client.ts)
- [web/public/sw.js](../../web/public/sw.js)
- [tests/web/src/pages/workbench.spec.ts](../../tests/web/src/pages/workbench.spec.ts)
