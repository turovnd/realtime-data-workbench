---
id: FD-T05
type: task
is_task_of: FD-S03
status: verified-local
depends_on: ["FD-T04"]
---

# FD-T05: Private client and offline isolation

Parent story: [FD-S03](../stories/FD-S03.md).

## Goal

Prevent previous sessions from leaking through client caches or delayed requests.

## Scope

Guard auth queries, isolate offline snapshots, handle delayed 401/login/logout results, clear private state and keep offline mutations disabled.

## Dependencies

- [FD-T04](../tasks/FD-T04.md)

## Acceptance criteria

- [x] A late old-token 401 cannot clear a new session.
- [x] Logout prevents a pending authentication response from restoring access.
- [x] Private query/snapshot state is cleared and offline data stays read-only.

## Tests and verification

- Controlled auth promise unit tests.
- Browser logout/offline reload and session replacement tests.

## Status

**verified-local**.

## Implementation evidence

Current 11-test frontend suite includes delayed 401/login/logout races. Preview and connected browser checks passed private-cache cleanup, session changes and offline read-only reload behavior.

Implementation and verification locations:

- [web/src/lib/api/auth.ts](../../web/src/lib/api/auth.ts)
- [web/src/hooks/use-auth.ts](../../web/src/hooks/use-auth.ts)
- [web/src/hooks/use-workbench.ts](../../web/src/hooks/use-workbench.ts)
- [tests/web/src/lib/api/auth.test.ts](../../tests/web/src/lib/api/auth.test.ts)
